# Como Executar Configuração do Postgres

## ⚠️ Importante

O `fly postgres connect` abre uma sessão interativa. Você precisa executar os comandos SQL manualmente após conectar.

## Passo a Passo

### 1. Conectar ao Postgres

```bash
fly postgres connect -a tastematch-db
```

Você verá algo como:
```
Connecting to tastematch-db... 
psql (XX.X)
Type "help" for help.

tastematch-db=>
```

### 2. Executar Comandos SQL

Cole e execute os seguintes comandos SQL (um por vez ou todos juntos):

```sql
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '2MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET max_connections = '20';
ALTER SYSTEM SET temp_buffers = '8MB';
ALTER SYSTEM SET log_min_duration_statement = '1000';
SELECT pg_reload_conf();
```

### 3. Verificar Configurações

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

### 4. Verificar Uso de Memória

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
    setting::int / 1024 / 1024 as mb;
```

### 5. Sair do Postgres

```sql
\q
```

## Arquivo SQL Completo

Todos os comandos estão em: `backend/scripts/configure_postgres.sql`

Você pode copiar o conteúdo desse arquivo e colar no terminal do Postgres.

## Resultado Esperado

Após executar, você deve ver:
- `ALTER SYSTEM` retornando `ALTER SYSTEM` para cada comando
- `pg_reload_conf` retornando `t` (true)
- A query de verificação mostrando os valores configurados

## Troubleshooting

### Se `ALTER SYSTEM` não funcionar

Alguns ambientes gerenciados podem não permitir `ALTER SYSTEM`. Nesse caso:
1. Verifique se há interface web no Fly.io para configurações
2. Verifique se há variáveis de ambiente disponíveis
3. Contate suporte do Fly.io se necessário

### Se precisar reiniciar

Algumas configurações (como `shared_buffers`) podem requerer restart:
```bash
fly apps restart -a tastematch-db
```

