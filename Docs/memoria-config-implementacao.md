# Plano de Implementação Consolidado - Otimização de Memória TasteMatch

## Objetivo
Resolver OOM do banco de dados (1GB fixo) e otimizar performance da aplicação, integrando as melhores práticas das análises técnicas (Manus AI + Gemini).

## Análise Consolidada das Recomendações

### Pontos de Consenso
- ✅ Pool de conexões deve ser conservador (pool_size=3-4, max_overflow=0-2)
- ✅ Remover carregamento de 10.000 restaurantes (CRÍTICO)
- ✅ Implementar cache thread-safe com limite rígido
- ✅ Configurar Postgres para 1GB (shared_buffers=256MB, work_mem=2-4MB)
- ✅ Usar selectinload ao invés de joinedload para evitar produto cartesiano
- ✅ Queries com projection (apenas colunas necessárias)

### Decisões Técnicas Consolidadas

| Item | Manus AI | Gemini | Decisão Final |
|------|----------|--------|---------------|
| **pool_size** | 4 | 4 | **4** (consenso) |
| **max_overflow** | 0 | 2 | **2** (balance: segurança + flexibilidade) |
| **work_mem** | 2MB | 4MB | **2MB** (mais conservador para 1GB) |
| **Cache** | Redis (ideal) | SafeMemoryCache (MVP) | **SafeMemoryCache primeiro, Redis depois** |
| **Eager Loading** | selectinload | selectinload | **selectinload** (consenso) |

## Fases de Implementação

### Fase 1: Pool de Conexões e Configuração Base (CRÍTICO - Prioridade 1)

#### 1.1 Configurar SQLAlchemy Engine
**Arquivo**: `backend/app/database/base.py`

**Implementação**:
```python
engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    echo=settings.DEBUG,
    # Pool otimizado para 1GB: 2 workers * (4 + 2) = máximo 12 conexões
    pool_size=4,              # 4 conexões fixas por worker
    max_overflow=2,           # 2 extras em picos (total: 6 por worker)
    pool_recycle=1800,       # Reciclar após 30min
    pool_pre_ping=True,       # Verificar conexão antes de usar
    pool_timeout=10,          # Falhar rápido se banco cheio
)
```

**Justificativa**: 
- Total máximo: 2 workers * 6 = 12 conexões (dentro do limite de 20 do Postgres)
- `max_overflow=2` oferece margem sem risco de picos excessivos
- `pool_timeout=10` evita workers "zombies" esperando indefinidamente

#### 1.2 Ajustar Workers do Backend
**Arquivo**: `backend/Dockerfile`

**Mudança**: Manter `--workers 1` (já está correto)

#### 1.3 Configurar Postgres para 1GB
**Aplicar via Fly.io secrets ou postgresql.conf**

**Configurações**:
```bash
shared_buffers=256MB          # 25% de 1GB
work_mem=2MB                  # Conservador (Manus AI)
maintenance_work_mem=64MB
effective_cache_size=768MB
max_connections=20            # Reduzido de padrão
temp_buffers=8MB
```

**Cálculo de Memória**:
- shared_buffers: 256MB
- work_mem * max_connections: 2MB * 20 = 40MB (pior caso)
- maintenance_work_mem: 64MB
- **Total estimado**: ~360MB para Postgres, deixando ~640MB para sistema

### Fase 2: Otimizar Queries Críticas (CRÍTICO - Prioridade 1)

#### 2.1 Criar Função de Metadados Otimizada
**Arquivo**: `backend/app/database/crud.py`

**Nova função** (usando projection - apenas colunas necessárias):
```python
def get_restaurants_metadata(db: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retorna apenas metadados essenciais (sem descrições longas).
    OTIMIZAÇÃO: Projection + No-ORM overhead = 60-80% menos memória.
    """
    from sqlalchemy import select
    from typing import Dict, Any
    
    stmt = select(
        Restaurant.id,
        Restaurant.name,
        Restaurant.cuisine_type,
        Restaurant.rating,
        Restaurant.price_range
    )
    
    if limit:
        stmt = stmt.limit(limit)
    
    # Retorna dicionários diretos (sem hidratação de objetos ORM)
    result = db.execute(stmt).mappings().all()
    return [dict(row) for row in result]
```

#### 2.2 Substituir get_restaurants(limit=10000) em recommendations.py
**Arquivo**: `backend/app/api/routes/recommendations.py`

**Mudanças**:
- Linha 107: `all_restaurants = get_restaurants_metadata(db, limit=None)` 
- Linha 277: `all_restaurants = get_restaurants_metadata(db, limit=None)`
- Linha 362: `all_restaurants = get_restaurants_metadata(db, limit=None)`

**Impacto**: Reduz uso de memória em 60-80% ao carregar metadados

#### 2.3 Otimizar get_user_orders com selectinload
**Arquivo**: `backend/app/database/crud.py`

**Mudança na função existente**:
```python
from sqlalchemy.orm import selectinload

def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """
    Busca pedidos com selectinload (evita produto cartesiano do joinedload).
    Faz apenas 2 queries: orders + restaurants (IN clause).
    """
    return db.query(Order)\
        .options(selectinload(Order.restaurant))\
        .filter(Order.user_id == user_id)\
        .order_by(Order.order_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
```

**Justificativa**: 
- `selectinload` faz 2 queries separadas ao invés de JOIN gigante
- Evita duplicação de dados do restaurante na rede
- Reduz memória de transferência em ~40-60%

### Fase 3: Implementar Cache Thread-Safe (IMPORTANTE - Prioridade 2)

#### 3.1 Criar SafeMemoryCache
**Arquivo**: `backend/app/core/cache.py` (criar)

**Implementação completa** (do Gemini):
```python
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple
from threading import Lock

class SafeMemoryCache:
    """
    Cache em memória com política LRU (Least Recently Used) e Thread-Safety.
    Evita crescimento infinito e OOM na aplicação.
    """
    def __init__(self, max_items: int = 50, default_ttl_minutes: int = 60):
        self._cache: OrderedDict[str, Tuple[Any, datetime]] = OrderedDict()
        self._max_items = max_items
        self._default_ttl = default_ttl_minutes
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            
            data, expiry = self._cache[key]
            
            if datetime.now() > expiry:
                del self._cache[key]
                return None
            
            self._cache.move_to_end(key)
            return data

    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        with self._lock:
            if len(self._cache) >= self._max_items and key not in self._cache:
                self._cache.popitem(last=False)
            
            ttl = ttl_minutes if ttl_minutes is not None else self._default_ttl
            expiry = datetime.now() + timedelta(minutes=ttl)
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

# Instância global
metadata_cache = SafeMemoryCache(max_items=50, default_ttl_minutes=60)

def get_cached_restaurants_metadata(db, ttl_minutes: int = 60):
    """Função auxiliar para cache de metadados de restaurantes."""
    cache_key = "all_restaurants_metadata"
    
    cached_data = metadata_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    from app.database.crud import get_restaurants_metadata
    data = get_restaurants_metadata(db, limit=None)
    
    metadata_cache.set(cache_key, data, ttl_minutes=ttl_minutes)
    return data
```

#### 3.2 Integrar Cache em recommendations.py
**Arquivo**: `backend/app/api/routes/recommendations.py`

**Mudanças**:
```python
from app.core.cache import get_cached_restaurants_metadata

# Substituir todas as chamadas:
# all_restaurants = get_restaurants_metadata(db, limit=None)
# Por:
all_restaurants = get_cached_restaurants_metadata(db, ttl_minutes=60)
```

### Fase 4: Configurar Fly.io (IMPORTANTE - Prioridade 2)

#### 4.1 Ajustar fly.toml - Concorrência e Swap
**Arquivo**: `backend/fly.toml`

**Adicionar/Atualizar**:
```toml
[http_service.concurrency]
  type = "requests"
  soft_limit = 10    # Começa a distribuir para 2ª máquina
  hard_limit = 15    # Teto absoluto (proteção OOM)

# Habilitar swap (memória virtual em disco)
[swap_size_mb]
  size = 512
```

**Justificativa**:
- 15 conexões * 50MB = 750MB (dentro de 1GB)
- Swap de 512MB evita morte súbita em picos anômalos

#### 4.2 Health Checks Otimizados
**Arquivo**: `backend/fly.toml`

**Configuração**:
```toml
[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"
```

### Fase 5: Headers HTTP Cache (MELHORIA - Prioridade 3)

#### 5.1 Middleware de Cache-Control
**Arquivo**: `backend/app/main.py`

**Adicionar middleware**:
```python
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    
    if request.method == "GET":
        if "/api/restaurants" in str(request.url.path):
            response.headers["Cache-Control"] = "public, max-age=300"  # 5min
        elif "/api/recommendations" in str(request.url.path):
            response.headers["Cache-Control"] = "private, max-age=600"  # 10min
    
    return response
```

### Fase 6: Observabilidade Básica (MELHORIA - Prioridade 3)

#### 6.1 Log de Queries Lentas (Postgres)
**Configurar via Fly.io**:
```sql
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries > 1s
SELECT pg_reload_conf();
```

#### 6.2 Middleware de Process Time
**Arquivo**: `backend/app/main.py` (já existe, verificar se está completo)

**Verificar se inclui**:
- Tempo total da requisição
- Status code
- Endpoint

## Arquivos a Modificar

1. **`backend/app/database/base.py`** - Pool de conexões
2. **`backend/app/database/crud.py`** - Funções otimizadas (get_restaurants_metadata, get_user_orders)
3. **`backend/app/api/routes/recommendations.py`** - Substituir get_restaurants(limit=10000)
4. **`backend/app/main.py`** - Middleware de cache headers
5. **`backend/fly.toml`** - Concorrência e swap

## Arquivos a Criar

1. **`backend/app/core/cache.py`** - SafeMemoryCache completo

## Configurações do Fly.io

### Para o Banco (tastematch-db)
```bash
# Via fly postgres connect ou secrets
fly postgres connect -a tastematch-db

# Dentro do Postgres:
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '2MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET max_connections = '20';
ALTER SYSTEM SET log_min_duration_statement = '1000';
SELECT pg_reload_conf();
```

## Checklist de Validação Pós-Deploy

### 1. Verificação Imediata
```bash
fly status -a tastematch-api
# Verificar: started, health checks passing, restarts = 0
```

### 2. Monitorar Conexões do Banco
```bash
fly postgres connect -a tastematch-db
```
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'tastematch-db';
-- Esperado: 4-12 conexões (não >20)
```

### 3. Monitorar Memória
```bash
fly stats show -a tastematch-api
# Esperado: <800MB (idealmente 400-600MB)
```

### 4. Validar SelectinLoad (N+1 resolvido)
```bash
fly logs -a tastematch-api | grep "SELECT"
# Carregar lista de pedidos no navegador
# Esperado: 2 blocos de SELECT (orders + restaurants), não dezenas
```

### 5. Teste de Carga
```bash
# Abrir 5-10 abas no endpoint /api/recommendations
fly stats show -a tastematch-api
# Esperado: Memória sobe mas não ultrapassa 1GB
```

## Priorização de Implementação

### Sprint 1 (CRÍTICO - Fazer Primeiro)
1. ✅ Fase 1.1: Pool de conexões
2. ✅ Fase 1.3: Configurar Postgres
3. ✅ Fase 2.1: Criar get_restaurants_metadata
4. ✅ Fase 2.2: Substituir get_restaurants(limit=10000)

### Sprint 2 (IMPORTANTE - Fazer em Seguida)
5. ✅ Fase 2.3: Otimizar get_user_orders com selectinload
6. ✅ Fase 3: Implementar SafeMemoryCache
7. ✅ Fase 4: Configurar fly.toml

### Sprint 3 (MELHORIAS - Fazer Depois)
8. ✅ Fase 5: Headers HTTP Cache
9. ✅ Fase 6: Observabilidade básica

## Critérios de Sucesso

1. ✅ Banco não apresenta mais OOM
2. ✅ Pool limitado a 12 conexões máximas (2 workers * 6)
3. ✅ Postgres configurado (shared_buffers=256MB, work_mem=2MB)
4. ✅ Queries não carregam mais de 10.000 objetos ORM
5. ✅ Cache implementado (SafeMemoryCache com limite de 50 itens)
6. ✅ N+1 resolvido (selectinload implementado)
7. ✅ Memória do backend <800MB em operação normal
8. ✅ Concorrência limitada (hard_limit=15)

## Notas Técnicas Finais

### Pool de Conexões
- **Total máximo**: 2 workers * (4 + 2) = 12 conexões
- **Dentro do limite**: 12 < 20 (max_connections do Postgres)
- **Margem de segurança**: 40% de headroom

### Memória Postgres (1GB Total)
- shared_buffers: 256MB (25%)
- work_mem * max_connections: 40MB (pior caso)
- maintenance_work_mem: 64MB
- **Total**: ~360MB (36% de 1GB)
- **Margem**: ~640MB para sistema e operações

### Cache
- **Limite**: 50 itens (proteção contra crescimento infinito)
- **TTL padrão**: 60 minutos
- **Thread-safe**: Lock para segurança em multi-thread

### Próximos Passos (Futuro)
- Migrar cache para Redis (quando houver orçamento)
- Implementar OpenTelemetry para tracing distribuído
- Considerar PGBouncer se disponível no Fly.io
- Implementar paginação baseada em cursor (se necessário)

## Referências

- [PostgreSQL Memory Configuration](https://www.postgresql.org/docs/current/runtime-config-resource.html)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html)
- [Fly.io Postgres Scaling](https://fly.io/docs/postgres/scaling/)
- [SQLAlchemy selectinload vs joinedload](https://docs.sqlalchemy.org/en/20/orm/loading_relationships.html#selectin-eager-loading)

