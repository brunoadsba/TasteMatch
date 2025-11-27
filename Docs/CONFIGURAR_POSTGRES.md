# Configuração do Postgres no Fly.io

## Objetivo
Configurar o Postgres (`tastematch-db`) para trabalhar dentro do limite de **1GB de memória**, aplicando configurações otimizadas que previnem OOM (Out of Memory).

## Configurações Necessárias

### Memória Total: 1GB

| Configuração | Valor | Justificativa |
|-------------|-------|---------------|
| `shared_buffers` | 256MB | 25% de 1GB (padrão recomendado) |
| `work_mem` | 2MB | Conservador: 2MB * 20 conexões = 40MB (pior caso) |
| `maintenance_work_mem` | 64MB | Limite para operações de manutenção |
| `effective_cache_size` | 768MB | Estimativa de cache do OS |
| `max_connections` | 20 | Reduzido de padrão (100) para economizar memória |
| `temp_buffers` | 8MB | Buffers temporários |
| `log_min_duration_statement` | 1000ms | Log queries lentas (>1s) para observabilidade |

### Cálculo de Memória

- **shared_buffers**: 256MB
- **work_mem * max_connections**: 2MB * 20 = 40MB (pior caso)
- **maintenance_work_mem**: 64MB
- **Total estimado**: ~360MB (36% de 1GB)
- **Margem para sistema**: ~640MB

## Método 1: Via Fly CLI (Recomendado)

### Passo 1: Conectar ao Postgres

```bash
fly postgres connect -a tastematch-db
```

### Passo 2: Executar Comandos SQL

Cole e execute os seguintes comandos SQL:

```sql
-- Configurações de memória otimizadas para 1GB
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '2MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET max_connections = '20';
ALTER SYSTEM SET temp_buffers = '8MB';
ALTER SYSTEM SET log_min_duration_statement = '1000';

-- Aplicar configurações
SELECT pg_reload_conf();
```

### Passo 3: Verificar Configurações

```sql
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
```

### Passo 4: Verificar Uso de Memória Estimado

```sql
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
```

**Resultado esperado:**
```
config                        | mb
------------------------------|----
shared_buffers                | 256
work_mem * max_connections    | 40
maintenance_work_mem          | 64
```

## Método 2: Via Script (Alternativo)

Se preferir, você pode usar o script gerado:

```bash
# Ver o conteúdo do script
cat backend/scripts/configure_postgres.sh

# Conectar e executar (se o Fly.io suportar)
fly postgres connect -a tastematch-db < backend/scripts/configure_postgres.sh
```

## Validação Pós-Configuração

### 1. Verificar Conexões Ativas

```sql
SELECT count(*) as active_connections
FROM pg_stat_activity 
WHERE datname = 'tastematch-db';
```

**Esperado**: 4-12 conexões (não >20)

### 2. Verificar Uso de Memória

```bash
# Via Fly CLI
fly status -a tastematch-db
```

**Esperado**: Uso de memória estável, sem picos acima de 800MB

### 3. Monitorar Logs

```bash
# Verificar logs do Postgres
fly logs -a tastematch-db

# Procurar por:
# - Queries lentas (>1s) - devem aparecer nos logs
# - Erros de memória - não devem aparecer
```

## Troubleshooting

### Problema: Configurações não aplicadas

**Solução**: Verificar se `pg_reload_conf()` foi executado:

```sql
SELECT pg_reload_conf();
```

### Problema: Postgres não aceita ALTER SYSTEM

**Solução**: Alguns ambientes gerenciados podem não permitir `ALTER SYSTEM`. Nesse caso:
- Verificar se há interface web no Fly.io para configurações
- Contatar suporte do Fly.io
- Usar variáveis de ambiente se disponíveis

### Problema: Configurações revertidas após restart

**Solução**: Verificar se as configurações foram salvas em `postgresql.conf`:

```sql
SHOW config_file;
```

## Notas Importantes

1. **Reinicialização**: Algumas configurações (como `shared_buffers`) podem requerer restart do Postgres. O Fly.io pode fazer isso automaticamente.

2. **Monitoramento**: Após aplicar as configurações, monitore o uso de memória por alguns dias para garantir que está estável.

3. **Ajustes Finaos**: Se ainda houver problemas de memória, considere reduzir ainda mais:
   - `work_mem` para `1MB` (mais conservador)
   - `max_connections` para `15` (se possível)

## Referências

- [PostgreSQL Memory Configuration](https://www.postgresql.org/docs/current/runtime-config-resource.html)
- [Fly.io Postgres Documentation](https://fly.io/docs/postgres/)

