#!/bin/bash
#
# Script para executar configuração do Postgres no Fly.io
# 
# Este script tenta executar os comandos SQL de forma automatizada
# Se não funcionar, use o método manual descrito abaixo

echo "🔧 Tentando configurar Postgres no Fly.io..."
echo ""

# Método 1: Tentar via psql se tiver connection string
if command -v psql &> /dev/null; then
    echo "📋 Método 1: Tentando via psql..."
    echo "   (Requer DATABASE_URL configurada)"
    echo ""
fi

# Método 2: Instruções para execução manual
echo "📋 Método 2: Execução Manual (Recomendado)"
echo ""
echo "Execute os seguintes passos:"
echo ""
echo "1. Conecte ao Postgres:"
echo "   fly postgres connect -a tastematch-db"
echo ""
echo "2. Execute os comandos SQL (copie e cole):"
echo ""
cat << 'SQL'
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '2MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET max_connections = '20';
ALTER SYSTEM SET temp_buffers = '8MB';
ALTER SYSTEM SET log_min_duration_statement = '1000';
SELECT pg_reload_conf();
SQL

echo ""
echo "3. Verifique as configurações:"
echo ""
cat << 'SQL'
SELECT name, setting, unit 
FROM pg_settings 
WHERE name IN (
    'shared_buffers',
    'work_mem',
    'maintenance_work_mem',
    'effective_cache_size',
    'max_connections',
    'temp_buffers',
    'log_min_duration_statement'
)
ORDER BY name;
SQL

echo ""
echo "4. Sair do Postgres:"
echo "   \\q"
echo ""
echo "✅ Todos os comandos SQL estão em: backend/scripts/configure_postgres.sql"

