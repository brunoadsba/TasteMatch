-- ============================================
-- Configurações de Memória Postgres (256MB)
-- ============================================
-- ATENÇÃO: Banco tem 256MB, não 1GB!
-- Configurações ajustadas para 256MB

-- shared_buffers: 25% de 256MB (máximo recomendado)
ALTER SYSTEM SET shared_buffers = '64MB';

-- work_mem: Limite por operação (muito conservador para 256MB)
-- Cálculo: 1MB * 10 conexões = 10MB (pior caso)
ALTER SYSTEM SET work_mem = '1MB';

-- maintenance_work_mem: Limite para operações de manutenção
ALTER SYSTEM SET maintenance_work_mem = '16MB';

-- effective_cache_size: Estimativa de cache do OS (75% de 256MB)
ALTER SYSTEM SET effective_cache_size = '192MB';

-- max_connections: Reduzido drasticamente para economizar memória
ALTER SYSTEM SET max_connections = '10';

-- temp_buffers: Buffers temporários (reduzido)
ALTER SYSTEM SET temp_buffers = '2MB';

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
    setting::int / 1024 / 1024 as mb
FROM pg_settings WHERE name = 'maintenance_work_mem';

-- Cálculo total estimado
SELECT 
    'Total estimado' as config,
    (
        (SELECT setting::int FROM pg_settings WHERE name = 'shared_buffers') +
        (SELECT setting::int FROM pg_settings WHERE name = 'work_mem') * 
        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') +
        (SELECT setting::int FROM pg_settings WHERE name = 'maintenance_work_mem')
    ) / 1024 / 1024 as mb;

