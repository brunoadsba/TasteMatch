"""
Módulo de Inicialização Automática de Bancos de Dados

Inicializa e valida todos os bancos de dados no startup do backend:
- PostgreSQL local (via Docker Compose)
- Supabase (validação de conexão)
- RAG/PGVector (validação de extensão e inicialização lazy)
"""

import os
import subprocess
import time
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from app.config import settings
from app.database.base import engine, SessionLocal
from app.core.rag_service import RAGService, validate_database_requirements
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def is_docker_running() -> bool:
    """
    Verifica se o Docker está rodando.
    
    Returns:
        True se Docker está rodando, False caso contrário
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def is_postgres_container_running() -> bool:
    """
    Verifica se o container PostgreSQL está rodando.
    
    Returns:
        True se container está rodando, False caso contrário
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=tastematch-postgres", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "tastematch-postgres" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def start_postgres_docker() -> Dict[str, any]:
    """
    Inicia PostgreSQL local via Docker Compose.
    
    Returns:
        Dict com status da operação
    """
    # Verificar se deve iniciar Docker automaticamente
    auto_start_docker = os.getenv("AUTO_START_DOCKER", "true").lower() == "true"
    
    if not auto_start_docker:
        logger.info("AUTO_START_DOCKER=false, pulando início automático do Docker")
        return {"success": False, "skipped": True, "message": "AUTO_START_DOCKER desabilitado"}
    
    # Verificar se Docker está rodando
    if not is_docker_running():
        logger.warning("Docker não está rodando. PostgreSQL local não será iniciado automaticamente.")
        return {"success": False, "error": "Docker não está rodando"}
    
    # Verificar se container já está rodando
    if is_postgres_container_running():
        logger.info("Container PostgreSQL já está rodando")
        return {"success": True, "message": "Container já estava rodando"}
    
    # Verificar se docker-compose.yml existe
    docker_compose_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),  # backend/
        "..",  # raiz do projeto
        "docker-compose.yml"
    )
    
    if not os.path.exists(docker_compose_path):
        logger.warning(f"docker-compose.yml não encontrado em: {docker_compose_path}")
        return {"success": False, "error": "docker-compose.yml não encontrado"}
    
    try:
        logger.info("Iniciando PostgreSQL via Docker Compose...")
        
        # Executar docker-compose up -d postgres
        result = subprocess.run(
            ["docker-compose", "-f", docker_compose_path, "up", "-d", "postgres"],
            cwd=os.path.dirname(docker_compose_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"Erro ao iniciar PostgreSQL: {result.stderr}")
            return {"success": False, "error": result.stderr}
        
        # Aguardar PostgreSQL ficar pronto (health check)
        logger.info("Aguardando PostgreSQL ficar pronto...")
        max_attempts = 30
        for attempt in range(max_attempts):
            if is_postgres_container_running():
                # Tentar conectar para verificar se está realmente pronto
                try:
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    logger.info("PostgreSQL está pronto e aceitando conexões")
                    return {"success": True, "message": "PostgreSQL iniciado com sucesso"}
                except Exception:
                    # Ainda não está pronto, aguardar mais
                    time.sleep(1)
            else:
                time.sleep(1)
        
        logger.warning("PostgreSQL iniciado mas não respondeu ao health check a tempo")
        return {"success": False, "error": "Timeout aguardando PostgreSQL ficar pronto"}
        
    except subprocess.TimeoutExpired:
        logger.error("Timeout ao iniciar PostgreSQL")
        return {"success": False, "error": "Timeout ao iniciar PostgreSQL"}
    except FileNotFoundError:
        logger.error("docker-compose não encontrado no PATH")
        return {"success": False, "error": "docker-compose não encontrado no PATH"}
    except Exception as e:
        logger.error(f"Erro inesperado ao iniciar PostgreSQL: {str(e)}")
        return {"success": False, "error": str(e)}


def validate_postgres_connection() -> Dict[str, any]:
    """
    Valida conexão com PostgreSQL (local ou Supabase).
    
    Returns:
        Dict com status da conexão
    """
    try:
        # Verificar se é PostgreSQL (não SQLite)
        if "sqlite" in settings.DATABASE_URL.lower():
            return {
                "success": False,
                "error": "SQLite detectado. PostgreSQL é necessário para RAG/PGVector."
            }
        
        # Tentar conectar
        with engine.connect() as conn:
            # Verificar versão do PostgreSQL
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            # Detectar se é Supabase ou local
            is_supabase = "supabase" in settings.DATABASE_URL.lower() or os.getenv("DB_PROVIDER", "").lower() == "supabase"
            db_type = "Supabase" if is_supabase else "PostgreSQL Local"
            
            logger.info(f"Conectado ao {db_type}: {version[:50]}...")
            
            return {
                "success": True,
                "db_type": db_type,
                "version": version[:100]  # Primeiros 100 caracteres
            }
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro ao validar conexão PostgreSQL: {error_msg}")
        
        # Mensagens de erro mais específicas
        if "connection refused" in error_msg.lower() or "could not connect" in error_msg.lower():
            return {
                "success": False,
                "error": "Conexão recusada. Verifique se PostgreSQL está rodando e se DATABASE_URL está correto."
            }
        elif "authentication failed" in error_msg.lower() or "password" in error_msg.lower():
            return {
                "success": False,
                "error": "Erro de autenticação. Verifique credenciais em DATABASE_URL."
            }
        else:
            return {
                "success": False,
                "error": f"Erro de conexão: {error_msg}"
            }


def validate_pgvector_extension(db: Session) -> Dict[str, any]:
    """
    Valida se a extensão pgvector está instalada.
    Tenta criar automaticamente se não existir.
    
    Args:
        db: Sessão do banco de dados
    
    Returns:
        Dict com status da extensão
    """
    try:
        # Verificar se extensão existe
        result = db.execute(
            text("SELECT * FROM pg_extension WHERE extname = 'vector'")
        )
        extension = result.fetchone()
        
        if extension:
            logger.info("Extensão pgvector já está instalada")
            return {"success": True, "message": "Extensão pgvector instalada"}
        
        # Tentar criar extensão
        logger.info("Extensão pgvector não encontrada. Tentando criar...")
        try:
            db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            db.commit()
            logger.info("Extensão pgvector criada com sucesso")
            return {"success": True, "message": "Extensão pgvector criada"}
        except Exception as e:
            db.rollback()
            error_msg = str(e)
            logger.error(f"Erro ao criar extensão pgvector: {error_msg}")
            
            if "permission denied" in error_msg.lower():
                return {
                    "success": False,
                    "error": "Permissão negada para criar extensão pgvector. Execute manualmente: CREATE EXTENSION vector;"
                }
            else:
                return {
                    "success": False,
                    "error": f"Erro ao criar extensão pgvector: {error_msg}"
                }
                
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro ao validar extensão pgvector: {error_msg}")
        return {"success": False, "error": error_msg}


def validate_rag_service(db: Session, connection_string: str, eager: bool = True) -> Dict[str, any]:
    """
    Valida e inicializa RAG Service.
    
    Args:
        db: Sessão do banco de dados
        connection_string: String de conexão PostgreSQL
        eager: Se True, inicializa vector_store completamente (eager).
               Se False, apenas valida requisitos (lazy).
    
    Returns:
        Dict com status da validação
    """
    try:
        # Validar requisitos do banco (sem inicializar vector_store)
        validation = validate_database_requirements(connection_string, db)
        
        if not validation["valid"]:
            error_msg = "Requisitos do banco de dados não atendidos:\n"
            error_msg += "\n".join(f"  - {err}" for err in validation["errors"])
            
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "warnings": validation.get("warnings", [])
            }
        
        # Criar instância RAGService
        # Se eager=True, inicializa vector_store completamente (sempre ativo)
        # Se eager=False, apenas valida (lazy - inicializa quando necessário)
        rag_service = RAGService(
            db=db,
            connection_string=connection_string,
            validate=True,
            initialize_vector_store=eager
        )
        
        # Se eager, verificar se há documentos para confirmar que está funcionando
        if eager:
            try:
                has_docs = rag_service.has_documents()
                logger.info(f"RAG Service inicializado (eager mode) - Documentos: {'Sim' if has_docs else 'Não'}")
            except Exception as e:
                logger.warning(f"Erro ao verificar documentos no RAG: {str(e)}")
        
        warnings = validation.get("warnings", [])
        if warnings:
            for warning in warnings:
                logger.warning(warning)
        
        mode = "eager" if eager else "lazy"
        logger.info(f"RAG Service validado com sucesso ({mode} initialization)")
        
        return {
            "success": True,
            "message": f"RAG Service validado ({mode} mode)",
            "warnings": warnings,
            "eager": eager
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erro ao validar RAG Service: {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }


async def initialize_databases() -> Dict[str, any]:
    """
    Função principal que inicializa todos os bancos de dados no startup.
    
    Returns:
        Dict com status de todas as inicializações
    """
    logger.info("=" * 60)
    logger.info("🚀 Inicializando bancos de dados...")
    logger.info("=" * 60)
    
    results = {
        "postgres_docker": None,
        "postgres_connection": None,
        "pgvector_extension": None,
        "rag_service": None,
        "overall_success": False
    }
    
    # 1. Iniciar PostgreSQL local (se necessário)
    logger.info("")
    logger.info("1️⃣  Verificando PostgreSQL local (Docker)...")
    postgres_docker_result = start_postgres_docker()
    results["postgres_docker"] = postgres_docker_result
    
    if postgres_docker_result.get("success"):
        logger.info("   ✅ PostgreSQL local iniciado/verificado")
    elif postgres_docker_result.get("skipped"):
        logger.info("   ⏭️  Início automático do Docker desabilitado")
    else:
        logger.warning(f"   ⚠️  PostgreSQL local: {postgres_docker_result.get('error', 'Erro desconhecido')}")
        logger.info("   ℹ️  Continuando (pode ser Supabase na nuvem)")
    
    # 2. Validar conexão PostgreSQL
    logger.info("")
    logger.info("2️⃣  Validando conexão PostgreSQL...")
    postgres_connection_result = validate_postgres_connection()
    results["postgres_connection"] = postgres_connection_result
    
    if postgres_connection_result.get("success"):
        db_type = postgres_connection_result.get("db_type", "PostgreSQL")
        logger.info(f"   ✅ Conectado ao {db_type}")
    else:
        logger.error(f"   ❌ Erro de conexão: {postgres_connection_result.get('error', 'Erro desconhecido')}")
        logger.error("   ⚠️  Aplicação pode não funcionar corretamente sem conexão ao banco!")
        results["overall_success"] = False
        logger.info("")
        logger.info("=" * 60)
        logger.error("❌ Inicialização de bancos de dados FALHOU")
        logger.info("=" * 60)
        return results
    
    # 3. Validar extensão pgvector
    logger.info("")
    logger.info("3️⃣  Validando extensão pgvector...")
    db = SessionLocal()
    try:
        pgvector_result = validate_pgvector_extension(db)
        results["pgvector_extension"] = pgvector_result
        
        if pgvector_result.get("success"):
            logger.info("   ✅ Extensão pgvector validada")
        else:
            logger.error(f"   ❌ Erro na extensão pgvector: {pgvector_result.get('error', 'Erro desconhecido')}")
            logger.error("   ⚠️  RAG não funcionará sem pgvector!")
    finally:
        db.close()
    
    # 4. Validar e inicializar RAG Service (eager - sempre ativo)
    logger.info("")
    logger.info("4️⃣  Validando e inicializando RAG Service (eager - sempre ativo)...")
    db = SessionLocal()
    try:
        connection_string = settings.DATABASE_URL
        if connection_string.startswith("postgres://"):
            connection_string = connection_string.replace("postgres://", "postgresql://", 1)
        
        # Inicializar RAG em modo eager (sempre ativo)
        # Isso inicializa o vector_store completamente, detectando erros cedo
        # Cada requisição ainda cria nova instância (com sua própria sessão db),
        # mas o vector_store será inicializado imediatamente (não lazy)
        rag_result = validate_rag_service(db, connection_string, eager=True)
        results["rag_service"] = rag_result
        
        if rag_result.get("success"):
            logger.info("   ✅ RAG Service validado")
            if rag_result.get("warnings"):
                for warning in rag_result["warnings"]:
                    logger.warning(f"   ⚠️  {warning}")
        else:
            logger.error(f"   ❌ Erro no RAG Service: {rag_result.get('error', 'Erro desconhecido')}")
    finally:
        db.close()
    
    # Resultado final
    results["overall_success"] = (
        results["postgres_connection"].get("success", False) and
        results["pgvector_extension"].get("success", False) and
        results["rag_service"].get("success", False)
    )
    
    logger.info("")
    logger.info("=" * 60)
    if results["overall_success"]:
        logger.info("✅ Inicialização de bancos de dados CONCLUÍDA com sucesso")
    else:
        logger.warning("⚠️  Inicialização de bancos de dados concluída com AVISOS")
    logger.info("=" * 60)
    logger.info("")
    
    return results

