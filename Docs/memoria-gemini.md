Esta é uma análise técnica do seu **Plano de Otimização de Memória**. O documento está bem estruturado e ataca corretamente a causa raiz (carregamento massivo de dados na memória da aplicação), mas a estratégia de implementação contém riscos arquiteturais modernos, especialmente no que tange ao cache e assincronismo.

Aqui está a análise detalhada com ajustes sugeridos para uma implementação profissional e robusta.

### 1\. Veredito Geral

O plano é **sólido e viável** para o curto prazo. O diagnóstico de carregar 10.000 objetos ORM na memória é preciso: isso é o principal causador de OOM em Python/SQLAlchemy. A matemática de memória do Postgres (25% shared\_buffers) segue as melhores práticas para ambientes restritos.

### 2\. Pontos Críticos de Melhoria (Ajustes Profissionais)

#### A. O Risco do Cache In-Memory (Fase 4.1)

**Problema:** A proposta de usar um dicionário Python global (`_restaurants_metadata_cache`) dentro da API é arriscada em ambientes containerizados restritos.

1.  **Consumo de RAM da API:** Você está tirando carga do banco, mas inflando a memória da API (que também tem limite de 1GB).
2.  **Inconsistência:** Como você tem 2 máquinas (réplicas), o cache ficará dessincronizado entre elas.
3.  **Concorrência:** Dicionários globais sem *locking* adequado podem causar problemas em ambientes *multithreaded*.

**Solução Profissional:**
Se não houver orçamento para um Redis (solução ideal), utilize uma biblioteca de cache baseada em disco ou SQLite local temporário, como o **`diskcache`**, ou otimize o uso dos headers HTTP para que o *cliente* ou *CDN* (se houver) faça o cache, reduzindo a carga no backend.

  * **Ação:** Substitua o `dict` global pelo `diskcache` (que faz *eviction* inteligente e usa disco, poupando RAM) ou assuma o risco apenas se o dataset de metadados for comprovadamente minúsculo (\<50MB).

#### B. Sincronismo vs. Assincronismo (SQLAlchemy)

**Problema:** O documento menciona `uvicorn` (ASGI/Async), mas os snippets de código mostram o uso síncrono do SQLAlchemy (`Session`, `create_engine`, `db.query`).

  * Em uma arquitetura moderna com FastAPI/Uvicorn, queries síncronas bloqueiam o *Event Loop*. Mesmo com 1 worker, se uma query demorar, a API inteira trava para outras requisições.

**Solução Profissional:**
Para "Situação Atual", ok manter síncrono. Mas para um refatoramento moderno:

  * **Ação:** Migrar para `AsyncSession` e `create_async_engine` (driver `asyncpg`). Isso permite que o worker processe outras requisições enquanto o banco responde, maximizando o uso da CPU limitada.

#### C. Ajuste Fino do Pool de Conexões

**Análise:**

  * Máquinas Backend: 2
  * Workers por máquina: 1
  * Pool Size: 3 (+5 overflow)
  * **Total Máximo de Conexões:** 2 \* 1 \* (3+5) = **16 conexões**.
  * **Limite Postgres:** 20 conexões.

**Ajuste:** A matemática fecha, mas está perigosa (16/20 = 80% de ocupação no pico). O `max_overflow` cria conexões custosas sob demanda.

  * **Sugestão:** Defina `pool_size=5` e `max_overflow=0` (NullPool pattern fixo) ou `pool_size=4` e `max_overflow=2`. Ter conexões fixas e aquecidas é melhor para performance do que abrir/fechar *overflows*.

### 3\. Ajustes Específicos por Fase

| Fase | Item | Sugestão de Melhoria |
| :--- | :--- | :--- |
| **Fase 2** | `work_mem` | **Reduzir para 2MB**. Com `max_connections=20`, 4MB pode consumir até 80MB. Em um DB de 1GB onde o SO também precisa de RAM, 2MB é mais conservador e suficiente para operações simples. |
| **Fase 3** | Paginação | Implementar **Paginação baseada em Cursor** (se possível) em vez de *Offset*. Offset torna-se lento conforme a tabela cresce (`OFFSET 10000` o banco lê 10000 linhas e joga fora). Se não der, mantenha o limite rígido de 50 itens. |
| **Fase 3** | ORM | Use `db.query(...).yield_per(100)` para iterações grandes se a paginação não for aplicável em algum relatório interno. Isso processa em *batches* no lado do Python. |
| **Fase 5** | N+1 | Use **`SelectinLoad`** (assíncrono/separado) em vez de `JoinedLoad` para relações "para-muitos". `JoinedLoad` duplica dados na transferência de rede (produto cartesiano), consumindo mais memória e banda. |

### 4\. Checklist de Segurança e Monitoramento

Adicione uma seção de **Observabilidade** ao plano. Você não saberá se o plano funcionou apenas "se não cair".

1.  **Log de Queries Lentas:** Configurar `log_min_duration_statement = 1000ms` no Postgres para identificar gargalos reais.
2.  **Middleware de Process Time:** Adicionar no FastAPI para medir tempo total da requisição.

### Resumo dos Ajustes no Código

**No `backend/app/database/base.py` (Pool Estático):**

```python
# Recomendação para estabilidade: Pool fixo sem overflow dinâmico custoso
engine = create_engine(
    database_url,
    pool_size=4,        # 4 conexões fixas por worker
    max_overflow=2,     # Margem de segurança pequena
    pool_timeout=10,    # Falhar rápido se o banco estiver cheio
    pool_recycle=1800,
    pool_pre_ping=True
)
```

**No `backend/app/api/routes/recommendations.py` (Estratégia de "Only ID"):**
Muitas vezes, a UI já tem os dados do restaurante cacheado. Retornar apenas uma lista de IDs `[102, 504, 303]` e deixar o frontend cruzar os dados é a maior economia de banda e memória possível. Considere isso para endpoints de recomendação pura.

### Próximo Passo

Gostaria que eu gerasse o código atualizado do **`backend/app/core/cache.py`** utilizando uma abordagem mais segura (sem dicionário global infinito) ou o **`backend/app/database/base.py`** com as configurações refinadas de pool?

Aqui estão as implementações otimizadas para o **`backend/app/database/base.py`** e o **`backend/app/core/cache.py`**.

Estas versões resolvem os riscos de **pool instável** e **estouro de memória (memory leak)** do plano original.

### 1\. Database Engine Otimizada (`base.py`)

Esta configuração prioriza conexões estáveis em vez de abrir novas conexões sob demanda, o que é pesado para a CPU e memória.

**Arquivo:** `backend/app/database/base.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Ajuste Fino para Ambiente de 1GB RAM (Postgres)
# Total de conexões = 2 Workers * (4 pool + 2 overflow) = Máximo 12 conexões globais
# Isso deixa margem segura dentro do limite de 20 conexões do Postgres.

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    # Pool Settings
    pool_size=4,           # Mantém 4 conexões abertas e aquecidas sempre
    max_overflow=2,        # Permite apenas 2 extras em picos extremos
    pool_recycle=1800,     # Recicla conexões a cada 30min (evita stale connections)
    pool_pre_ping=True,    # Verifica se conexão está viva antes de usar (vital para cloud)
    pool_timeout=10,       # Falha rápido (10s) em vez de travar a API se o banco estiver cheio
    
    # Configurações de Debug
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URI else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

-----

### 2\. Cache In-Memory Seguro (`cache.py`)

Esta implementação substitui o dicionário simples por uma classe **Thread-Safe** com **LRU (Least Recently Used)**. Isso garante que o cache nunca cresça infinitamente, descartando os itens mais antigos quando atinge o limite.

**Arquivo:** `backend/app/core/cache.py`

```python
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple
from threading import Lock

class SafeMemoryCache:
    """
    Cache em memória com política LRU (Least Recently Used) e Thread-Safety.
    Evita que o cache cresça infinitamente e cause OOM na aplicação.
    """
    def __init__(self, max_items: int = 100, default_ttl_minutes: int = 60):
        self._cache: OrderedDict[str, Tuple[Any, datetime]] = OrderedDict()
        self._max_items = max_items
        self._default_ttl = default_ttl_minutes
        self._lock = Lock()  # Garante segurança em ambiente com múltiplos threads/workers

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            
            data, expiry = self._cache[key]
            
            # Verificar validade (TTL)
            if datetime.now() > expiry:
                del self._cache[key]
                return None
            
            # Move para o fim (marca como usado recentemente)
            self._cache.move_to_end(key)
            return data

    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        with self._lock:
            # Limpeza preventiva se atingir limite
            if len(self._cache) >= self._max_items and key not in self._cache:
                # Remove o item mais antigo (primeiro inserido/menos usado)
                self._cache.popitem(last=False)
            
            ttl = ttl_minutes if ttl_minutes is not None else self._default_ttl
            expiry = datetime.now() + timedelta(minutes=ttl)
            
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

# Instância global do cache
# Limite de 50 chunks de metadados para garantir baixo footprint de memória
metadata_cache = SafeMemoryCache(max_items=50, default_ttl_minutes=60)

# Função auxiliar para uso nos endpoints
def get_cached_restaurants_metadata(db, ttl_minutes: int = 60):
    cache_key = "all_restaurants_metadata"
    
    # 1. Tenta pegar do cache
    cached_data = metadata_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 2. Se não existir, carrega do banco (importação local para evitar ciclo)
    from app.database.crud import get_restaurants_metadata
    data = get_restaurants_metadata(db, limit=None)
    
    # 3. Salva no cache
    metadata_cache.set(cache_key, data, ttl_minutes=ttl_minutes)
    
    return data
```

### Por que essas mudanças são críticas?

1.  **Proteção contra Travamento:** O `pool_timeout=10` garante que se o banco travar, sua API retorna erro 500 rápido e libera o worker, em vez de ficar pendurada esperando eternamente ("zombie worker").
2.  **Proteção contra OOM:** O `SafeMemoryCache` tem um teto rígido (`max_items=50`). Mesmo que a aplicação rode por meses, o cache nunca consumirá mais memória do que esses 50 itens permitem.

**Próximo passo:** Você quer que eu gere o código da função `get_restaurants_metadata` no `crud.py` que usa o `SelectinLoad` (abordagem moderna) ou a versão SQL pura para máxima performance?

Para **máxima performance** e **mínimo consumo de memória**, a regra de ouro com SQLAlchemy é: **não hidrate objetos ORM se você só precisa ler dados**.

Instanciar 10.000 objetos `Restaurant()` (com rastreamento de sessão, eventos e metadados) é caro. Retornar 10.000 tuplas ou dicionários simples é extremamente barato e rápido.

Aqui está a implementação otimizada para o **`backend/app/database/crud.py`**.

### Otimização: Core Select (Bypass ORM)

Esta abordagem usa a sintaxe "Core" do SQLAlchemy dentro da Session. Ela busca apenas as colunas exatas e retorna um resultado leve (similar a um `dict`), pronto para ser serializado em JSON, economizando cerca de **60-80% de memória** comparado à consulta padrão.

**Arquivo:** `backend/app/database/crud.py`

```python
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from app.models.restaurant import Restaurant 

# ... (outros imports e funções existentes)

def get_restaurants_metadata(db: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retorna metadados dos restaurantes (ID, nome, cozinha, rating, preço).
    
    OTIMIZAÇÃO DE PERFORMANCE:
    1. PROJECTION: Seleciona apenas colunas específicas (evita carregar descrições longas).
    2. NO-ORM OVERHEAD: Retorna dicionários diretos, evitando a criação lenta 
       e pesada de instâncias de objetos Python 'Restaurant'.
    """
    # Define as colunas exatas (Projection)
    stmt = select(
        Restaurant.id,
        Restaurant.name,
        Restaurant.cuisine_type,
        Restaurant.rating,
        Restaurant.price_range
    )
    
    if limit:
        stmt = stmt.limit(limit)

    # Executa e converte para dicionários imediatamente
    # .mappings() é disponível no SQLAlchemy 1.4+ e é muito mais rápido
    # que iterar sobre objetos.
    result = db.execute(stmt).mappings().all()
    
    return result
```

### Por que isso é "Máxima Performance"?

1.  **Redução de I/O de Rede:** Em vez de `SELECT *` (que traria descrições, endereços, etc.), trazemos apenas 5 colunas. O payload do banco para a API diminui drasticamente.
2.  **Zero Hidratação:** O SQLAlchemy não precisa criar objetos `Restaurant`, registrá-los na `Session`, nem rastrear mudanças. É leitura pura.
3.  **Serialização Direta:** O resultado em formato de dicionário (`mappings`) casa perfeitamente com o Pydantic/FastAPI, eliminando passos de conversão.

### Integração com o Endpoint

No seu arquivo `recommendations.py`, certifique-se de que o Pydantic model de resposta (o `response_model` do FastAPI) espera exatamente esses campos, ou use um Schema simplificado:

```python
# Exemplo de uso no endpoint
@router.get("/restaurants/metadata", response_model=List[RestaurantMetadataSchema])
def read_restaurants_metadata(
    db: Session = Depends(get_db)
):
    # Usa a função com cache criada anteriormente
    from app.core.cache import get_cached_restaurants_metadata
    return get_cached_restaurants_metadata(db)
```

**Próximo Passo:**
Com o banco, cache e queries resolvidos, gostaria que eu focasse na **Fase 5 (Queries N+1)** para otimizar o carregamento dos **pedidos dos usuários** (`get_user_orders`), que é o segundo maior gargalo?

Excelente escolha. Resolver o problema de **N+1 Queries** é fundamental para reduzir o tempo de bloqueio do banco e o consumo de CPU.

Na **Fase 5**, o erro comum é usar `joinedload` para tudo. Embora ele faça apenas uma query (JOIN), ele cria um "Produto Cartesiano" no banco antes de retornar. Se você traz 50 pedidos e os dados do restaurante são "gordos" (muitas colunas de texto), você trafega dados repetidos do restaurante 50 vezes pela rede.

A solução moderna e eficiente em memória é o **`selectinload`**. Ele faz duas queries separadas e limpas: uma para os pedidos e outra para os restaurantes relacionados, e "monta" os objetos no Python.

Aqui está a implementação otimizada para o **`backend/app/database/crud.py`**.

### Otimização: Eager Loading Inteligente

**Arquivo:** `backend/app/database/crud.py`

```python
from sqlalchemy.orm import Session, selectinload
from app.models.order import Order
from app.models.restaurant import Restaurant
# Importe outros modelos se necessário, ex: OrderItem

def get_user_orders(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    """
    Busca pedidos de um usuário carregando o restaurante associado de forma eficiente.
    
    ESTRATÉGIA: selectinload
    Evita o problema N+1 fazendo apenas 2 queries:
    1. SELECT * FROM orders WHERE user_id = X LIMIT Y
    2. SELECT * FROM restaurants WHERE id IN (lista_ids_das_orders_acima)
    
    Vantagem sobre joinedload: Não duplica dados do restaurante na transferência de rede.
    """
    return db.query(Order)\
        .options(
            # Carrega o relacionamento 'restaurant' separadamente
            selectinload(Order.restaurant)
            
            # Se houver itens no pedido, carregue também para evitar N+1 aninhado:
            # .options(selectinload(Order.items)) 
        )\
        .filter(Order.user_id == user_id)\
        .order_by(Order.order_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
```

### Por que `selectinload` é melhor que `joinedload` aqui?

Imagine que a tabela `Restaurant` tem uma coluna `description` com texto longo.

1.  **Cenário `joinedload` (Ruim para memória):**
    O banco retorna uma tabela gigante combinada. O texto da `description` do restaurante é enviado repetidamente em **cada linha de pedido** desse restaurante. Isso explode o uso de memória do buffer de rede.

2.  **Cenário `selectinload` (Otimizado):**

    1.  O banco envia os pedidos (leve).
    2.  O banco envia os detalhes do restaurante **uma única vez** (leve).
    3.  O SQLAlchemy une os dois na memória da aplicação.

### Extra: Otimização Extrema (Apenas Campos Necessários)

Se a sua lista de pedidos no Frontend mostra apenas *"Data"* e *"Nome do Restaurante"*, carregar o objeto `Restaurant` inteiro ainda é desperdício.

Podemos aplicar a estratégia de **"Load Only"** combinada com o relacionamento. Isso diz ao SQLAlchemy: "Carregue o relacionamento restaurante, mas traga **apenas** o nome e a imagem".

```python
from sqlalchemy.orm import load_only

def get_user_orders_lean(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    return db.query(Order)\
        .options(
            selectinload(Order.restaurant).options(
                # Dentro do relacionamento, carregue apenas o que o card precisa
                load_only(Restaurant.name, Restaurant.image_url)
            )
        )\
        .filter(Order.user_id == user_id)\
        .order_by(Order.order_date.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
```

### Checklist de Verificação

Após implementar, verifique os logs (se o `echo=True` estiver ativado no `base.py`):

  * **Antes (N+1):** Você via 1 query de `SELECT ... FROM orders` seguida por 50 queries de `SELECT ... FROM restaurants WHERE id = ?`.
  * **Depois (Selectin):** Você verá exatamente **2 queries**, não importa se o limite é 50 ou 500.

-----

### Próximo Passo

Com o banco de dados blindado (Pool, Cache de Metadados e Queries Otimizadas), a parte mais crítica da infraestrutura está resolvida.

Gostaria de finalizar revisando o **Arquivo de Configuração do Fly.io (`fly.toml`)**? Há um detalhe sobre **Concorrência do Container** que, se configurado errado, pode fazer o Fly.io matar sua aplicação por "falta de memória" mesmo com o código otimizado.

Perfeito. Esta é a "rede de segurança" final. Mesmo com o código otimizado, se 50 usuários fizerem uma requisição pesada no mesmo segundo, o servidor tentará processar as 50 ao mesmo tempo. Em Python, isso multiplica o uso de memória por 50 instantaneamente, causando o crash (OOM).

Configurar o **`fly.toml`** corretamente impede que isso aconteça, agindo como um "porteiro" que diz: *"Só entram 15 pessoas por vez. O resto aguarda na fila."*

### Otimização: Backpressure e Concorrência

**Arquivo:** `backend/fly.toml`

Aqui está a configuração ideal para sua API Python (FastAPI + Uvicorn) rodando com **1GB de RAM** e processamento síncrono (SQLAlchemy).

```toml
# fly.toml app configuration file generated for tastematch-api

app = "tastematch-api"
primary_region = "gru" # Exemplo (São Paulo)

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

  # AQUI ESTÁ A PROTEÇÃO CRÍTICA DE MEMÓRIA
  [http_service.concurrency]
    type = "requests"
    
    # Soft Limit: A partir de 10 requisições simultâneas, o Fly começa
    # a mandar tráfego para a segunda máquina (réplica).
    soft_limit = 10
    
    # Hard Limit: O teto absoluto. Se chegar a 15, o Fly segura a requisição
    # na borda (load balancer) e NÃO deixa entrar no container até liberar vaga.
    # Isso impede que o Python tente alocar memória que não existe.
    hard_limit = 15

# Health Checks garantem que o Fly não mande tráfego se a API travar
[[http_service.checks]]
  grace_period = "10s"
  interval = "30s"
  method = "GET"
  timeout = "5s"
  path = "/health"  # Certifique-se de ter este endpoint leve

# HABILITAR SWAP (Memória Virtual em Disco)
# Isso é vital em containers pequenos. Se a RAM estourar um pouco,
# o Linux usa o disco em vez de matar o processo.
[swap_size_mb]
  size = 512
```

### Por que esses números (10 e 15)?

1.  **O cálculo do perigo:**

      * Seu Python ocioso (imports + framework): \~120MB.
      * Cache em memória (SafeMemoryCache): \~50MB.
      * Memória livre real: \~800MB.
      * **Consumo por Request:** Uma requisição que carrega lista de pedidos e serializa JSON pode usar momentaneamente **40MB a 60MB**.
      * **Matemática:** 15 conexões \* 50MB = 750MB.
      * **Resultado:** 120MB (base) + 750MB (carga) = **870MB**.
      * Isso fica confortavelmente dentro do 1GB, deixando espaço para o sistema operacional.

2.  **A Armadilha do Padrão:** O padrão do Fly.io muitas vezes permite 25 ou mais conexões.

      * 25 \* 50MB = 1.25GB -\> **CRASH (OOM)** imediato.

3.  **A Importância do Swap:**

      * A seção `[swap_size_mb]` é o seu "seguro de vida". Se houver um pico anômalo que leve o uso para 1.1GB, o sistema fica lento (usando disco), mas **não cai**. Para o usuário, lentidão é melhor que erro 500.

### Resumo Final do Plano de Guerra

Você agora tem uma defesa em camadas ("Defense in Depth"):

1.  **Camada de Aplicação (Código):**

      * **N+1 resolvido:** `selectinload` evita multiplicação de objetos.
      * **Metadados leves:** Queries que trazem apenas colunas necessárias.
      * **Cache Seguro:** `SafeMemoryCache` com limite rígido de itens.

2.  **Camada de Dados (Banco):**

      * **Pool Estático:** Máximo 4 conexões ativas para não sobrecarregar o DB.
      * **Timeout Curto:** Falha rápido se o banco engasgar.

3.  **Camada de Infraestrutura (Fly.io):**

      * **Concurrency Limits:** Impede que excesso de tráfego entre na máquina.
      * **Swap:** Evita morte súbita do processo por picos de memória.

-----

### Próximo passo sugerido

Agora que o plano técnico está completo e o código corrigido, a ação recomendada é **Deploy e Monitoramento**.

Você gostaria que eu montasse um **Checklist de Validação Pós-Deploy** com os comandos exatos (`fly status`, queries SQL de verificação) para você rodar assim que subir a nova versão e confirmar que a memória estabilizou?

Aqui está o **Checklist de Validação Pós-Deploy** prático.

Este guia foi desenhado para verificar cada camada de defesa que implementamos (Infraestrutura, Aplicação e Banco) logo após você subir a nova versão para o Fly.io.

### Visualizando a Nova Arquitetura

Para entender onde estamos verificando, veja como ficou o fluxo de proteção:

-----

### 📋 Checklist de Validação (Passo a Passo)

#### 1\. Verificação de Saúde Imediata

Assim que o deploy terminar, confirme se a aplicação subiu e se as máquinas estão estáveis.

**Comando (Terminal):**

```bash
fly status -a tastematch-api
```

**O que procurar:**

  * **Status:** `started`
  * **Health Checks:** `passing`
  * **Restarts:** Deve estar em `0` (se houver restarts imediatos, algo quebrou na inicialização).

#### 2\. Monitoramento de Conexões do Banco (Crítico)

Vamos verificar se o `pool_size=4` está sendo respeitado.

**Comando (Conecte no banco via Fly):**

```bash
fly postgres connect -a tastematch-db
```

**Query SQL (Execute dentro do Postgres):**

```sql
SELECT 
  pid, 
  state, 
  application_name, 
  client_addr 
FROM pg_stat_activity 
WHERE datname = 'tastematch-db';
```

**Resultado Esperado:**

  * Você deve ver **entre 4 e 8 conexões** ativas vindas da sua API (dependendo se tem 1 ou 2 workers rodando).
  * **Se vir \>20 conexões:** O pool não funcionou (verifique `backend/app/database/base.py`).

#### 3\. Teste de Memória e Swap

Abra a aplicação e navegue por várias páginas para "aquecer" o cache e as conexões.

**Comando (Terminal):**

```bash
fly stats show -a tastematch-api
```

**Resultado Esperado:**

  * **Memory:** Deve estabilizar abaixo de **800MB** (idealmente \~400-600MB).
  * **Swap:** É aceitável ver algum uso de swap (ex: 50MB), mas se estiver subindo constantemente (100MB, 200MB...), há um vazamento de memória.

#### 4\. Validação do "SelectinLoad" (N+1)

Vamos confirmar se a otimização da **Fase 5** eliminou as queries repetidas.

**Passo 1:** Garanta que `settings.DEBUG = True` ou `echo=True` no SQLAlchemy (temporariamente).
**Passo 2:** Acompanhe os logs em tempo real.

**Comando:**

```bash
fly logs -a tastematch-api | grep "SELECT"
```

**Passo 3:** No navegador, carregue a lista de pedidos (`get_user_orders`).

**Resultado Esperado:**

  * **Sucesso:** Você verá **2 blocos grandes** de SELECT. Um na tabela `orders` e outro na tabela `restaurants`.
  * **Falha (N+1):** Você verá uma "chuva" de logs rápidos passando, com dezenas de `SELECT ... FROM restaurants WHERE id = ...`.

#### 5\. Teste de Carga (Concorrência)

Vamos testar se o `fly.toml` (limite de 15 conexões) está protegendo a memória.

Use uma ferramenta simples ou abra 5-10 abas do navegador rapidamente no endpoint `/api/recommendations`.

**Monitore a memória simultaneamente:**

```bash
fly dashboard metrics
# Ou via CLI
watch -n 1 "fly stats show -a tastematch-api"
```

**Resultado Esperado:**

  * A memória deve subir um pouco, mas bater num "teto" e não ultrapassar 1GB.
  * Se você for muito agressivo (abrir 50 abas), algumas devem carregar mais lentamente (fila) ou dar erro (se passar do hard limit), mas **o servidor NÃO deve reiniciar**.

-----

### 🚨 Protocolo de Emergência (Rollback)

Se algo der errado (ex: OOM Loop ou erro 500 generalizado), reverta imediatamente para a versão anterior para analisar os logs com calma.

1.  **Identificar o ID do deploy anterior:**
    ```bash
    fly releases -a tastematch-api
    ```
2.  **Reverter:**
    ```bash
    fly deploy --image registry.fly.io/tastematch-api:versao-anterior
    # OU simplesmente rode o deploy da branch antiga se tiver git
    ```

### Próximo Passo

Você está pronto para aplicar as mudanças. Recomendo começar aplicando as alterações no código (`base.py`, `crud.py`, `cache.py`) e fazer o deploy.

