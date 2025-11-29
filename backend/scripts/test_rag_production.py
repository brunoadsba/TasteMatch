#!/usr/bin/env python3
"""Script simples para testar RAG Service em produção via SSH."""

from app.database.base import SessionLocal
from app.core.rag_service import RAGService, validate_database_requirements
from app.config import settings
from sqlalchemy import text

print('=' * 60)
print('TESTE DE VALIDAÇÃO DO RAG SERVICE EM PRODUÇÃO')
print('=' * 60)
print()

db = SessionLocal()
try:
    # 1. Verificar extensão pgvector
    print('1. Verificando extensão pgvector...')
    result = db.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"))
    ext = result.fetchone()
    if ext:
        print(f'   ✅ pgvector INSTALADA (versão: {ext[1]})')
    else:
        print('   ❌ pgvector NÃO INSTALADA')
        exit(1)
    
    # 2. Validar requisitos
    print()
    print('2. Validando requisitos do RAG Service...')
    validation = validate_database_requirements(settings.DATABASE_URL, db)
    
    if validation['valid']:
        print('   ✅ Todos os requisitos atendidos')
        if validation.get('is_supabase'):
            print('   ✅ Supabase detectado e validado')
    else:
        print('   ❌ Falha na validação:')
        for error in validation['errors']:
            print(f'      - {error}')
        exit(1)
    
    # 3. Testar inicialização do RAG Service
    print()
    print('3. Testando inicialização do RAG Service...')
    rag_service = RAGService(db, settings.DATABASE_URL, validate=True)
    print('   ✅ RAG Service criado com sucesso')
    
    # 4. Inicializar vector store
    print()
    print('4. Inicializando vector store...')
    rag_service.initialize_vector_store()
    print('   ✅ Vector store inicializado')
    
    print()
    print('=' * 60)
    print('✅ TODOS OS TESTES PASSARAM!')
    print('=' * 60)
    print()
    print('Supabase e pgvector estão configurados corretamente!')
    
except Exception as e:
    print(f'❌ Erro: {str(e)}')
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    db.close()

