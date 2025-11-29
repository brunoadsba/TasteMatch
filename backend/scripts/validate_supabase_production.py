#!/usr/bin/env python3
"""
Script para validar configuração do Supabase em produção.

Pode ser executado via SSH no Fly.io ou localmente apontando para produção.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório do backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.database.base import SessionLocal, engine, IS_SUPABASE
from app.core.rag_service import validate_database_requirements, RAGService
from sqlalchemy import text, inspect

def print_header(title):
    """Imprime um cabeçalho formatado."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_success(message):
    """Imprime mensagem de sucesso."""
    print(f"✅ {message}")

def print_error(message):
    """Imprime mensagem de erro."""
    print(f"❌ {message}")

def print_warning(message):
    """Imprime mensagem de aviso."""
    print(f"⚠️  {message}")

def print_info(message):
    """Imprime mensagem informativa."""
    print(f"ℹ️  {message}")

def validate_supabase_production():
    """
    Valida configuração do Supabase em produção.
    Retorna True se todas as validações passarem.
    """
    print_header("Validação do Supabase em Produção")
    
    all_checks_passed = True
    
    # 1. Verificar DATABASE_URL
    print("\n1. Verificando DATABASE_URL...")
    database_url = settings.DATABASE_URL
    if not database_url:
        print_error("DATABASE_URL não configurada")
        return False
    
    # Mascarar senha para exibição
    if "@" in database_url:
        parts = database_url.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split(":")
            display_url = f"{user_pass[0]}:****@{parts[1]}"
        else:
            display_url = f"****@{parts[1]}"
    else:
        display_url = database_url[:50] + "..."
    
    print_info(f"DATABASE_URL: {display_url}")
    
    # Verificar se é Supabase
    is_supabase_url = "supabase" in database_url.lower() or "pooler.supabase.com" in database_url.lower()
    if is_supabase_url:
        print_success("URL do Supabase detectada")
    else:
        print_warning("URL não parece ser do Supabase")
    
    # 2. Verificar DB_PROVIDER
    print("\n2. Verificando DB_PROVIDER...")
    db_provider = os.getenv("DB_PROVIDER", "")
    if db_provider.lower() == "supabase":
        print_success(f"DB_PROVIDER configurado: {db_provider}")
        print_info("Configurações otimizadas do Supabase serão aplicadas")
    else:
        print_warning(f"DB_PROVIDER não configurado ou diferente de 'supabase': '{db_provider}'")
        print_info("A detecção automática funcionará, mas otimizações podem não ser aplicadas")
    
    # Verificar variável IS_SUPABASE do código
    print("\n3. Verificando detecção automática (IS_SUPABASE)...")
    if IS_SUPABASE:
        print_success("IS_SUPABASE = True (configurações otimizadas ativas)")
        print_info("Pool size: 20, Max overflow: 0")
    else:
        print_info(f"IS_SUPABASE = False (detecção automática: {is_supabase_url})")
        if is_supabase_url:
            print_info("Supabase será detectado automaticamente pela URL")
    
    # 3. Testar conexão ao banco
    print("\n4. Testando conexão ao banco de dados...")
    try:
        with engine.connect() as conn:
            # Verificar versão do PostgreSQL
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print_success(f"Conectado ao PostgreSQL: {version.split(',')[0]}")
            
            # Contar tabelas
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print_success(f"Tabelas encontradas: {len(tables)}")
            
    except Exception as e:
        print_error(f"Falha ao conectar ao banco: {str(e)}")
        all_checks_passed = False
    
    # 4. Validar requisitos do RAG Service (inclui pgvector)
    print("\n5. Validando requisitos do RAG Service (PostgreSQL + pgvector)...")
    try:
        db = SessionLocal()
        try:
            validation = validate_database_requirements(database_url, db)
            
            if validation["valid"]:
                print_success("Todos os requisitos do RAG Service estão atendidos!")
                
                if validation.get("is_supabase"):
                    print_success("Supabase detectado e validado")
            else:
                print_error("Falha na validação dos requisitos:")
                for error in validation["errors"]:
                    print_error(f"  - {error}")
                all_checks_passed = False
            
            if validation.get("warnings"):
                print_warning("Avisos encontrados:")
                for warning in validation["warnings"]:
                    print_warning(f"  - {warning}")
        finally:
            db.close()
            
    except Exception as e:
        print_error(f"Erro ao validar requisitos do RAG Service: {str(e)}")
        import traceback
        traceback.print_exc()
        all_checks_passed = False
    
    # 5. Testar inicialização do RAG Service (sem adicionar documentos)
    print("\n6. Testando inicialização do RAG Service...")
    try:
        db = SessionLocal()
        try:
            rag_service = RAGService(db, database_url, validate=True)
            print_success("RAG Service inicializado com sucesso")
            
            # Tentar inicializar vector store
            try:
                rag_service.initialize_vector_store()
                print_success("PGVector inicializado com sucesso")
            except Exception as e:
                print_error(f"Erro ao inicializar PGVector: {str(e)}")
                all_checks_passed = False
        finally:
            db.close()
            
    except ValueError as e:
        print_error(f"Erro de validação ao inicializar RAG Service: {str(e)}")
        all_checks_passed = False
    except Exception as e:
        print_error(f"Erro ao inicializar RAG Service: {str(e)}")
        import traceback
        traceback.print_exc()
        all_checks_passed = False
    
    # Resumo final
    print_header("Resumo da Validação")
    
    if all_checks_passed:
        print_success("TODAS AS VALIDAÇÕES PASSARAM!")
        print_info("Supabase está configurado corretamente e pronto para uso")
        return True
    else:
        print_error("ALGUMAS VALIDAÇÕES FALHARAM")
        print_info("Verifique os erros acima e corrija antes de usar o RAG Service")
        return False

if __name__ == "__main__":
    try:
        success = validate_supabase_production()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

