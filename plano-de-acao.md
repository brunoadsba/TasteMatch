# TasteMatch - Plano de Ação de Desenvolvimento

> **Plano Executável Baseado em SPEC.md v1.1.0**  
> Última atualização: 24/11/2025  
> **Status:** Fases 1-9 completas (85% MVP) - Tarefas atualizadas conforme progresso real

---

## 📊 Visão Geral do Projeto

### Objetivo
Desenvolver o **TasteMatch** - Agente de Recomendação Inteligente que utiliza IA generativa e machine learning para fornecer recomendações personalizadas de restaurantes baseadas no histórico de pedidos dos usuários.

### Escopo do Projeto

#### Escopo do MVP (Entregável do Teste Técnico)
- **Backend:** API REST com FastAPI, PostgreSQL (pgvector), Auth JWT
- **IA/ML:** Sistema de recomendações com embeddings semânticos
- **GenAI:** Geração de insights contextualizados com LLM (Groq)
- **Frontend:** Dashboard minimalista (React + Vite + Shadcn/UI ou Vanilla JS - decisão justificada)
- **Tempo estimado:** 20-30 horas (foco em robustez do Backend/IA)

**Nota:** Para teste técnico, priorizamos a qualidade do Backend e da IA. Frontend será minimalista para focar no core do produto.

#### Escopo do Produto Final (Versão Completa)
- **Backend:** API REST completa com todos os endpoints
- **Frontend:** Interface completa e polida
- **Testes:** Cobertura completa de testes automatizados
- **Deploy:** Produção completa com CI/CD
- **Tempo estimado:** 60-100+ horas (com todas as melhorias)

### Tempo Estimado Total
- **MVP (Teste Técnico):** 20-30 horas (Backend sólido + IA + Frontend minimalista)
- **Mínimo (POC Funcional):** 40-50 horas
- **Ideal (Com Testes):** 60-80 horas
- **Completo (Produção):** 100+ horas

---

## 🎯 Marcos Principais (Milestones)

| Marco | Descrição | Critério de Sucesso |
|-------|-----------|---------------------|
| **M1** | Setup Completo | Ambiente rodando, banco inicializado, estrutura criada |
| **M2** | Backend Core | Autenticação funcionando, CRUD básico operacional |
| **M3** | Sistema de Recomendações | Algoritmo gerando recomendações personalizadas |
| **M4** | Integração LLM | Insights sendo gerados com GenAI |
| **M5** | Frontend Funcional | Interface exibindo recomendações e insights |
| **M6** | MVP Completo | Sistema end-to-end funcionando, testes básicos |
| **M7** | Produção Ready | Deploy realizado, documentação completa |

---

## 📋 Fases de Desenvolvimento

### FASE 1: Setup Inicial e Infraestrutura
**Objetivo:** Configurar ambiente de desenvolvimento e estrutura base do projeto  
**Tempo estimado:** 4-6 horas  
**Dependências:** Nenhuma

#### Tarefas

1. **Inicializar Repositório Git**
   - [x] Inicializar repositório Git: `git init`
   - [x] Configurar `.gitignore` (já existe, verificar e completar se necessário)
   - [x] Definir estratégia de branches (ex: `main`, `develop`, `feat/...`)
   - [x] Fazer commit inicial: estrutura de pastas e arquivos de configuração

2. **Criar Estrutura de Pastas**
   - [x] Criar diretório `tastematch/`
   - [x] Criar estrutura `backend/app/` conforme SPEC.md seção 8.1
   - [x] Criar estrutura `frontend/`
   - [x] Criar diretórios `data/`, `docs/`, `backend/tests/`, `backend/scripts/`
   - [x] Criar arquivos `__init__.py` necessários

3. **Configurar Ambiente de Desenvolvimento**
   - [x] Criar ambiente virtual Python 3.11+
   - [x] Criar `requirements.txt` com todas as dependências (SPEC.md seção 9.3)
   - [x] Instalar dependências: `pip install -r requirements.txt`
   - [x] Verificar instalação de sentence-transformers e PyTorch

4. **Configurar Docker (Opcional mas Recomendado)**
   - [ ] Criar `docker-compose.yml` na raiz *(Não priorizado para MVP - usando SQLite local)*
   - [ ] Criar `backend/Dockerfile` *(Não priorizado para MVP)*
   - [ ] Configurar PostgreSQL com pgvector *(Para produção - SQLite usado em desenvolvimento)*
   - [ ] Testar `docker-compose up -d` *(Não priorizado para MVP)*

5. **Configurar Variáveis de Ambiente**
   - [x] Criar `.env.example` (já existe, verificar)
   - [x] Criar `.env` local
   - [x] Obter e configurar `GROQ_API_KEY`
   - [x] Configurar `DATABASE_URL`, `JWT_SECRET_KEY`, `SECRET_KEY`

6. **Inicializar Banco de Dados**
   - [x] Criar script `backend/scripts/init_db.py`
   - [x] Implementar criação de tabelas (SPEC.md seção 4.1)
   - [x] Configurar SQLAlchemy base (SPEC.md seção 8.1)
   - [x] Testar conexão com banco
   - [ ] Se usar PostgreSQL: habilitar extensão pgvector *(SQLite usado em desenvolvimento, PostgreSQL para produção)*

**Checkpoint Fase 1:**
- ✅ Repositório Git inicializado e primeiro commit feito
- ✅ Estrutura de pastas criada
- ✅ Ambiente virtual ativo
- ✅ Dependências instaladas
- ✅ `.env` configurado
- ✅ Banco de dados inicializado (tabelas criadas via migrations)

---

### FASE 2: Backend Core - Modelos e Banco de Dados
**Objetivo:** Implementar camada de dados e modelos  
**Tempo estimado:** 6-8 horas  
**Dependências:** Fase 1 completa

#### Tarefas

1. **Modelos SQLAlchemy (ORM)**
   - [x] Criar `backend/app/database/models.py`
   - [x] Implementar modelo `User` (SPEC.md seção 4.1)
   - [x] Implementar modelo `Restaurant` (com campo embedding)
   - [x] Implementar modelo `Order`
   - [x] Implementar modelo `Recommendation`
   - [x] Implementar modelo `UserPreferences`
   - [x] Configurar relacionamentos (Foreign Keys)

2. **Modelos Pydantic (Validação)**
   - [x] Criar `backend/app/models/user.py`
   - [x] Criar `backend/app/models/restaurant.py`
   - [x] Criar `backend/app/models/order.py`
   - [x] Criar `backend/app/models/recommendation.py`
   - [x] Implementar schemas: Base, Create, Response (SPEC.md seção 4.2)

3. **Configuração SQLAlchemy**
   - [x] Criar `backend/app/database/base.py`
   - [x] Configurar engine e session
   - [x] Configurar Base declarativa
   - [x] Implementar função `get_db()` para dependency injection

4. **Configurar Migrations com Alembic**
   - [x] Inicializar Alembic: `alembic init alembic`
   - [x] Configurar Alembic para usar modelos SQLAlchemy
   - [x] Criar primeira migration: `alembic revision --autogenerate -m "Initial schema"`
   - [x] Aplicar migration: `alembic upgrade head`
   - [x] **Nota:** Usar migrations em vez de `db.create_all()` é prática profissional

5. **Operações CRUD Básicas**
   - [x] Criar `backend/app/database/crud.py` (ou módulos separados)
   - [x] Implementar CRUD para Users
   - [x] Implementar CRUD para Restaurants
   - [x] Implementar CRUD para Orders
   - [x] Testar operações básicas (criar, ler, atualizar)

6. **Scripts de Seeding com Embeddings**
   - [x] Criar `backend/scripts/seed_data.py`
   - [x] Gerar 20-30 restaurantes de exemplo (diferentes culinárias) *(25 restaurantes criados)*
   - [x] Gerar 5-10 usuários de exemplo *(5 usuários criados)*
   - [x] Gerar 50-100 pedidos de exemplo (histórico variado) *(67 pedidos criados)*
   - [x] **Integrar geração de embeddings no seed:** Gerar embeddings automaticamente para cada restaurante durante o seeding
   - [x] Executar seeding e validar dados
   - [x] **Otimização:** Fundir seed e geração de embeddings em um único passo para facilitar setup

**Checkpoint Fase 2:**
- ✅ Modelos SQLAlchemy criados e testados
- ✅ Alembic configurado e migrations criadas
- ✅ Modelos Pydantic implementados
- ✅ CRUD básico funcionando
- ✅ Dados de exemplo populados no banco (com embeddings gerados)

---

### FASE 3: Autenticação e Segurança
**Objetivo:** Implementar sistema de autenticação JWT  
**Tempo estimado:** 4-6 horas  
**Dependências:** Fase 2 completa

#### Tarefas

1. **Módulo de Segurança**
   - [x] Criar `backend/app/core/security.py`
   - [x] Implementar hash de senhas com bcrypt (usar bcrypt diretamente)
   - [x] Implementar função `verify_password()`
   - [x] Implementar função `get_password_hash()`
   - [x] Implementar geração de JWT tokens
   - [x] Implementar validação de JWT tokens
   - [x] Configurar expiração de tokens (24h padrão)

2. **Dependências de Autenticação**
   - [x] Criar `backend/app/api/deps.py`
   - [x] Implementar `get_current_user()` (dependency para FastAPI)
   - [x] Implementar validação de token JWT
   - [x] Tratar erros de autenticação (401 Unauthorized)

3. **Endpoints de Autenticação**
   - [x] Criar `backend/app/api/routes/auth.py`
   - [x] Implementar `POST /auth/register` (SPEC.md seção 5.3)
   - [x] Implementar `POST /auth/login` (SPEC.md seção 5.3)
   - [x] Validar dados de entrada (Pydantic)
   - [x] Retornar token JWT na resposta
   - [x] Testar registro e login manualmente

4. **Endpoint Health Check**
   - [x] Criar endpoint `GET /health` (SPEC.md seção 5.3)
   - [x] Verificar conexão com banco de dados
   - [x] Retornar status da aplicação

5. **Configuração FastAPI Base**
   - [x] Criar `backend/app/main.py`
   - [x] Configurar app FastAPI
   - [x] Incluir routers de autenticação
   - [x] Configurar CORS (SPEC.md seção 12.3) *(Configurado para localhost:5173, localhost:5174, 127.0.0.1:5174)*
   - [x] Testar servidor rodando (`uvicorn app.main:app --reload`)

**Checkpoint Fase 3:**
- ✅ Autenticação JWT funcionando
- ✅ Endpoints `/auth/register` e `/auth/login` testados
- ✅ Proteção de rotas com JWT implementada
- ✅ Endpoint `/health` respondendo

---

### FASE 4: Endpoints CRUD Básicos
**Objetivo:** Implementar endpoints REST para recursos principais  
**Tempo estimado:** 6-8 horas  
**Dependências:** Fase 3 completa

#### Tarefas

1. **Endpoints de Usuários**
   - [x] Criar `backend/app/api/routes/users.py`
   - [x] Implementar `GET /api/users/me` (SPEC.md seção 5.7)
   - [x] Implementar `GET /api/users/me/preferences` (SPEC.md seção 5.7)
   - [x] Proteger endpoints com autenticação
   - [x] Testar endpoints com token JWT

2. **Endpoints de Restaurantes**
   - [x] Criar `backend/app/api/routes/restaurants.py`
   - [x] Implementar `GET /api/restaurants` (listagem com paginação) (SPEC.md seção 5.5)
   - [x] Implementar `GET /api/restaurants/{restaurant_id}` (detalhes) (SPEC.md seção 5.5)
   - [x] Implementar filtros (cuisine_type, min_rating)
   - [x] Testar endpoints

3. **Endpoints de Pedidos**
   - [x] Criar `backend/app/api/routes/orders.py`
   - [x] Implementar `GET /api/orders` (histórico do usuário) (SPEC.md seção 5.6)
   - [x] Implementar `POST /api/orders` (criar pedido) (SPEC.md seção 5.6)
   - [x] Validar dados de entrada
   - [x] Associar pedido ao usuário autenticado
   - [x] Testar criação e listagem de pedidos

4. **Integração de Rotas no Main**
   - [x] Incluir router de users no `main.py`
   - [x] Incluir router de restaurants no `main.py`
   - [x] Incluir router de orders no `main.py`
   - [x] Testar todos os endpoints via Swagger (`/docs`)

**Checkpoint Fase 4:**
- ✅ Todos os endpoints CRUD básicos funcionando
- ✅ Autenticação aplicada corretamente
- ✅ Validação de dados funcionando
- ✅ Swagger UI mostrando todos os endpoints

---

### FASE 5: Sistema de Embeddings
**Objetivo:** Implementar geração e armazenamento de embeddings  
**Tempo estimado:** 6-8 horas  
**Dependências:** Fase 4 completa

#### Tarefas

1. **Serviço de Embeddings**
   - [x] Criar `backend/app/core/embeddings.py`
   - [x] Implementar carregamento do modelo sentence-transformers
   - [x] Implementar função `generate_restaurant_embedding()` (SPEC.md seção 6.1)
   - [x] Testar geração de embedding para um restaurante

2. **Script de Geração de Embeddings (Se não integrado no Seed)**
   - [ ] Criar `backend/scripts/generate_embeddings.py` *(Não necessário - embeddings integrados no seed)*
   - [x] Ler todos os restaurantes do banco sem embedding *(Integrado no seed)*
   - [x] Gerar embedding para cada restaurante *(Integrado no seed)*
   - [x] Armazenar embeddings no banco (Vector(384) ou JSON) *(JSON para SQLite)*
   - [x] Executar script e validar embeddings gerados
   - [x] **Nota:** Preferir gerar embeddings durante o seed (ver Fase 2, tarefa 6) *(Implementado)*

3. **Otimização com pgvector (Produção)**
   - [ ] Se usando PostgreSQL: configurar tipo Vector(384) *(Para produção - SQLite em desenvolvimento)*
   - [ ] Atualizar modelo Restaurant para usar Vector *(Para produção)*
   - [ ] Testar armazenamento de embeddings como Vector *(Para produção)*
   - [x] Documentar diferença entre SQLite (JSON) e PostgreSQL (Vector)

4. **Cache de Embeddings**
   - [x] Verificar que embeddings são gerados uma vez
   - [x] Implementar lógica para não recalcular embeddings existentes
   - [x] Validar performance de leitura de embeddings

**Checkpoint Fase 5:**
- ✅ Embeddings sendo gerados corretamente
- ✅ Embeddings armazenados no banco
- ✅ Script de geração executado com sucesso
- ✅ Modelo sentence-transformers carregado e funcionando

---

### FASE 6: Lógica de Recomendação
**Objetivo:** Implementar algoritmo de recomendações personalizadas  
**Tempo estimado:** 8-10 horas  
**Dependências:** Fase 5 completa

#### Tarefas

1. **Cálculo de Preferências do Usuário**
   - [x] Criar `backend/app/core/recommender.py`
   - [x] Implementar `calculate_user_preference_embedding()` (SPEC.md seção 6.1)
   - [x] Implementar `calculate_weight()` (recência e rating)
   - [x] Testar cálculo de embedding do usuário

2. **Extração de Padrões do Usuário**
   - [x] Implementar `extract_user_patterns()` (SPEC.md seção 6.4)
   - [x] Extrair culinárias favoritas
   - [x] Extrair dias/horários preferidos
   - [x] Calcular ticket médio
   - [x] Testar extração de padrões

3. **Cálculo de Similaridade**
   - [ ] Se PostgreSQL: implementar busca com pgvector (SPEC.md seção 6.1) *(Para produção)*
   - [x] Se SQLite: implementar cálculo em memória com scikit-learn
   - [x] Implementar função `get_similar_restaurants()` *(Integrado em generate_recommendations)*
   - [x] Testar cálculo de similaridade

4. **Algoritmo de Recomendação Completo**
   - [x] Implementar `generate_recommendations()` (SPEC.md seção 6.1)
   - [x] Implementar filtros (rating mínimo, excluir recentes)
   - [x] Implementar ordenação por similaridade
   - [x] Implementar fallback para cold start (SPEC.md seção 6.3)
   - [x] Testar com usuário com histórico
   - [x] Testar com usuário novo (cold start)

5. **Cache de Preferências do Usuário**
   - [x] Implementar armazenamento em `user_preferences`
   - [x] Implementar lógica de atualização (quando necessário)
   - [x] Implementar flag `refresh` para forçar recálculo

**Checkpoint Fase 6:**
- ✅ Algoritmo de recomendação gerando resultados
- ✅ Similaridade sendo calculada corretamente
- ✅ Cold start funcionando (fallback para populares)
- ✅ Recomendações fazem sentido com histórico do usuário

---

### FASE 7: Integração com LLM (GenAI)
**Objetivo:** Implementar geração de insights com IA generativa  
**Tempo estimado:** 6-8 horas  
**Dependências:** Fase 6 completa

#### Tarefas

1. **Serviço de LLM**
   - [x] Criar `backend/app/core/llm_service.py`
   - [x] Configurar cliente Groq (SPEC.md seção 7.4)
   - [x] Implementar função `generate_insight()` (SPEC.md seção 7.4)
   - [x] Configurar modelo `llama-3.3-70b-versatile` *(Atualizado de llama-3.1-70b-versatile devido a depreciação)*
   - [x] **Implementar Retry com Backoff Exponencial:** Adicionar tratamento de erros robusto para timeouts e falhas da API Groq
   - [x] Testar chamada básica à API Groq
   - [x] Testar retry em cenários de falha simulados

2. **Templates de Prompts**
   - [x] Implementar função `build_insight_prompt()` (SPEC.md seção 7.3)
   - [x] Criar template base do prompt
   - [x] Integrar contexto do usuário (padrões, histórico)
   - [x] Integrar informações do restaurante
   - [x] Testar geração de prompt completo

3. **Geração de Insights**
   - [x] Integrar geração de insights no fluxo de recomendações
   - [x] Implementar tratamento de erros (fallback genérico)
   - [x] Testar geração de insights para recomendações

4. **Cache de Insights**
   - [x] Implementar `get_cached_insight()` (SPEC.md seção 7.5)
   - [x] Armazenar insights na tabela `recommendations`
   - [x] Implementar TTL de 7 dias
   - [x] Validar cache funcionando

5. **Batching de Insights (Opcional)**
   - [ ] Implementar geração assíncrona em batch (SPEC.md seção 7.5) *(Opcional - não priorizado para MVP)*
   - [ ] Otimizar para gerar múltiplos insights em paralelo *(Opcional - não priorizado para MVP)*
   - [ ] Testar performance *(Opcional - não priorizado para MVP)*

**Checkpoint Fase 7:**
- ✅ LLM gerando insights contextualizados
- ✅ Retry com backoff exponencial implementado
- ✅ Prompts sendo construídos corretamente
- ✅ Cache de insights funcionando
- ✅ Fallback para erros implementado (genérico + retry)

---

### FASE 8: Endpoint de Recomendações
**Objetivo:** Expor endpoint completo de recomendações  
**Tempo estimado:** 4-6 horas  
**Dependências:** Fases 6 e 7 completas

#### Tarefas

1. **Endpoint Principal**
   - [x] Criar `backend/app/api/routes/recommendations.py`
   - [x] Implementar `GET /api/recommendations` (SPEC.md seção 5.4)
   - [x] Integrar com lógica de recomendação
   - [x] Integrar com geração de insights
   - [x] Implementar parâmetros `limit` e `refresh`
   - [x] Retornar formato correto (SPEC.md seção 5.4)

2. **Endpoint de Insight Específico**
   - [x] Implementar `GET /api/recommendations/{restaurant_id}/insight` (SPEC.md seção 5.4)
   - [x] Gerar insight sob demanda
   - [x] Testar endpoint

3. **Integração e Testes**
   - [x] Incluir router de recommendations no `main.py`
   - [x] Testar endpoint completo end-to-end
   - [x] Validar resposta JSON
   - [x] Testar com diferentes usuários e históricos

**Checkpoint Fase 8:**
- ✅ Endpoint `/api/recommendations` funcionando
- ✅ Insights sendo gerados e retornados
- ✅ Resposta no formato especificado
- ✅ Testes manuais bem-sucedidos

---

### FASE 9: Frontend Básico
**Objetivo:** Criar interface web para visualizar recomendações  
**Tempo estimado:** 8-12 horas  
**Dependências:** Fase 8 completa

**Decisão Técnica:** 
- **Opção Recomendada:** React + Vite + Shadcn/UI (mais rápido com componentes prontos, alinhado com mercado/iFood)
- **Opção Alternativa:** HTML/CSS/JS Vanilla (justificar como "decisão de escopo para focar no Backend/IA" se escolhida)

#### Tarefas

1. **Escolher Stack e Configurar**
   - [x] Decidir: React + Vite + Shadcn/UI OU Vanilla JS *(React + Vite + Shadcn/UI escolhido)*
   - [x] Se React: Configurar projeto Vite + React
   - [x] Se React: Instalar Shadcn/UI e componentes necessários
   - [ ] Se Vanilla: Criar estrutura HTML base *(Não aplicável - React escolhido)*

2. **Estrutura HTML/Componentes Base**
   - [x] Criar `frontend/index.html` *(Via Vite)*
   - [x] Criar estrutura básica (header, main, footer) *(Componentes React criados)*
   - [x] Adicionar seções: login, dashboard, recomendações

3. **Cliente HTTP para API**
   - [x] Criar `frontend/api.js` *(Criado como `lib/api.ts` - TypeScript)*
   - [x] Implementar função de login
   - [x] Implementar função de registro
   - [x] Implementar função de buscar recomendações
   - [x] Implementar armazenamento de token (localStorage)

4. **Página de Login**
   - [x] Criar formulário de login
   - [x] Integrar com endpoint `/auth/login`
   - [x] Redirecionar para dashboard após login
   - [x] Tratar erros de autenticação

5. **Dashboard de Recomendações**
   - [x] Criar layout do dashboard
   - [x] Exibir lista de recomendações
   - [x] Exibir insights para cada recomendação
   - [x] Mostrar similarity_score
   - [x] Adicionar botão de refresh

6. **Estilização**
   - [x] Criar `frontend/styles.css` *(Via Tailwind CSS e `index.css`)*
   - [x] Estilizar formulário de login
   - [x] Estilizar cards de recomendações
   - [x] Adicionar responsividade básica
   - [ ] Melhorar UX (loading states, mensagens de erro) *(Parcial - melhorias pendentes)*

7. **Funcionalidades Adicionais**
   - [ ] Exibir histórico de pedidos *(Feature adicional - não MVP)*
   - [ ] Exibir preferências do usuário *(Feature adicional - não MVP)*
   - [x] Adicionar logout
   - [x] Proteger rotas (redirecionar se não autenticado)

**Checkpoint Fase 9:**
- ✅ Frontend exibindo recomendações
- ✅ Login funcionando
- ✅ Insights sendo exibidos
- ✅ Interface básica funcional

---

### FASE 10: Testes e Validação
**Objetivo:** Implementar testes automatizados e validar sistema  
**Tempo estimado:** 6-8 horas  
**Dependências:** Fase 9 completa

#### Tarefas

1. **Configuração de Testes**
   - [ ] Criar `backend/tests/conftest.py` *(Pendente - testes automatizados)*
   - [ ] Configurar fixtures (db, client, user de teste) *(Pendente)*
   - [ ] Configurar banco de dados de teste *(Pendente)*
   - [ ] Configurar pytest-asyncio *(Pendente)*

2. **Testes de Autenticação**
   - [x] Criar `backend/tests/test_auth.py` *(Criado como script manual: `scripts/test_auth_endpoints.py`)*
   - [x] Testar registro de usuário *(Teste manual implementado)*
   - [x] Testar login *(Teste manual implementado)*
   - [x] Testar validação de token *(Teste manual implementado)*
   - [x] Testar proteção de rotas *(Teste manual implementado)*

3. **Testes de Recomendações**
   - [x] Criar `backend/tests/test_recommendations.py` *(Criado como script manual: `scripts/test_recommendations_endpoints.py`)*
   - [x] Testar geração de recomendações *(Teste manual implementado)*
   - [x] Testar cold start (usuário sem histórico) *(Teste manual implementado)*
   - [x] Testar cálculo de similaridade *(Teste manual implementado)*
   - [x] Validar formato de resposta *(Teste manual implementado)*

4. **Testes de Integração**
   - [x] Testar fluxo completo: login → recomendações → insights *(Validação manual realizada)*
   - [x] Testar criação de pedido e impacto nas recomendações *(Validação manual realizada)*
   - [ ] Validar performance (tempo de resposta < 1s) *(Pendente - métricas automatizadas)*

5. **Validação Manual**
   - [x] Testar com diferentes históricos de usuários
   - [x] Validar que recomendações fazem sentido
   - [x] Validar qualidade dos insights gerados
   - [x] Testar edge cases (usuário novo, sem restaurantes, etc.)

**Checkpoint Fase 10:**
- ✅ Testes automatizados passando
- ✅ Cobertura básica de testes
- ✅ Validação manual bem-sucedida
- ✅ Sistema funcionando end-to-end

---

### FASE 11: Refinamento e Otimização
**Objetivo:** Melhorar performance, tratamento de erros e UX  
**Tempo estimado:** 6-8 horas  
**Dependências:** Fase 10 completa

#### Tarefas

1. **Tratamento de Erros**
   - [x] Adicionar tratamento de erros em todos os endpoints
   - [x] Implementar mensagens de erro claras
   - [ ] Adicionar logging estruturado (SPEC.md seção 10.3) *(Pendente - logging básico existente)*
   - [x] Tratar erros de API externa (Groq) *(Retry com backoff implementado)*

2. **Otimização de Performance**
   - [x] Validar cache de embeddings funcionando
   - [x] Validar cache de preferências do usuário
   - [ ] Otimizar queries ao banco (indexes se necessário) *(Pendente - otimização adicional)*
   - [ ] Validar tempo de resposta < 1 segundo *(Pendente - métricas automatizadas)*

3. **Melhorias de UX**
   - [x] Adicionar loading states no frontend *(Parcial - básico implementado)*
   - [ ] Melhorar mensagens de erro no frontend *(Pendente - melhorias pendentes)*
   - [ ] Adicionar feedback visual (toasts, alerts) *(Pendente - não implementado)*
   - [x] Melhorar responsividade *(Básico implementado)*

4. **Documentação**
   - [ ] Atualizar README com instruções finais *(Pendente - documentação básica existe)*
   - [x] Documentar endpoints adicionais (se houver) *(Swagger UI automático)*
   - [x] Adicionar comentários no código complexo
   - [ ] Criar guia de troubleshooting básico *(Pendente)*

**Checkpoint Fase 11:**
- ✅ Tratamento de erros robusto
- ✅ Performance otimizada
- ✅ UX melhorada
- ✅ Documentação atualizada

---

### FASE 12: Deploy e Produção
**Objetivo:** Fazer deploy do sistema em produção  
**Tempo estimado:** 4-6 horas  
**Dependências:** Fase 11 completa

#### Tarefas

1. **Preparação para Deploy**
   - [ ] Configurar variáveis de ambiente de produção
   - [ ] Configurar CORS para frontend (SPEC.md seção 12.3)
   - [ ] Validar que DEBUG=False em produção
   - [ ] Gerar SECRET_KEY seguro

2. **Deploy Backend (Fly.io)**
   - [ ] Criar `backend/fly.toml` (SPEC.md seção 12.1)
   - [ ] Configurar PostgreSQL em produção
   - [ ] Configurar secrets (GROQ_API_KEY, DATABASE_URL)
   - [ ] Fazer deploy: `fly deploy`
   - [ ] Testar API em produção

3. **Deploy Frontend (Netlify)**
   - [ ] Criar `netlify.toml` (SPEC.md seção 12.1)
   - [ ] Configurar redirects para API
   - [ ] Fazer deploy do frontend
   - [ ] Testar integração frontend-backend

4. **Validação Final**
   - [ ] Testar todos os endpoints em produção
   - [ ] Validar que insights estão sendo gerados
   - [ ] Verificar logs e monitoramento
   - [ ] Testar endpoint `/health`

**Checkpoint Fase 12:**
- ✅ Backend deployado e funcionando
- ✅ Frontend deployado e funcionando
- ✅ Sistema completo em produção
- ✅ Documentação de deploy atualizada

---

## ✅ Checklist Executável Completo

### Setup e Infraestrutura
- [x] Repositório Git inicializado com histórico de commits organizado
- [x] Estrutura de pastas criada conforme SPEC.md seção 8.1
- [x] Ambiente virtual Python 3.11+ criado e ativado
- [x] `requirements.txt` criado com todas as dependências
- [x] Dependências instaladas (incluindo sentence-transformers)
- [ ] Docker Compose configurado (opcional mas recomendado) *(Não priorizado para MVP - SQLite usado)*
- [x] `.env` configurado com todas as variáveis
- [x] `GROQ_API_KEY` obtida e configurada
- [x] Banco de dados inicializado (SQLite ou PostgreSQL) *(SQLite usado em desenvolvimento)*
- [ ] Extensão pgvector habilitada (se PostgreSQL) *(Para produção - SQLite em dev)*

### Backend - Modelos e Dados
- [x] Modelos SQLAlchemy criados (User, Restaurant, Order, Recommendation, UserPreferences)
- [x] Alembic configurado para migrations
- [x] Migrations criadas e aplicadas (não usar db.create_all())
- [x] Modelos Pydantic criados (schemas de validação)
- [x] Configuração SQLAlchemy (base.py, get_db)
- [x] CRUD básico implementado
- [x] Scripts de seeding criados e executados (com geração de embeddings integrada)
- [x] Dados de exemplo populados no banco *(25 restaurantes, 5 usuários, 67 pedidos)*

### Backend - Autenticação
- [x] Módulo de segurança implementado (bcrypt, JWT)
- [x] Endpoints `/auth/register` e `/auth/login` funcionando
- [x] Proteção de rotas com JWT implementada
- [x] Endpoint `/health` implementado
- [x] CORS configurado *(localhost:5173, localhost:5174, 127.0.0.1:5174)*

### Backend - Endpoints CRUD
- [x] `GET /api/users/me` implementado
- [x] `GET /api/users/me/preferences` implementado
- [x] `GET /api/restaurants` implementado (com paginação e filtros)
- [x] `GET /api/restaurants/{id}` implementado
- [x] `GET /api/orders` implementado
- [x] `POST /api/orders` implementado
- [x] Todos os endpoints testados via Swagger

### Backend - Sistema de Recomendações
- [x] Serviço de embeddings implementado
- [x] Script de geração de embeddings executado *(Integrado no seed)*
- [x] Embeddings armazenados no banco
- [x] Cálculo de preferências do usuário implementado
- [x] Extração de padrões do usuário implementada
- [x] Cálculo de similaridade implementado (pgvector ou scikit-learn) *(scikit-learn para SQLite)*
- [x] Algoritmo de recomendação completo implementado
- [x] Cold start (fallback) implementado
- [x] Cache de preferências implementado

### Backend - GenAI (LLM)
- [x] Serviço de LLM (Groq) implementado
- [x] Retry com backoff exponencial implementado
- [x] Templates de prompts criados
- [x] Geração de insights implementada
- [x] Cache de insights implementado
- [x] Tratamento de erros robusto (fallback + retry)

### Backend - Endpoint de Recomendações
- [x] `GET /api/recommendations` implementado
- [x] `GET /api/recommendations/{id}/insight` implementado
- [x] Integração completa testada
- [x] Resposta no formato especificado

### Frontend
- [x] Estrutura HTML criada *(React + Vite + TypeScript)*
- [x] Cliente HTTP para API implementado *(lib/api.ts)*
- [x] Página de login funcionando
- [x] Dashboard de recomendações implementado
- [x] Exibição de insights funcionando
- [x] Estilização CSS aplicada *(Tailwind CSS + Shadcn/UI)*
- [x] Responsividade básica implementada
- [x] Funcionalidades adicionais (histórico, logout) *(Logout implementado, histórico pendente)*

### Testes
- [ ] Configuração de testes (pytest, fixtures) *(Pendente - testes automatizados)*
- [x] Testes de autenticação *(Scripts manuais implementados)*
- [x] Testes de recomendações *(Scripts manuais implementados)*
- [x] Testes de integração *(Validação manual realizada)*
- [x] Validação manual completa

### Refinamento
- [x] Tratamento de erros robusto
- [ ] Logging estruturado implementado *(Pendente - logging básico existe)*
- [ ] Performance otimizada (< 1s resposta) *(Pendente - métricas automatizadas)*
- [x] UX melhorada (loading, feedback) *(Parcial - melhorias pendentes)*
- [x] Documentação atualizada *(Básica - melhorias pendentes)*

### Deploy
- [ ] Backend deployado (Fly.io)
- [ ] Frontend deployado (Netlify)
- [ ] CORS configurado corretamente *(Pendente configuração de produção)*
- [ ] Sistema funcionando em produção
- [ ] Endpoint `/health` validado *(Pendente validação em produção)*

---

## 🔄 Fluxo de Trabalho Recomendado

### Desenvolvimento Incremental

1. **Sempre comece pela Fase 1** (Setup)
2. **Complete cada fase antes de avançar** (checkpoints)
3. **Teste após cada fase** (validação incremental)
4. **Use SPEC.md como referência** constante
5. **Trabalhe com IA** usando prompts estruturados (SPEC.md seção 10.2)

### Trabalhando com IA (Cursor, ChatGPT, etc.)

**Template de Prompt:**
```
Baseado na especificação técnica do TasteMatch (SPEC.md):
- Implementar [tarefa específica]
- Seguir estrutura de pastas da seção 8
- Usar modelos Pydantic da seção 4.2
- Seguir padrões de código da seção 10.3
- Referenciar exemplos da seção [X]
```

### Validação Contínua

- **Após cada fase:** Validar checkpoint
- **Após cada endpoint:** Testar via Swagger
- **Após cada feature:** Testar manualmente
- **Antes de avançar:** Garantir que fase anterior está 100% funcional

---

## 📊 Estimativas de Tempo por Fase

| Fase | Tempo Mínimo | Tempo Ideal | Complexidade |
|------|--------------|-------------|--------------|
| Fase 1: Setup | 4h | 6h | Baixa |
| Fase 2: Modelos | 6h | 8h | Média |
| Fase 3: Autenticação | 4h | 6h | Média |
| Fase 4: CRUD | 6h | 8h | Baixa |
| Fase 5: Embeddings | 6h | 8h | Média |
| Fase 6: Recomendações | 8h | 10h | Alta |
| Fase 7: LLM | 6h | 8h | Média |
| Fase 8: Endpoint Recomendações | 4h | 6h | Baixa |
| Fase 9: Frontend | 8h | 12h | Média |
| Fase 10: Testes | 6h | 8h | Média |
| Fase 11: Refinamento | 6h | 8h | Baixa |
| Fase 12: Deploy | 4h | 6h | Baixa |
| **TOTAL** | **68h** | **92h** | - |

---

## 🚀 Estratégia "Fast Track" (Foco no Teste Técnico - 25h)

Para cumprir o prazo de um teste técnico padrão (1 semana ou fim de semana), o escopo será reduzido para:

### Escopo Fast Track

1. **Backend Sólido (10h):** FastAPI, PostgreSQL (pgvector), Auth JWT, Endpoints CRUD
2. **IA & Dados (8h):** Integração Groq, Embeddings, Algoritmo de Recomendação completo
3. **Frontend Minimalista (7h):** Dashboard simples em React (apenas leitura de recomendações e input de pedidos)

### Cortes Estratégicos

- ✅ **Testes Automatizados:** Apenas no Core (Recomendação) - testes unitários básicos
- ✅ **Deploy Automatizado:** Substituído por Docker Compose perfeito e documentado
- ✅ **Histórico Complexo:** Apenas seeding inicial (não implementar CRUD completo de pedidos)
- ✅ **Frontend Completo:** Dashboard minimalista focado em exibir recomendações e insights
- ✅ **Refinamentos:** Tratamento de erros básico, sem otimizações avançadas

### Priorização de Fases (Fast Track)

1. **Fases 1-4:** Essenciais (Setup + Backend Core) - **10h**
2. **Fases 5-6:** Core do produto (Recomendações) - **8h**
3. **Fase 7:** Diferencial (GenAI) - **4h** (versão simplificada)
4. **Fase 8:** Exposição (Endpoint) - **2h**
5. **Fase 9:** Interface mínima (Frontend básico) - **7h**
6. **Fases 10-12:** **Cortadas** (deploy via Docker Compose, testes mínimos)

**Total Fast Track:** ~25-30 horas (alinhado com expectativa de teste técnico)

---

## 🎯 Priorização para MVP Completo (40-50h)

Se tiver mais tempo disponível:

1. **Fases 1-4:** Essenciais (Setup + Backend Core)
2. **Fases 5-6:** Core do produto (Recomendações)
3. **Fase 7:** Diferencial (GenAI)
4. **Fase 8:** Exposição (Endpoint)
5. **Fase 9:** Interface mínima (Frontend básico)

**MVP Completo:** Fases 1-9 = ~40-50 horas

---

## 📝 Notas Importantes

### Dependências Críticas
- **GROQ_API_KEY:** Obrigatória para Fase 7
- **Banco de dados:** SQLite OK para POC, PostgreSQL recomendado para produção
- **Docker:** Opcional mas altamente recomendado para reprodutibilidade

### Decisões Técnicas
- **SQLite vs PostgreSQL:** SQLite para desenvolvimento rápido, PostgreSQL para produção
- **pgvector:** Usar em produção para escalabilidade
- **Frontend:** 
  - **React + Vite + Shadcn/UI** (recomendado): Mais rápido, componentes prontos, alinhado com mercado
  - **Vanilla JS:** Apenas se justificado explicitamente como "decisão de escopo para focar no Backend/IA"
- **Migrations:** Sempre usar Alembic (não `db.create_all()`) - prática profissional

### Riscos e Mitigações
- **Risco:** API Groq pode ter rate limits
  - **Mitigação:** Implementar cache de insights, fallback genérico
- **Risco:** Embeddings podem ser lentos na primeira execução
  - **Mitigação:** Gerar embeddings uma vez e armazenar
- **Risco:** Cálculo de similaridade pode ser lento com muitos restaurantes
  - **Mitigação:** Usar pgvector em produção

---

## 🚀 Próximos Passos Imediatos

1. **Revisar este plano** e confirmar escopo
2. **Iniciar Fase 1** (Setup Inicial)
3. **Configurar ambiente** (Docker ou manual)
4. **Obter GROQ_API_KEY** (gratuita, 5 minutos)
5. **Começar desenvolvimento** seguindo fases sequenciais

---

**Última atualização:** 2025-01-27  
**Baseado em:** SPEC.md v1.1.0  
**Revisado com base em:** gemini.md (análise profissional)  
**Status:** Pronto para execução

---

## 📌 Nota para Avaliadores

Este plano reflete duas abordagens:

1. **Estratégia Fast Track (25h):** Focada em entregar um MVP robusto dentro do prazo típico de teste técnico, priorizando qualidade do Backend e IA sobre completude do Frontend.

2. **Plano Completo (60-100h):** Escopo completo para um produto production-ready, incluindo testes abrangentes, refinamentos e deploy completo.

A estimativa de 100+ horas é para o **produto final completo**. Para o teste técnico, utilize a **Estratégia Fast Track** que entrega o core do sistema em ~25 horas.

