#!/bin/bash
#
# Script para configurar Postgres no Fly.io para ambiente com 1GB de memória
# 
# Uso:
#   fly postgres connect -a tastematch-db
#   Depois execute os comandos SQL abaixo manualmente
#
# OU execute este script após conectar:
#   fly postgres connect -a tastematch-db < scripts/configure_postgres.sh

echo "🔧 Configurando Postgres para 1GB de memória..."
echo ""

# Configurações de memória otimizadas para 1GB
cat << 'EOF'
-- ============================================
-- Configurações de Memória Postgres (1GB)
-- ============================================

-- shared_buffers: 25% de 1GB (padrão recomendado)
ALTER SYSTEM SET shared_buffers = '256MB';

-- work_mem: Limite por operação (conservador para 1GB)
-- Cálculo: 2MB * 20 conexões = 40MB (pior caso)
ALTER SYSTEM SET work_mem = '2MB';

-- maintenance_work_mem: Limite para operações de manutenção
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- effective_cache_size: Estimativa de cache do OS
ALTER SYSTEM SET effective_cache_size = '768MB';

-- max_connections: Reduzido de padrão para economizar memória
ALTER SYSTEM SET max_connections = '20';

-- temp_buffers: Buffers temporários
ALTER SYSTEM SET temp_buffers = '8MB';

-- log_min_duration_statement: Log queries > 1s (observabilidade)
ALTER SYSTEM SET log_min_duration_statement = '1000';

-- Aplicar configurações
SELECT pg_reload_conf();

-- Verificar configurações aplicadas
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

-- Verificar uso de memória estimado
SELECT 
    'shared_buffers' as config,
    setting::int / 1024 / 1024 as mb
FROM pg_settings WHERE name = 'shared_buffers'
UNION ALL
SELECT 
    'work_mem * max_connections' as config,
    (SELECT setting::int FROM pg_settings WHERE name = 'work_mem') * 
    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') / 1024 / 1024 as mb
UNION ALL
SELECT 
    'maintenance_work_mem' as config,
    setting::int / 1024 / 1024 as mb;

EOF

echo ""
echo "✅ Script gerado. Execute os comandos SQL acima no Postgres."
echo ""
echo "📝 Como usar:"
echo "   1. fly postgres connect -a tastematch-db"
echo "   2. Cole e execute os comandos SQL acima"
echo "   3. Verifique as configurações com a última query"

