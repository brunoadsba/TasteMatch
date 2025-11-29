# Plano de Migração para Supabase - TasteMatch

> **Status**: ✅ **CONCLUÍDA**  
> **Data de Conclusão**: 29/11/2025  
> **Última atualização**: 29/11/2025

---

## Objetivo

Migrar banco de dados PostgreSQL do Fly.io Postgres para Supabase, mantendo apenas a API FastAPI no Fly.io (mínimo) e movendo todos os dados pesados (banco completo, embeddings, base RAG) para Supabase.

## Estratégia

- **Fly.io (mínimo)**: Apenas API FastAPI com lógica de negócio
- **Supabase (pesado)**: PostgreSQL completo com pgvector, todos os dados, embeddings e base RAG

---

## Fase 1: Preparação Supabase

### 1.1 Criar projeto Supabase

1. Acessar https://supabase.com
2. Criar novo projeto:
   - Nome: `tastematch`
   - Região: South America (São Paulo)
   - Senha do banco: gerar e guardar em local seguro

### 1.2 Habilitar extensão pgvector

No SQL Editor do Supabase, executar:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verificar instalação:

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 1.3 Obter connection string

1. Dashboard → Settings → Database
2. Copiar "Connection string" (URI mode)
3. Formato esperado:
   - **Connection Pooling (recomendado)**: `postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`
   - **Direto**: `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres`

**Recomendação**: Usar connection pooling (porta 6543) para melhor performance.

---

## Fase 2: Backup dos Dados Atuais

### 2.0 Parar Escrita (Crítico)

**IMPORTANTE**: Para garantir consistência dos dados e evitar perda de novos pedidos durante a migração, é **mandatório** parar a API antes do backup.

```bash
# Colocar API em modo manutenção (Zero downtime não é viável sem replicação lógica complexa)
fly scale count 0 -a tastematch-api

# Verificar que a API está parada
fly status -a tastematch-api
```

**Nota**: A API será reativada apenas na Fase 4, após atualizar a connection string para Supabase.

### 2.1 Fazer dump do banco Fly.io

```bash
# Opção 1: Via proxy (recomendado)
fly proxy 5432:5432 -a tastematch-db &
pg_dump -h localhost -p 5432 -U tastematch -d tastematch \
  -F c -f tastematch_backup.dump

# Opção 2: Via SSH direto
fly ssh console -a tastematch-api
pg_dump -U tastematch -d tastematch -F c -f /tmp/tastematch_backup.dump
exit
fly sftp shell -a tastematch-api
get /tmp/tastematch_backup.dump ./tastematch_backup.dump
```

### 2.2 Validar backup

```bash
# Verificar tamanho
ls -lh tastematch_backup.dump

# Listar objetos do dump
pg_restore --list tastematch_backup.dump | head -20
```

---

## Fase 3: Migração de Schema e Dados

### 3.1 Restaurar schema no Supabase

Restaurar apenas estrutura (sem dados primeiro):

```bash
pg_restore \
  --host=[SUPABASE_HOST] \
  --port=5432 \
  --username=postgres \
  --dbname=postgres \
  --schema-only \
  --no-owner \
  --no-privileges \
  -v \
  tastematch_backup.dump
```

**Nota**: Substituir `[SUPABASE_HOST]` pela URL do Supabase (ex: `db.xxxxx.supabase.co`)

**Nota sobre `pgvector`**: Como a extensão requer superuser e você já a criou na Fase 1.2, se o restore falhar na criação da extensão, **ignore o erro**. O importante são as tabelas e dados. A extensão já está instalada manualmente.

**Se precisar reexecutar o restore**, adicione `--clean --if-exists`:
```bash
pg_restore \
  --host=[SUPABASE_HOST] \
  --port=5432 \
  --username=postgres \
  --dbname=postgres \
  --schema-only \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  -v \
  tastematch_backup.dump
```

### 3.2 Verificar extensão vector e tabelas

No SQL Editor do Supabase:

```sql
-- Verificar extensão
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Verificar tabelas criadas
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Verificar estrutura da tabela restaurants (embedding)
\d restaurants
```

### 3.3 Restaurar dados

Após schema estar criado:

```bash
pg_restore \
  --host=[SUPABASE_HOST] \
  --port=5432 \
  --username=postgres \
  --dbname=postgres \
  --data-only \
  --no-owner \
  --no-privileges \
  -v \
  tastematch_backup.dump
```

**Nota**: O flag `-v` (verbose) permite monitorar o progresso do restore. Se houver avisos sobre "Owner", podem ser ignorados (são esperados com `--no-owner`).

### 3.4 Validar dados migrados

```sql
-- Contar registros
SELECT 
  (SELECT COUNT(*) FROM users) as users_count,
  (SELECT COUNT(*) FROM restaurants) as restaurants_count,
  (SELECT COUNT(*) FROM orders) as orders_count,
  (SELECT COUNT(*) FROM recommendations) as recommendations_count;

-- Verificar embeddings preservados
SELECT COUNT(*) as restaurants_with_embeddings
FROM restaurants 
WHERE embedding IS NOT NULL;
```

---

## Fase 4: Atualização do Código

### 4.1 Ajustar pool de conexões

**Arquivo**: `backend/app/database/base.py`

Ajustar configuração do engine para Supabase com detecção explícita e otimizações para PgBouncer (Transaction Mode):

```python
import os

# Configuração explícita é melhor que implícita (12-factor app)
# Definir variável de ambiente: DB_PROVIDER=supabase
IS_SUPABASE = os.getenv("DB_PROVIDER", "").lower() == "supabase"

# Configurar connect_args com SSL e keepalives para Supabase
connect_args = {}
if IS_SUPABASE:
    connect_args = {
        "sslmode": "require",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        # Se usar Supabase Transaction Pooler (porta 6543) com alguns drivers,
        # pode ser necessário desativar prepared statements:
        # "prepare_threshold": None
    }
elif "sqlite" in database_url:
    connect_args["check_same_thread"] = False

# Pool otimizado para Supabase (mais conexões disponíveis)
# Supabase aguenta mais conexões, aproveite
# Em Transaction Mode, evite overflow agressivo
if IS_SUPABASE:
    pool_size = 20
    max_overflow = 0  # Evitar overflow agressivo em Transaction Mode
    pool_recycle = 300  # Reciclar conexões mais rápido no pooler
else:
    pool_size = 4
    max_overflow = 2
    pool_recycle = 1800

engine = create_engine(
    database_url,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_recycle=pool_recycle,
    pool_pre_ping=True,
    pool_timeout=10,
)
```

**Nota**: Adicionar variável de ambiente `DB_PROVIDER=supabase` no Fly.io secrets (Fase 4.2) para habilitar configurações otimizadas.

### 4.2 Atualizar connection string no Fly.io

**Passo 1**: Remover DATABASE_URL antiga (Fly Postgres)

```bash
fly secrets unset DATABASE_URL -a tastematch-api
```

**Passo 2**: Adicionar nova DATABASE_URL (Supabase) e variável DB_PROVIDER

```bash
# Usando connection pooling (recomendado)
fly secrets set DATABASE_URL=postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres -a tastematch-api

# OU usando conexão direta
fly secrets set DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres -a tastematch-api

# Habilitar configurações otimizadas para Supabase
fly secrets set DB_PROVIDER=supabase -a tastematch-api
```

**Passo 3**: Verificar secrets configurados

```bash
fly secrets list -a tastematch-api
```

**Passo 4**: Reativar API

```bash
# Reativar API agora apontando para Supabase
fly scale count 1 -a tastematch-api

# Verificar que a API está rodando
fly status -a tastematch-api
```

### 4.3 Validar normalização de URL

O código em `backend/app/database/base.py` já normaliza `postgres://` → `postgresql://`, que funciona com Supabase.

---

## Fase 5: Migração da Base RAG

### 5.1 Criar script de migração RAG

**Arquivo**: `backend/scripts/migrate_rag_to_supabase.py`

```python
"""
Script para migrar base de conhecimento RAG para Supabase
"""
from app.database.base import SessionLocal
from app.core.rag_service import RAGService
from app.core.knowledge_base import update_knowledge_base
from app.config import settings

def migrate_rag():
    """Migra base de conhecimento RAG para Supabase"""
    db = SessionLocal()
    try:
        print("🔄 Inicializando RAG service...")
        rag = RAGService(db, settings.DATABASE_URL)
        rag.initialize_vector_store("tastematch_knowledge")
        
        print("🔄 Recriando base de conhecimento...")
        update_knowledge_base(db)
        
        print("✅ Base de conhecimento RAG migrada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao migrar RAG: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_rag()
```

### 5.2 Executar migração RAG

```bash
cd backend
python scripts/migrate_rag_to_supabase.py
```

### 5.3 Validar base RAG

No Supabase SQL Editor:

```sql
-- Verificar coleção PGVector criada
SELECT * FROM langchain_pg_collection WHERE name = 'tastematch_knowledge';

-- Contar documentos na coleção
SELECT COUNT(*) FROM langchain_pg_embedding 
WHERE collection_id = (
  SELECT uuid FROM langchain_pg_collection WHERE name = 'tastematch_knowledge'
);
```

---

## Fase 6: Scripts de Validação

### 6.1 Criar script de validação

**Arquivo**: `backend/scripts/validate_supabase_migration.py`

```python
"""
Script para validar migração para Supabase
"""
from app.database.base import SessionLocal
from sqlalchemy import text

def validate_migration():
    """Valida migração completa para Supabase"""
    db = SessionLocal()
    try:
        # 1. Testar conexão
        db.execute(text("SELECT 1"))
        print("✅ Conexão com Supabase OK")
        
        # 2. Verificar extensão vector
        result = db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        if result.fetchone():
            print("✅ Extensão vector instalada")
        else:
            print("❌ Extensão vector NÃO encontrada")
            return False
        
        # 3. Contar registros
        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        restaurants_count = db.execute(text("SELECT COUNT(*) FROM restaurants")).scalar()
        orders_count = db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        recommendations_count = db.execute(text("SELECT COUNT(*) FROM recommendations")).scalar()
        
        print(f"✅ Usuários: {users_count}")
        print(f"✅ Restaurantes: {restaurants_count}")
        print(f"✅ Pedidos: {orders_count}")
        print(f"✅ Recomendações: {recommendations_count}")
        
        # 4. Verificar embeddings
        embeddings_count = db.execute(
            text("SELECT COUNT(*) FROM restaurants WHERE embedding IS NOT NULL")
        ).scalar()
        print(f"✅ Restaurantes com embeddings: {embeddings_count}")
        
        # 5. Verificar base RAG
        try:
            rag_count = db.execute(
                text("SELECT COUNT(*) FROM langchain_pg_collection WHERE name = 'tastematch_knowledge'")
            ).scalar()
            if rag_count > 0:
                print("✅ Base RAG encontrada")
            else:
                print("⚠️ Base RAG não encontrada (pode ser normal se ainda não migrada)")
        except Exception as e:
            print(f"⚠️ Não foi possível verificar base RAG: {e}")
        
        print("\n✅ Validação completa!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    validate_migration()
```

### 6.2 Executar validação

```bash
cd backend
python scripts/validate_supabase_migration.py
```

---

## Fase 7: Testes e Validação

### 7.1 Testes de conexão

Via Fly.io SSH:

```bash
fly ssh console -a tastematch-api
cd /app
python -c "from app.database.base import engine; engine.connect(); print('✅ Conexão OK')"
exit
```

### 7.2 Testes de endpoints

**Health check:**
```bash
curl https://tastematch-api.fly.dev/health
```

**Login:**
```bash
curl -X POST https://tastematch-api.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@example.com","password":"123456"}'
```

**Recomendações (com token):**
```bash
curl https://tastematch-api.fly.dev/api/recommendations \
  -H "Authorization: Bearer <token>"
```

**Chef Virtual (RAG):**
```bash
curl -X POST https://tastematch-api.fly.dev/api/chat \
  -H "Authorization: Bearer <token>" \
  -F "message=Quais são os melhores restaurantes?"
```

### 7.3 Validação de dados no Supabase

No SQL Editor do Supabase:

```sql
-- Verificar estrutura completa
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Verificar embeddings preservados
SELECT 
    id, 
    name, 
    CASE 
        WHEN embedding IS NULL THEN 'NULL'
        ELSE 'HAS_EMBEDDING'
    END as embedding_status
FROM restaurants 
LIMIT 10;
```

---

## Fase 8: Documentação

### 8.1 Atualizar DEPLOY.md

**Arquivo**: `Docs/DEPLOY.md`

Atualizar seção "Opção B: Serviço Externo" com instruções específicas do Supabase:

```markdown
**Opção B: Supabase (Recomendado para produção)**

1. Criar projeto no Supabase (https://supabase.com)
2. Habilitar extensão pgvector no SQL Editor:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Obter connection string (Settings → Database)
4. Configurar como secret:
   ```bash
   fly secrets set DATABASE_URL=<supabase-connection-string> -a tastematch-api
   ```

**Vantagens do Supabase:**
- Connection pooling automático
- Backups automáticos
- Interface web para gerenciamento
- Escalabilidade gerenciada
```

---

## Fase 9: Descomissionar Fly Postgres (Opcional)

### 9.1 Validação final

Antes de remover Fly Postgres, confirmar:

- [ ] Todos os testes passando
- [ ] Endpoints funcionando corretamente
- [ ] RAG/Chef Virtual funcionando
- [ ] Embeddings preservados
- [ ] Performance adequada
- [ ] Monitoramento ativo por pelo menos 3 dias

### 9.2 Remover Fly Postgres

**Apenas após validação completa:**

```bash
# Desanexar banco do app
fly postgres detach tastematch-db -a tastematch-api

# Destruir banco (CUIDADO: ação irreversível!)
fly postgres destroy tastematch-db
```

**Nota**: Manter backup do dump por segurança.

---

## Plano de Rollback (Emergência)

Se a validação falhar e o serviço precisar voltar ao ar imediatamente:

### 1. Reverter Connection String

```bash
# Restaurar DATABASE_URL original do Fly Postgres
fly secrets set DATABASE_URL=<URL_ANTIGA_DO_FLY_POSTGRES> -a tastematch-api

# Remover variável DB_PROVIDER (se adicionada)
fly secrets unset DB_PROVIDER -a tastematch-api
```

**Nota**: Guardar a URL antiga do Fly Postgres antes de iniciar a migração.

### 2. Reativar API

```bash
# Reativar API com configuração antiga
fly scale count 1 -a tastematch-api

# Verificar status
fly status -a tastematch-api
```

### 3. Análise

Verificar logs do Fly para entender o erro antes de tentar novamente:

```bash
# Ver logs recentes
fly logs -a tastematch-api

# Ver logs com mais contexto
fly logs -a tastematch-api --limit 100
```

### 4. Validação Pós-Rollback

```bash
# Testar health check
curl https://tastematch-api.fly.dev/health

# Testar endpoint crítico
curl -X POST https://tastematch-api.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@example.com","password":"123456"}'
```

**Importante**: Após rollback bem-sucedido, analisar os logs e corrigir o problema antes de tentar a migração novamente.

---

## Checklist de Migração

### Pré-migração
- [ ] Projeto Supabase criado
- [ ] Extensão pgvector habilitada
- [ ] Connection string obtida e testada
- [ ] **API parada (fly scale count 0)** - Crítico para consistência
- [ ] URL antiga do Fly Postgres guardada (para rollback)
- [ ] Backup do banco Fly.io realizado e validado

### Migração
- [ ] Schema restaurado no Supabase (com verbose para monitoramento)
- [ ] Dados migrados e validados
- [ ] Base RAG migrada
- [ ] Connection string atualizada no Fly.io
- [ ] Variável DB_PROVIDER=supabase configurada
- [ ] Pool de conexões ajustado no código (com PgBouncer otimizado)
- [ ] SSL configurado
- [ ] **API reativada (fly scale count 1)** - Após atualizar connection string

### Validação
- [ ] Conexão testada via SSH
- [ ] Endpoints funcionando (health, auth, recommendations)
- [ ] Autenticação OK
- [ ] Recomendações OK
- [ ] RAG/Chef Virtual OK
- [ ] Embeddings preservados
- [ ] Script de validação executado com sucesso

### Pós-migração
- [ ] Monitoramento ativo por 3+ dias
- [ ] Performance validada
- [ ] Documentação atualizada
- [ ] Fly Postgres descomissionado (opcional)

---

## Troubleshooting

### Problema: Erro de SSL

**Sintoma**: `SSL connection required`

**Solução**: Adicionar `sslmode=require` no `connect_args` do engine (ver Fase 4.1)

### Problema: Erro de conexão

**Sintoma**: `Connection refused` ou timeout

**Solução**: 
- Verificar connection string está correta
- Usar connection pooling (porta 6543) em vez de direta
- Verificar firewall/network do Supabase

### Problema: Extensão vector não encontrada

**Sintoma**: `extension "vector" does not exist`

**Solução**: Executar no SQL Editor do Supabase:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Problema: Base RAG não funciona

**Sintoma**: Erro ao inicializar PGVector

**Solução**:
- Verificar se extensão vector está instalada
- Executar script de migração RAG novamente
- Verificar connection string está correta

### Problema: Pool de conexões esgotado

**Sintoma**: `too many connections`

**Solução**:
- Reduzir `pool_size` e `max_overflow` no código
- Usar connection pooling do Supabase (porta 6543)
- Verificar limites do plano Supabase

---

## Arquivos Modificados/Criados

### Modificados
1. `backend/app/database/base.py` - Ajustar pool e SSL para Supabase

### Criados
1. `backend/scripts/migrate_rag_to_supabase.py` - Script de migração RAG
2. `backend/scripts/validate_supabase_migration.py` - Script de validação
3. `Docs/supabase.md` - Este documento

### Atualizados
1. `Docs/DEPLOY.md` - Adicionar instruções do Supabase

---

## Referências

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [PGVector Extension](https://github.com/pgvector/pgvector)
- [Fly.io Postgres](https://fly.io/docs/postgres/)

---

**Última atualização**: 29/11/2025  
**Status**: ✅ **CONCLUÍDA** - Migração 100% completa

## 🎉 Resumo da Migração Concluída

**Data**: 29/11/2025  
**Versão API**: v42

### ✅ Itens Migrados

- ✅ Schema completo (10 tabelas)
- ✅ 15 usuários
- ✅ 24 restaurantes
- ✅ 102 pedidos
- ✅ 5.156 recomendações
- ✅ 24 embeddings de restaurantes (regenerados)
- ✅ Base RAG (64 documentos na coleção `tastematch_knowledge`)

### ✅ Configurações Aplicadas

- ✅ Connection string Supabase configurada no Fly.io
- ✅ `DB_PROVIDER=supabase` configurado
- ✅ Pool de conexões otimizado para Supabase
- ✅ SSL configurado (`sslmode=require`)
- ✅ Extensão `pgvector` habilitada

### ✅ Validações Realizadas

- ✅ Conexão com Supabase testada
- ✅ Endpoints da API funcionando
- ✅ Embeddings validados (24/24)
- ✅ Base RAG validada (64 documentos)
- ✅ Health check retornando "healthy"

**Para detalhes completos, consulte:**
- [status-migracao-supabase.md](./status-migracao-supabase.md) - Status detalhado
- [erros-deploy-migracao.md](./erros-deploy-migracao.md) - Erros e soluções durante o processo

---

## Notas de Segurança e Boas Práticas

### Integridade de Dados
- **Sempre** parar a API antes do backup para garantir consistência
- Manter backup do dump por segurança mesmo após migração bem-sucedida
- Guardar URL antiga do Fly Postgres para rollback rápido

### Configuração Explícita
- Usar variável de ambiente `DB_PROVIDER` em vez de detecção implícita
- Configuração explícita segue princípios 12-factor app
- Facilita manutenção e debugging

### PgBouncer Transaction Mode
- Supabase usa Transaction Mode no pooler (porta 6543)
- Evitar `max_overflow` agressivo
- Reciclar conexões mais rápido (`pool_recycle=300`)
- Considerar desativar prepared statements se necessário

### Monitoramento
- Usar flags `-v` (verbose) em comandos críticos
- Verificar logs após cada fase
- Validar dados em cada etapa antes de prosseguir

