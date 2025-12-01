#!/usr/bin/env python3
"""
Script para validar configuração do banco de dados para RAG Service.

Pode ser executado localmente ou em produção para verificar:
- Conexão ao banco
- Extensão pgvector instalada
- Configurações do Supabase (se aplicável)

Uso:
    python scripts/validate_database.py
"""

import os
import sys
from pathlib import Path

# Adicionar diretório do backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.core.rag_service import validate_database_requirements
from app.database.base import get_db

def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text: str):
    """Imprime mensagem de sucesso"""
    print(f"✅ {text}")

def print_error(text: str):
    """Imprime mensagem de erro"""
    print(f"❌ {text}")

def print_warning(text: str):
    """Imprime mensagem de aviso"""
    print(f"⚠️  {text}")

def validate_database():
    """Valida configuração do banco de dados"""
    
    print_header("Validação do Banco de Dados - RAG Service")
    
    # 1. Verificar DATABASE_URL
    print("\n1. Verificando DATABASE_URL...")
    if not settings.DATABASE_URL:
        print_error("DATABASE_URL não está configurada!")
        return False
    
    # Ocultar senha na exibição
    db_url_display = settings.DATABASE_URL
    if "@" in db_url_display:
        parts = db_url_display.split("@")
        if ":" in parts[0]:
            user_pass = parts[0].split(":")
            db_url_display = f"{user_pass[0]}:****@{parts[-1]}"
    else:
        db_url_display = db_url_display[:50] + "..." if len(db_url_display) > 50 else db_url_display
    
    print(f"   DATABASE_URL: {db_url_display}")
    
    # Detectar ambiente
    is_supabase = "supabase" in settings.DATABASE_URL.lower() or "pooler.supabase.com" in settings.DATABASE_URL.lower()
    is_local = "localhost" in settings.DATABASE_URL or "127.0.0.1" in settings.DATABASE_URL
    
    if is_supabase:
        print("   Ambiente: Produção (Supabase)")
    elif is_local:
        print("   Ambiente: Local (PostgreSQL local)")
    else:
        print("   Ambiente: Produção/Remoto")
    
    # 2. Testar conexão
    print("\n2. Testando conexão ao banco...")
    try:
        from app.database.base import engine, SessionLocal
        
        # Criar sessão temporária
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print_success(f"Conectado ao banco: {version[:80]}...")
        finally:
            db.close()
            
    except Exception as e:
        print_error(f"Falha ao conectar ao banco: {str(e)}")
        return False
    
    # 3. Validar requisitos do RAG Service
    print("\n3. Validando requisitos do RAG Service...")
    try:
        db = SessionLocal()
        try:
            validation = validate_database_requirements(settings.DATABASE_URL, db)
            
            if validation["valid"]:
                print_success("Todos os requisitos estão atendidos!")
            else:
                print_error("Requisitos não atendidos:")
                for error in validation["errors"]:
                    print(f"   - {error}")
            
            if validation.get("warnings"):
                print("\n⚠️  Avisos:")
                for warning in validation["warnings"]:
                    print(f"   - {warning}")
            
            if not validation["valid"]:
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print_error(f"Erro ao validar requisitos: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Verificar DB_PROVIDER (se Supabase)
    if is_supabase:
        print("\n4. Verificando configuração do Supabase...")
        db_provider = os.getenv("DB_PROVIDER", "").lower()
        if db_provider == "supabase":
            print_success("DB_PROVIDER=supabase configurado")
        else:
            print_warning(
                "DB_PROVIDER não está configurado como 'supabase'. "
                "Isso pode afetar configurações de SSL e pooling. "
                "Configure: export DB_PROVIDER=supabase"
            )
    
    # 5. Testar inicialização do RAG Service
    print("\n5. Testando inicialização do RAG Service...")
    try:
        from app.core.rag_service import get_rag_service, RAGService
        
        db = SessionLocal()
        try:
            # get_rag_service não aceita validate, então criar diretamente
            rag_service = RAGService(db, settings.DATABASE_URL, validate=True)
            print_success("RAG Service inicializado com sucesso!")
            
            # Tentar inicializar vector store (sem adicionar documentos)
            try:
                rag_service.initialize_vector_store()
                print_success("PGVector inicializado com sucesso!")
            except Exception as e:
                print_error(f"Erro ao inicializar PGVector: {str(e)}")
                return False
                
        finally:
            db.close()
            
    except Exception as e:
        print_error(f"Erro ao inicializar RAG Service: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Resumo final
    print_header("Resumo da Validação")
    print_success("✅ Todas as validações passaram!")
    print("\nO banco de dados está configurado corretamente para usar o RAG Service.")
    
    if is_supabase:
        print("\n📝 Lembrete para produção:")
        print("   - Verifique se a extensão 'vector' está habilitada no Supabase")
        print("   - Verifique se DB_PROVIDER=supabase está configurado no Fly.io")
        print("   - Verifique se DATABASE_URL está correta (com SSL)")
    
    return True

if __name__ == "__main__":
    try:
        success = validate_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Validação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

