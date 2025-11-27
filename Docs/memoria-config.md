# Plano de Otimização de Memória - TasteMatch

## Objetivo
Resolver o problema de OOM (Out of Memory) do banco de dados `tastematch-db` e otimizar a performance da aplicação, trabalhando dentro do limite fixo de **1GB de memória** sem aumentar custos.

## Situação Atual

### Configurações Identificadas
- **Banco de dados (tastematch-db)**: 1GB RAM (LIMITE FIXO - não pode ser aumentado)
- **Backend (tastematch-api)**: 1GB RAM, 1 CPU compartilhado, 2 máquinas (2 workers)
- **Postgres**: Sem configurações de memória explícitas
- **SQLAlchemy**: Sem pool de conexões configurado

### Problemas Críticos Identificados

#### 1. Queries que Carregam Dados Excessivos (CRÍTICO)
- **`recommendations.py:107`**: `get_restaurants(db, limit=10000)` - Carrega TODOS os restaurantes na memória
- **`recommendations.py:277`**: `get_restaurants(db, limit=10000)` - Repetido
- **`recommendations.py:362`**: `get_restaurants(db, limit=10000)` - Repetido
- **Impacto**: Carregar 10.000 restaurantes pode facilmente causar OOM em 1GB

#### 2. Pool de Conexões Não Configurado
- SQLAlchemy usa valores padrão (pool_size=5, max_overflow=10)
- Sem controle sobre número de conexões simultâneas
- Sem reciclagem de conexões

#### 3. Postgres Sem Limites de Memória
- `shared_buffers` não configurado (pode usar toda memória disponível)
- `work_mem` não limitado (operações podem usar memória excessiva)
- `max_connections` pode estar muito alto

#### 4. Sem Cache Implementado
- Todas as queries vão direto ao banco
- Dados estáticos são recalculados a cada requisição

## Fases de Implementação

### Fase 1: Otimizar Pool de Conexões (CRÍTICO)

#### 1.1 Configurar SQLAlchemy Engine com Pool Conservador
**Arquivo**: `backend/app/database/base.py`

```python
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=settings.DEBUG,
    # Pool conservador para 1GB de memória
    pool_size=3,              # Conexões base (reduzido de 5)
    max_overflow=5,           # Máximo 8 conexões totais (reduzido de 15)
    pool_recycle=1800,        # Reciclar após 30min (mais agressivo que 1h)
    pool_pre_ping=True,       # Verificar conexões antes de usar
    pool_timeout=30,          # Timeout para obter conexão
)
```

**Justificativa**:
- `pool_size=3`: Reduz conexões base para economizar memória
- `max_overflow=5`: Máximo 8 conexões (alinhado com `max_connections=20` do Postgres)
- `pool_recycle=1800`: Reciclagem mais frequente libera memória mais rápido

#### 1.2 Ajustar Workers do Backend
**Arquivo**: `backend/Dockerfile`

```dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

**Justificativa**:
- 1 worker por máquina = 2 workers totais (distribuídos)
- Reduz conexões simultâneas por worker
- Mantém redundância com 2 máquinas

### Fase 2: Configurar Postgres para 1GB (CRÍTICO)

#### 2.1 Configurações de Memória do Postgres
**Aplicar via variáveis de ambiente no Fly.io** ou arquivo de configuração:

```bash
# Configurações para Postgres com 1GB de RAM
shared_buffers=256MB          # 25% de 1GB (padrão recomendado)
work_mem=4MB                  # Limite por operação de ordenação/hash
maintenance_work_mem=64MB     # Limite para operações de manutenção
effective_cache_size=768MB    # Estimativa de cache do OS
max_connections=20            # Reduzido de padrão (100) para economizar memória
temp_buffers=8MB              # Buffers temporários
```

**Cálculo de Memória**:
- `shared_buffers`: 256MB (25% de 1GB)
- `work_mem * max_connections`: 4MB * 20 = 80MB (pior caso)
- `maintenance_work_mem`: 64MB
- **Total estimado**: ~400MB para Postgres, deixando ~600MB para sistema e operações

**Como aplicar no Fly.io**:
```bash
# Via fly secrets (se suportado) ou arquivo postgresql.conf
fly secrets set -a tastematch-db POSTGRES_SHARED_BUFFERS=256MB
fly secrets set -a tastematch-db POSTGRES_WORK_MEM=4MB
# ... etc
```

**Alternativa**: Criar arquivo `postgresql.conf` e aplicar via volume ou init script.

### Fase 3: Otimizar Queries Críticas (CRÍTICO)

#### 3.1 Remover Carregamento de 10.000 Restaurantes
**Arquivo**: `backend/app/api/routes/recommendations.py`

**Problema**: Linhas 107, 277, 362 carregam `get_restaurants(db, limit=10000)`

**Solução**: Carregar apenas o necessário ou usar cache

**Antes**:
```python
all_restaurants = get_restaurants(db, limit=10000)  # ❌ Carrega tudo na memória
```

**Depois**:
```python
# Opção 1: Carregar apenas IDs e metadados essenciais
all_restaurants = get_restaurants_metadata(db, limit=None)  # Apenas ID, nome, cuisine_type

# Opção 2: Usar cache (melhor)
from app.core.cache import get_cached_restaurants_metadata
all_restaurants = get_cached_restaurants_metadata(db, ttl_minutes=60)
```

**Criar função otimizada em `backend/app/database/crud.py`**:
```python
def get_restaurants_metadata(db: Session, limit: Optional[int] = None):
    """Retorna apenas metadados essenciais dos restaurantes (sem descrição completa)."""
    query = db.query(
        Restaurant.id,
        Restaurant.name,
        Restaurant.cuisine_type,
        Restaurant.rating,
        Restaurant.price_range
    )
    if limit:
        query = query.limit(limit)
    return query.all()
```

#### 3.2 Otimizar Carregamento de Pedidos
**Arquivo**: `backend/app/api/routes/recommendations.py`

**Problema**: Linha 106 carrega até 100 pedidos completos

**Solução**: Carregar apenas dados necessários para padrões

**Antes**:
```python
user_orders = get_user_orders(db, user_id=current_user.id, limit=100)
```

**Depois**:
```python
# Carregar apenas campos necessários para extrair padrões
user_orders = get_user_orders_metadata(
    db, 
    user_id=current_user.id, 
    limit=50  # Reduzido de 100
)
```

#### 3.3 Adicionar Paginação Obrigatória
**Arquivo**: `backend/app/api/routes/recommendations.py`

Todos os endpoints de listagem devem ter paginação:
- `limit` máximo: 50 (reduzido de padrão)
- `offset` obrigatório para navegação

### Fase 4: Implementar Cache (IMPORTANTE)

#### 4.1 Cache In-Memory para Metadados de Restaurantes
**Arquivo**: `backend/app/core/cache.py` (criar)

```python
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time

# Cache simples em memória (pode migrar para Redis depois)
_restaurants_metadata_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 3600  # 1 hora

def get_cached_restaurants_metadata(db: Session, ttl_minutes: int = 60):
    """Retorna metadados de restaurantes com cache."""
    cache_key = "restaurants_metadata"
    now = time.time()
    
    # Verificar cache
    if cache_key in _restaurants_metadata_cache:
        data, timestamp = _restaurants_metadata_cache[cache_key]
        if now - timestamp < (ttl_minutes * 60):
            return data
    
    # Carregar do banco (apenas metadados)
    from app.database.crud import get_restaurants_metadata
    data = get_restaurants_metadata(db, limit=None)
    
    # Atualizar cache
    _restaurants_metadata_cache[cache_key] = (data, now)
    
    return data
```

#### 4.2 Cache de Recomendações
- Cache de recomendações por usuário (TTL: 10 minutos)
- Cache de insights gerados (TTL: 7 dias, já implementado)

#### 4.3 Headers HTTP Cache-Control
**Arquivo**: `backend/app/main.py`

Adicionar middleware para adicionar headers de cache:

```python
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Cache para endpoints GET de dados estáticos
    if request.method == "GET":
        if "/api/restaurants" in str(request.url.path):
            response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutos
        elif "/api/recommendations" in str(request.url.path):
            response.headers["Cache-Control"] = "private, max-age=600"  # 10 minutos
    
    return response
```

### Fase 5: Otimizar Queries N+1

#### 5.1 Verificar Eager Loading
**Arquivo**: `backend/app/database/crud.py`

Garantir que queries usam `joinedload` ou `selectinload`:

```python
from sqlalchemy.orm import joinedload, selectinload

def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    """Busca pedidos com eager loading do restaurante."""
    return db.query(Order)\
        .options(selectinload(Order.restaurant))\
        .filter(Order.user_id == user_id)\
        .order_by(Order.order_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
```

### Fase 6: Adicionar Índices (SE NECESSÁRIO)

#### 6.1 Verificar Índices Existentes
Verificar se existem índices em:
- `orders.user_id`
- `orders.restaurant_id`
- `orders.created_at`
- `restaurants.cuisine_type`
- `restaurants.rating`

**Arquivo**: Criar migration se necessário

```python
# Alembic migration
def upgrade():
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_restaurant_id', 'orders', ['restaurant_id'])
    op.create_index('idx_restaurants_cuisine_type', 'restaurants', ['cuisine_type'])
```

## Arquivos a Modificar

1. **`backend/app/database/base.py`** - Pool de conexões
2. **`backend/Dockerfile`** - Workers
3. **`backend/app/api/routes/recommendations.py`** - Otimizar queries (CRÍTICO)
4. **`backend/app/database/crud.py`** - Funções otimizadas de metadados
5. **`backend/app/main.py`** - Headers de cache
6. **`backend/fly.toml`** - Configurações (se necessário)

## Arquivos a Criar

1. **`backend/app/core/cache.py`** - Utilitários de cache
2. **`Docs/OTIMIZACOES.md`** - Documentação das otimizações aplicadas

## Configurações do Fly.io

### Para o Banco de Dados (tastematch-db)

**Opção 1: Via arquivo de configuração**
Criar `postgresql.conf` e aplicar via volume ou init script.

**Opção 2: Via variáveis de ambiente** (se suportado)
```bash
fly secrets set -a tastematch-db \
  POSTGRES_SHARED_BUFFERS=256MB \
  POSTGRES_WORK_MEM=4MB \
  POSTGRES_MAINTENANCE_WORK_MEM=64MB \
  POSTGRES_MAX_CONNECTIONS=20
```

**Opção 3: Via comando fly postgres config**
```bash
fly postgres connect -a tastematch-db
# Dentro do Postgres:
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '4MB';
# ... etc
SELECT pg_reload_conf();
```

### Para o Backend (tastematch-api)

**Arquivo**: `backend/fly.toml`
- Manter 1GB RAM (suficiente com otimizações)
- Ajustar `concurrency` se necessário

## Estratégia de Testes

1. **Testar pool de conexões localmente**
   - Verificar que não excede 8 conexões
   - Testar reciclagem após 30 minutos

2. **Testar queries otimizadas**
   - Verificar que `get_restaurants_metadata` não carrega descrições completas
   - Medir uso de memória antes/depois

3. **Testar cache**
   - Verificar que cache funciona corretamente
   - Testar TTL e invalidação

4. **Monitorar memória em produção**
   - Usar `fly logs` para monitorar uso de memória
   - Verificar que não há mais OOM

## Critérios de Sucesso

1. ✅ Banco de dados não apresenta mais OOM
2. ✅ Pool de conexões limitado a 8 conexões máximas
3. ✅ Postgres configurado com limites de memória (shared_buffers=256MB, work_mem=4MB)
4. ✅ Queries não carregam mais de 10.000 registros na memória
5. ✅ Cache implementado para metadados de restaurantes
6. ✅ Paginação obrigatória em todos os endpoints de listagem
7. ✅ Tempo de resposta reduzido em pelo menos 30%
8. ✅ Uso de memória do banco abaixo de 800MB (deixando margem de segurança)

## Notas Técnicas

### Limites de Memória do Postgres (1GB Total)

- **shared_buffers**: 256MB (25% de 1GB)
- **work_mem**: 4MB por operação
- **max_connections**: 20 conexões
- **work_mem * max_connections**: 80MB (pior caso)
- **maintenance_work_mem**: 64MB
- **Total estimado para Postgres**: ~400MB
- **Margem para sistema**: ~600MB

### Pool de Conexões SQLAlchemy

- **pool_size**: 3 conexões base
- **max_overflow**: 5 conexões adicionais
- **Total máximo**: 8 conexões (alinhado com max_connections=20 do Postgres)
- **pool_recycle**: 1800s (30 minutos)
- **pool_timeout**: 30s

### Cache TTL

- **Metadados de restaurantes**: 60 minutos
- **Recomendações**: 10 minutos
- **Insights**: 7 dias (já implementado)

### Paginação

- **Padrão**: 20 itens por página
- **Máximo**: 50 itens por requisição (reduzido de 100)
- **Offset obrigatório** para navegação

## Priorização de Implementação

1. **CRÍTICO - Fazer primeiro**:
   - Fase 3.1: Remover `get_restaurants(db, limit=10000)` (maior impacto)
   - Fase 1.1: Configurar pool de conexões
   - Fase 2.1: Configurar Postgres para 1GB

2. **IMPORTANTE - Fazer em seguida**:
   - Fase 4: Implementar cache
   - Fase 3.2: Otimizar carregamento de pedidos

3. **MELHORIAS - Fazer depois**:
   - Fase 5: Otimizar queries N+1
   - Fase 6: Adicionar índices se necessário

## Monitoramento Pós-Implementação

1. Monitorar logs do Fly.io:
   ```bash
   fly logs -a tastematch-db
   fly logs -a tastematch-api
   ```

2. Verificar uso de memória:
   ```bash
   fly status -a tastematch-db
   ```

3. Verificar conexões ativas:
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

4. Verificar queries lentas:
   ```sql
   SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
   ```

## Referências

- [PostgreSQL Memory Configuration](https://www.postgresql.org/docs/current/runtime-config-resource.html)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Fly.io Postgres Scaling](https://fly.io/docs/postgres/scaling/)

