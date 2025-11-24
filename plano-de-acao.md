# TasteMatch - Plano de Ação de Desenvolvimento

> **Plano Executável Baseado em SPEC.md v1.1.0**  
> Última atualização: 2025-01-27

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
   - [ ] Inicializar repositório Git: `git init`
   - [ ] Configurar `.gitignore` (já existe, verificar e completar se necessário)
   - [ ] Definir estratégia de branches (ex: `main`, `develop`, `feat/...`)
   - [ ] Fazer commit inicial: estrutura de pastas e arquivos de configuração

2. **Criar Estrutura de Pastas**
   - [ ] Criar diretório `tastematch/`
   - [ ] Criar estrutura `backend/app/` conforme SPEC.md seção 8.1
   - [ ] Criar estrutura `frontend/`
   - [ ] Criar diretórios `data/`, `docs/`, `backend/tests/`, `backend/scripts/`
   - [ ] Criar arquivos `__init__.py` necessários

3. **Configurar Ambiente de Desenvolvimento**
   - [ ] Criar ambiente virtual Python 3.11+
   - [ ] Criar `requirements.txt` com todas as dependências (SPEC.md seção 9.3)
   - [ ] Instalar dependências: `pip install -r requirements.txt`
   - [ ] Verificar instalação de sentence-transformers e PyTorch

4. **Configurar Docker (Opcional mas Recomendado)**
   - [ ] Criar `docker-compose.yml` na raiz
   - [ ] Criar `backend/Dockerfile`
   - [ ] Configurar PostgreSQL com pgvector
   - [ ] Testar `docker-compose up -d`

5. **Configurar Variáveis de Ambiente**
   - [ ] Criar `.env.example` (já existe, verificar)
   - [ ] Criar `.env` local
   - [ ] Obter e configurar `GROQ_API_KEY`
   - [ ] Configurar `DATABASE_URL`, `JWT_SECRET_KEY`, `SECRET_KEY`

6. **Inicializar Banco de Dados**
   - [ ] Criar script `backend/scripts/init_db.py`
   - [ ] Implementar criação de tabelas (SPEC.md seção 4.1)
   - [ ] Configurar SQLAlchemy base (SPEC.md seção 8.1)
   - [ ] Testar conexão com banco
   - [ ] Se usar PostgreSQL: habilitar extensão pgvector

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
   - [ ] Criar `backend/app/database/models.py`
   - [ ] Implementar modelo `User` (SPEC.md seção 4.1)
   - [ ] Implementar modelo `Restaurant` (com campo embedding)
   - [ ] Implementar modelo `Order`
   - [ ] Implementar modelo `Recommendation`
   - [ ] Implementar modelo `UserPreferences`
   - [ ] Configurar relacionamentos (Foreign Keys)

2. **Modelos Pydantic (Validação)**
   - [ ] Criar `backend/app/models/user.py`
   - [ ] Criar `backend/app/models/restaurant.py`
   - [ ] Criar `backend/app/models/order.py`
   - [ ] Criar `backend/app/models/recommendation.py`
   - [ ] Implementar schemas: Base, Create, Response (SPEC.md seção 4.2)

3. **Configuração SQLAlchemy**
   - [ ] Criar `backend/app/database/base.py`
   - [ ] Configurar engine e session
   - [ ] Configurar Base declarativa
   - [ ] Implementar função `get_db()` para dependency injection

4. **Configurar Migrations com Alembic**
   - [ ] Inicializar Alembic: `alembic init alembic`
   - [ ] Configurar Alembic para usar modelos SQLAlchemy
   - [ ] Criar primeira migration: `alembic revision --autogenerate -m "Initial schema"`
   - [ ] Aplicar migration: `alembic upgrade head`
   - [ ] **Nota:** Usar migrations em vez de `db.create_all()` é prática profissional

5. **Operações CRUD Básicas**
   - [ ] Criar `backend/app/database/crud.py` (ou módulos separados)
   - [ ] Implementar CRUD para Users
   - [ ] Implementar CRUD para Restaurants
   - [ ] Implementar CRUD para Orders
   - [ ] Testar operações básicas (criar, ler, atualizar)

6. **Scripts de Seeding com Embeddings**
   - [ ] Criar `backend/scripts/seed_data.py`
   - [ ] Gerar 20-30 restaurantes de exemplo (diferentes culinárias)
   - [ ] Gerar 5-10 usuários de exemplo
   - [ ] Gerar 50-100 pedidos de exemplo (histórico variado)
   - [ ] **Integrar geração de embeddings no seed:** Gerar embeddings automaticamente para cada restaurante durante o seeding
   - [ ] Executar seeding e validar dados
   - [ ] **Otimização:** Fundir seed e geração de embeddings em um único passo para facilitar setup

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
   - [ ] Criar `backend/app/core/security.py`
   - [ ] Implementar hash de senhas com bcrypt (usar `passlib[bcrypt]`)
   - [ ] Implementar função `verify_password()`
   - [ ] Implementar função `get_password_hash()`
   - [ ] Implementar geração de JWT tokens
   - [ ] Implementar validação de JWT tokens
   - [ ] Configurar expiração de tokens (24h padrão)

2. **Dependências de Autenticação**
   - [ ] Criar `backend/app/api/deps.py`
   - [ ] Implementar `get_current_user()` (dependency para FastAPI)
   - [ ] Implementar validação de token JWT
   - [ ] Tratar erros de autenticação (401 Unauthorized)

3. **Endpoints de Autenticação**
   - [ ] Criar `backend/app/api/routes/auth.py`
   - [ ] Implementar `POST /auth/register` (SPEC.md seção 5.3)
   - [ ] Implementar `POST /auth/login` (SPEC.md seção 5.3)
   - [ ] Validar dados de entrada (Pydantic)
   - [ ] Retornar token JWT na resposta
   - [ ] Testar registro e login manualmente

4. **Endpoint Health Check**
   - [ ] Criar endpoint `GET /health` (SPEC.md seção 5.3)
   - [ ] Verificar conexão com banco de dados
   - [ ] Retornar status da aplicação

5. **Configuração FastAPI Base**
   - [ ] Criar `backend/app/main.py`
   - [ ] Configurar app FastAPI
   - [ ] Incluir routers de autenticação
   - [ ] Configurar CORS (SPEC.md seção 12.3)
   - [ ] Testar servidor rodando (`uvicorn app.main:app --reload`)

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
   - [ ] Criar `backend/app/api/routes/users.py`
   - [ ] Implementar `GET /api/users/me` (SPEC.md seção 5.7)
   - [ ] Implementar `GET /api/users/me/preferences` (SPEC.md seção 5.7)
   - [ ] Proteger endpoints com autenticação
   - [ ] Testar endpoints com token JWT

2. **Endpoints de Restaurantes**
   - [ ] Criar `backend/app/api/routes/restaurants.py`
   - [ ] Implementar `GET /api/restaurants` (listagem com paginação) (SPEC.md seção 5.5)
   - [ ] Implementar `GET /api/restaurants/{restaurant_id}` (detalhes) (SPEC.md seção 5.5)
   - [ ] Implementar filtros (cuisine_type, min_rating)
   - [ ] Testar endpoints

3. **Endpoints de Pedidos**
   - [ ] Criar `backend/app/api/routes/orders.py`
   - [ ] Implementar `GET /api/orders` (histórico do usuário) (SPEC.md seção 5.6)
   - [ ] Implementar `POST /api/orders` (criar pedido) (SPEC.md seção 5.6)
   - [ ] Validar dados de entrada
   - [ ] Associar pedido ao usuário autenticado
   - [ ] Testar criação e listagem de pedidos

4. **Integração de Rotas no Main**
   - [ ] Incluir router de users no `main.py`
   - [ ] Incluir router de restaurants no `main.py`
   - [ ] Incluir router de orders no `main.py`
   - [ ] Testar todos os endpoints via Swagger (`/docs`)

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
   - [ ] Criar `backend/app/core/embeddings.py`
   - [ ] Implementar carregamento do modelo sentence-transformers
   - [ ] Implementar função `generate_restaurant_embedding()` (SPEC.md seção 6.1)
   - [ ] Testar geração de embedding para um restaurante

2. **Script de Geração de Embeddings (Se não integrado no Seed)**
   - [ ] Criar `backend/scripts/generate_embeddings.py` (opcional se já integrado no seed)
   - [ ] Ler todos os restaurantes do banco sem embedding
   - [ ] Gerar embedding para cada restaurante
   - [ ] Armazenar embeddings no banco (Vector(384) ou JSON)
   - [ ] Executar script e validar embeddings gerados
   - [ ] **Nota:** Preferir gerar embeddings durante o seed (ver Fase 2, tarefa 6)

3. **Otimização com pgvector (Produção)**
   - [ ] Se usando PostgreSQL: configurar tipo Vector(384)
   - [ ] Atualizar modelo Restaurant para usar Vector
   - [ ] Testar armazenamento de embeddings como Vector
   - [ ] Documentar diferença entre SQLite (JSON) e PostgreSQL (Vector)

4. **Cache de Embeddings**
   - [ ] Verificar que embeddings são gerados uma vez
   - [ ] Implementar lógica para não recalcular embeddings existentes
   - [ ] Validar performance de leitura de embeddings

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
   - [ ] Criar `backend/app/core/recommender.py`
   - [ ] Implementar `calculate_user_preference_embedding()` (SPEC.md seção 6.1)
   - [ ] Implementar `calculate_weight()` (recência e rating)
   - [ ] Testar cálculo de embedding do usuário

2. **Extração de Padrões do Usuário**
   - [ ] Implementar `extract_user_patterns()` (SPEC.md seção 6.4)
   - [ ] Extrair culinárias favoritas
   - [ ] Extrair dias/horários preferidos
   - [ ] Calcular ticket médio
   - [ ] Testar extração de padrões

3. **Cálculo de Similaridade**
   - [ ] Se PostgreSQL: implementar busca com pgvector (SPEC.md seção 6.1)
   - [ ] Se SQLite: implementar cálculo em memória com scikit-learn
   - [ ] Implementar função `get_similar_restaurants()`
   - [ ] Testar cálculo de similaridade

4. **Algoritmo de Recomendação Completo**
   - [ ] Implementar `generate_recommendations()` (SPEC.md seção 6.1)
   - [ ] Implementar filtros (rating mínimo, excluir recentes)
   - [ ] Implementar ordenação por similaridade
   - [ ] Implementar fallback para cold start (SPEC.md seção 6.3)
   - [ ] Testar com usuário com histórico
   - [ ] Testar com usuário novo (cold start)

5. **Cache de Preferências do Usuário**
   - [ ] Implementar armazenamento em `user_preferences`
   - [ ] Implementar lógica de atualização (quando necessário)
   - [ ] Implementar flag `refresh` para forçar recálculo

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
   - [ ] Criar `backend/app/core/llm_service.py`
   - [ ] Configurar cliente Groq (SPEC.md seção 7.4)
   - [ ] Implementar função `generate_insight()` (SPEC.md seção 7.4)
   - [ ] Configurar modelo `llama-3.1-70b-versatile`
   - [ ] **Implementar Retry com Backoff Exponencial:** Adicionar tratamento de erros robusto para timeouts e falhas da API Groq
   - [ ] Testar chamada básica à API Groq
   - [ ] Testar retry em cenários de falha simulados

2. **Templates de Prompts**
   - [ ] Implementar função `build_insight_prompt()` (SPEC.md seção 7.3)
   - [ ] Criar template base do prompt
   - [ ] Integrar contexto do usuário (padrões, histórico)
   - [ ] Integrar informações do restaurante
   - [ ] Testar geração de prompt completo

3. **Geração de Insights**
   - [ ] Integrar geração de insights no fluxo de recomendações
   - [ ] Implementar tratamento de erros (fallback genérico)
   - [ ] Testar geração de insights para recomendações

4. **Cache de Insights**
   - [ ] Implementar `get_cached_insight()` (SPEC.md seção 7.5)
   - [ ] Armazenar insights na tabela `recommendations`
   - [ ] Implementar TTL de 7 dias
   - [ ] Validar cache funcionando

5. **Batching de Insights (Opcional)**
   - [ ] Implementar geração assíncrona em batch (SPEC.md seção 7.5)
   - [ ] Otimizar para gerar múltiplos insights em paralelo
   - [ ] Testar performance

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
   - [ ] Criar `backend/app/api/routes/recommendations.py`
   - [ ] Implementar `GET /api/recommendations` (SPEC.md seção 5.4)
   - [ ] Integrar com lógica de recomendação
   - [ ] Integrar com geração de insights
   - [ ] Implementar parâmetros `limit` e `refresh`
   - [ ] Retornar formato correto (SPEC.md seção 5.4)

2. **Endpoint de Insight Específico**
   - [ ] Implementar `GET /api/recommendations/{restaurant_id}/insight` (SPEC.md seção 5.4)
   - [ ] Gerar insight sob demanda
   - [ ] Testar endpoint

3. **Integração e Testes**
   - [ ] Incluir router de recommendations no `main.py`
   - [ ] Testar endpoint completo end-to-end
   - [ ] Validar resposta JSON
   - [ ] Testar com diferentes usuários e históricos

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
   - [ ] Decidir: React + Vite + Shadcn/UI OU Vanilla JS
   - [ ] Se React: Configurar projeto Vite + React
   - [ ] Se React: Instalar Shadcn/UI e componentes necessários
   - [ ] Se Vanilla: Criar estrutura HTML base

2. **Estrutura HTML/Componentes Base**
   - [ ] Criar `frontend/index.html`
   - [ ] Criar estrutura básica (header, main, footer)
   - [ ] Adicionar seções: login, dashboard, recomendações

3. **Cliente HTTP para API**
   - [ ] Criar `frontend/api.js`
   - [ ] Implementar função de login
   - [ ] Implementar função de registro
   - [ ] Implementar função de buscar recomendações
   - [ ] Implementar armazenamento de token (localStorage)

4. **Página de Login**
   - [ ] Criar formulário de login
   - [ ] Integrar com endpoint `/auth/login`
   - [ ] Redirecionar para dashboard após login
   - [ ] Tratar erros de autenticação

5. **Dashboard de Recomendações**
   - [ ] Criar layout do dashboard
   - [ ] Exibir lista de recomendações
   - [ ] Exibir insights para cada recomendação
   - [ ] Mostrar similarity_score
   - [ ] Adicionar botão de refresh

6. **Estilização**
   - [ ] Criar `frontend/styles.css`
   - [ ] Estilizar formulário de login
   - [ ] Estilizar cards de recomendações
   - [ ] Adicionar responsividade básica
   - [ ] Melhorar UX (loading states, mensagens de erro)

7. **Funcionalidades Adicionais**
   - [ ] Exibir histórico de pedidos
   - [ ] Exibir preferências do usuário
   - [ ] Adicionar logout
   - [ ] Proteger rotas (redirecionar se não autenticado)

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
   - [ ] Criar `backend/tests/conftest.py`
   - [ ] Configurar fixtures (db, client, user de teste)
   - [ ] Configurar banco de dados de teste
   - [ ] Configurar pytest-asyncio

2. **Testes de Autenticação**
   - [ ] Criar `backend/tests/test_auth.py`
   - [ ] Testar registro de usuário
   - [ ] Testar login
   - [ ] Testar validação de token
   - [ ] Testar proteção de rotas

3. **Testes de Recomendações**
   - [ ] Criar `backend/tests/test_recommendations.py`
   - [ ] Testar geração de recomendações
   - [ ] Testar cold start (usuário sem histórico)
   - [ ] Testar cálculo de similaridade
   - [ ] Validar formato de resposta

4. **Testes de Integração**
   - [ ] Testar fluxo completo: login → recomendações → insights
   - [ ] Testar criação de pedido e impacto nas recomendações
   - [ ] Validar performance (tempo de resposta < 1s)

5. **Validação Manual**
   - [ ] Testar com diferentes históricos de usuários
   - [ ] Validar que recomendações fazem sentido
   - [ ] Validar qualidade dos insights gerados
   - [ ] Testar edge cases (usuário novo, sem restaurantes, etc.)

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
   - [ ] Adicionar tratamento de erros em todos os endpoints
   - [ ] Implementar mensagens de erro claras
   - [ ] Adicionar logging estruturado (SPEC.md seção 10.3)
   - [ ] Tratar erros de API externa (Groq)

2. **Otimização de Performance**
   - [ ] Validar cache de embeddings funcionando
   - [ ] Validar cache de preferências do usuário
   - [ ] Otimizar queries ao banco (indexes se necessário)
   - [ ] Validar tempo de resposta < 1 segundo

3. **Melhorias de UX**
   - [ ] Adicionar loading states no frontend
   - [ ] Melhorar mensagens de erro no frontend
   - [ ] Adicionar feedback visual (toasts, alerts)
   - [ ] Melhorar responsividade

4. **Documentação**
   - [ ] Atualizar README com instruções finais
   - [ ] Documentar endpoints adicionais (se houver)
   - [ ] Adicionar comentários no código complexo
   - [ ] Criar guia de troubleshooting básico

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
- [ ] Repositório Git inicializado com histórico de commits organizado
- [ ] Estrutura de pastas criada conforme SPEC.md seção 8.1
- [ ] Ambiente virtual Python 3.11+ criado e ativado
- [ ] `requirements.txt` criado com todas as dependências
- [ ] Dependências instaladas (incluindo sentence-transformers)
- [ ] Docker Compose configurado (opcional mas recomendado)
- [ ] `.env` configurado com todas as variáveis
- [ ] `GROQ_API_KEY` obtida e configurada
- [ ] Banco de dados inicializado (SQLite ou PostgreSQL)
- [ ] Extensão pgvector habilitada (se PostgreSQL)

### Backend - Modelos e Dados
- [ ] Modelos SQLAlchemy criados (User, Restaurant, Order, Recommendation, UserPreferences)
- [ ] Alembic configurado para migrations
- [ ] Migrations criadas e aplicadas (não usar db.create_all())
- [ ] Modelos Pydantic criados (schemas de validação)
- [ ] Configuração SQLAlchemy (base.py, get_db)
- [ ] CRUD básico implementado
- [ ] Scripts de seeding criados e executados (com geração de embeddings integrada)
- [ ] Dados de exemplo populados no banco

### Backend - Autenticação
- [ ] Módulo de segurança implementado (bcrypt, JWT)
- [ ] Endpoints `/auth/register` e `/auth/login` funcionando
- [ ] Proteção de rotas com JWT implementada
- [ ] Endpoint `/health` implementado
- [ ] CORS configurado

### Backend - Endpoints CRUD
- [ ] `GET /api/users/me` implementado
- [ ] `GET /api/users/me/preferences` implementado
- [ ] `GET /api/restaurants` implementado (com paginação e filtros)
- [ ] `GET /api/restaurants/{id}` implementado
- [ ] `GET /api/orders` implementado
- [ ] `POST /api/orders` implementado
- [ ] Todos os endpoints testados via Swagger

### Backend - Sistema de Recomendações
- [ ] Serviço de embeddings implementado
- [ ] Script de geração de embeddings executado
- [ ] Embeddings armazenados no banco
- [ ] Cálculo de preferências do usuário implementado
- [ ] Extração de padrões do usuário implementada
- [ ] Cálculo de similaridade implementado (pgvector ou scikit-learn)
- [ ] Algoritmo de recomendação completo implementado
- [ ] Cold start (fallback) implementado
- [ ] Cache de preferências implementado

### Backend - GenAI (LLM)
- [ ] Serviço de LLM (Groq) implementado
- [ ] Retry com backoff exponencial implementado
- [ ] Templates de prompts criados
- [ ] Geração de insights implementada
- [ ] Cache de insights implementado
- [ ] Tratamento de erros robusto (fallback + retry)

### Backend - Endpoint de Recomendações
- [ ] `GET /api/recommendations` implementado
- [ ] `GET /api/recommendations/{id}/insight` implementado
- [ ] Integração completa testada
- [ ] Resposta no formato especificado

### Frontend
- [ ] Estrutura HTML criada
- [ ] Cliente HTTP para API implementado
- [ ] Página de login funcionando
- [ ] Dashboard de recomendações implementado
- [ ] Exibição de insights funcionando
- [ ] Estilização CSS aplicada
- [ ] Responsividade básica implementada
- [ ] Funcionalidades adicionais (histórico, logout)

### Testes
- [ ] Configuração de testes (pytest, fixtures)
- [ ] Testes de autenticação
- [ ] Testes de recomendações
- [ ] Testes de integração
- [ ] Validação manual completa

### Refinamento
- [ ] Tratamento de erros robusto
- [ ] Logging estruturado implementado
- [ ] Performance otimizada (< 1s resposta)
- [ ] UX melhorada (loading, feedback)
- [ ] Documentação atualizada

### Deploy
- [ ] Backend deployado (Fly.io)
- [ ] Frontend deployado (Netlify)
- [ ] CORS configurado corretamente
- [ ] Sistema funcionando em produção
- [ ] Endpoint `/health` validado

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

