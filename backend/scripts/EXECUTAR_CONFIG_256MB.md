# Guia: Configurar Postgres para 256MB

## ⚠️ IMPORTANTE

O banco tem **256MB de memória**, não 1GB! As configurações precisam ser ajustadas.

## 📋 Passo a Passo

### 1. Reiniciar o Banco (se necessário)

```bash
fly machine restart 4d8946ddbe72d8 -a tastematch-db
```

Aguarde alguns segundos para o banco reiniciar.

### 2. Verificar Status

```bash
fly status -a tastematch-db
```

Confirme que o banco está `started` e não mais em `error`.

### 3. Conectar ao Postgres

```bash
fly postgres connect -a tastematch-db
```

Isso abrirá uma sessão interativa `psql`.

### 4. Aplicar Configurações

Dentro da sessão `psql`, copie e cole o conteúdo do arquivo:

```bash
cat backend/scripts/configure_postgres_256mb.sql
```

Ou execute diretamente:

```sql
-- shared_buffers: 25% de 256MB
ALTER SYSTEM SET shared_buffers = '64MB';

-- work_mem: Muito conservador para 256MB
ALTER SYSTEM SET work_mem = '1MB';

-- maintenance_work_mem
ALTER SYSTEM SET maintenance_work_mem = '16MB';

-- effective_cache_size: 75% de 256MB
ALTER SYSTEM SET effective_cache_size = '192MB';

-- max_connections: Reduzido drasticamente
ALTER SYSTEM SET max_connections = '10';

-- temp_buffers
ALTER SYSTEM SET temp_buffers = '2MB';

-- log_min_duration_statement
ALTER SYSTEM SET log_min_duration_statement = '1000';

-- Aplicar configurações
SELECT pg_reload_conf();
```

### 5. Verificar Configurações

```sql
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
```

### 6. Verificar Uso de Memória Estimado

```sql
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
```

### 7. Sair do psql

```sql
\q
```

### 8. Verificar se o Backend Conecta

```bash
curl https://tastematch-api.fly.dev/health
```

O campo `database` deve mostrar `connected` ao invés de `disconnected`.

## 📊 Configurações Esperadas

| Configuração | Valor | Justificativa |
|--------------|-------|---------------|
| shared_buffers | 64MB | 25% de 256MB |
| work_mem | 1MB | Conservador (10MB total com 10 conexões) |
| maintenance_work_mem | 16MB | Reduzido para 256MB |
| effective_cache_size | 192MB | 75% de 256MB |
| max_connections | 10 | Reduzido drasticamente |
| temp_buffers | 2MB | Reduzido |
| log_min_duration_statement | 1000ms | Observabilidade |

## ⚠️ Cálculo de Memória Total

- shared_buffers: 64MB
- work_mem * max_connections: 1MB * 10 = 10MB
- maintenance_work_mem: 16MB
- **Total estimado**: ~90MB (35% de 256MB)
- **Margem**: ~166MB para sistema e operações

## ✅ Critérios de Sucesso

1. Banco reiniciado e em estado `started`
2. Configurações aplicadas e verificadas
3. Backend conecta ao banco (`database: connected`)
4. Sem erros de OOM nos logs

