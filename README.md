# TasteMatch 🍽️

> **Agente de Recomendação Inteligente para Delivery**  
> Sistema de recomendações personalizadas que utiliza IA generativa e machine learning

[![Status](https://img.shields.io/badge/status-MVP%20Funcional-success)]()
[![Backend](https://img.shields.io/badge/backend-FastAPI-blue)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb)]()
[![IA](https://img.shields.io/badge/IA-Groq%20LLM-orange)]()

---

## 📋 Sobre o Projeto

O **TasteMatch** é um agente de recomendação inteligente que:

- 🎯 Analisa padrões de comportamento do usuário através de embeddings semânticos
- 🤖 Gera recomendações personalizadas usando similaridade vetorial
- 💡 Cria insights contextualizados com IA generativa explicando **por quê** cada restaurante foi recomendado
- ⚡ Processa recomendações em tempo real com cache inteligente
- 🔐 Sistema completo de autenticação JWT
- 🎨 Interface moderna com React + TypeScript + Shadcn/UI, com tema claro/escuro
- 📱 Design mobile-first totalmente responsivo com menu hambúrguer e viewports dinâmicos

### Principais recursos de demonstração

- **Onboarding Gamificado**: novo usuário cria seu perfil de sabor em 3 etapas (culinárias, preço, restrições), gerando vetor sintético para recomendações personalizadas desde o primeiro acesso
- **Modo Demonstração**: ativa um fluxo guiado para simular pedidos sem impactar dados reais
- **Chef Recomenda**: card hero que destaca a recomendação principal do usuário, com explicação em linguagem natural
- **Raciocínio do Chef**: modal com explicação detalhada do porquê daquela escolha, baseada no perfil do usuário
- **Simulador de Pedidos**: quick personas (Vida Saudável, Comfort Food, Gourmet) e modo manual para criar pedidos simulados
- **Terminal de Raciocínio da IA**: terminal visual que mostra passo a passo como o sistema atualiza o perfil e recalcula recomendações
- **🤖 Chef Virtual**: chatbot conversacional com RAG, suporte a áudio (STT/TTS), e monitoramento completo de métricas LLM

### Status do Projeto

**Progresso:** ~100% do MVP completo + Melhorias P0/P1 + Onboarding Gamificado + Correção de CORS

- ✅ **Backend:** 100% completo (FastAPI, autenticação, CRUD, recomendações, GenAI, onboarding)
- ✅ **IA/ML:** 100% completo (embeddings, algoritmo de recomendação, vetor sintético)
- ✅ **GenAI:** 100% completo (Groq API com retry robusto)
- ✅ **Frontend:** 100% completo (React + Vite + TypeScript + Shadcn/UI, onboarding)
- ✅ **Deploy:** 100% completo (Backend no Fly.io v42, Frontend no Netlify)
- ✅ **Banco de Dados:** 100% migrado para Supabase (PostgreSQL + pgvector)
- ✅ **CORS:** 100% corrigido (URL da API detecta ambiente automaticamente)
- ✅ **Mobile-First:** 100% completo (design responsivo, menu hambúrguer, viewports dinâmicos)
- ✅ **Testes E2E:** 100% completo (Playwright, 50 testes, 0 falhas)
- ✅ **Chef Virtual:** 95% completo (RAG, STT/TTS, monitoramento LLM, testes E2E)

### Tecnologias Principais

**Backend:**
- FastAPI 0.104+ (Python 3.11+)
- SQLAlchemy 2.0+ com Alembic (migrations)
- SQLite (desenvolvimento) / **Supabase PostgreSQL** com pgvector (produção)
- JWT para autenticação
- Bcrypt para hash de senhas
- LangChain 0.3+ (RAG, LLM integration)
- Groq API (LLM, Whisper STT)
- Edge-TTS (text-to-speech)

**IA/ML:**
- sentence-transformers (all-MiniLM-L6-v2)
- scikit-learn (similaridade coseno)
- pandas, numpy

**GenAI:**
- Groq API (Llama 3.3 70B Versatile, Llama 3.1 8B Instant para Chef Virtual)
- Retry com backoff exponencial
- Cache de insights (TTL 7 dias)
- RAG com PGVector (Chef Virtual)
- Hybrid Search (busca exata + semântica)

**Frontend:**
- React 18+ com TypeScript
- Vite (build tool)
- Shadcn/UI (componentes)
- Tailwind CSS v3
- React Router
- Axios (cliente HTTP)

---

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.11+
- Node.js 18+ e npm
- Git

### Instalação e Configuração

#### 1. Clone o Repositório

```bash
git clone https://github.com/brunoadsba/TasteMatch.git
cd tastematch
```

#### 2. Configure o Backend

```bash
# Crie e ative ambiente virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt
```

**Nota:** A instalação do `sentence-transformers` pode demorar alguns minutos, pois baixa o modelo de embeddings.

#### 3. Configure Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite .env e configure (obrigatório: GROQ_API_KEY)
nano .env  # ou use seu editor preferido
```

**Variáveis obrigatórias:**
- `GROQ_API_KEY` - Obtenha em https://console.groq.com (gratuito)
- `JWT_SECRET_KEY` - Gere uma chave aleatória
- `SECRET_KEY` - Gere uma chave aleatória

#### 4. Inicialize o Banco de Dados

```bash
cd backend

# Aplicar migrations
alembic upgrade head

# Popular com dados de exemplo (inclui geração de embeddings)
python scripts/seed_data.py
```

**Dados criados:**
- 25 restaurantes (diferentes culinárias)
- 5 usuários de exemplo
- 67 pedidos de exemplo
- Embeddings gerados automaticamente

#### 5. Inicie o Backend

```bash
# No diretório backend/
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

A API estará disponível em: `http://localhost:8000`
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

#### 6. Configure e Inicie o Frontend

```bash
# Em outro terminal, no diretório frontend/
cd frontend

# Instale dependências
npm install

# Inicie servidor de desenvolvimento
npm run dev
```

O frontend estará disponível em: `http://localhost:5173` (ou outra porta se 5173 estiver em uso)

---

## 🔑 Credenciais de Teste

Após executar o seed, você pode usar estas credenciais:

| Email | Senha | Nome |
|-------|-------|------|
| joao@example.com | 123456 | João Silva |
| maria@example.com | 123456 | Maria Santos |
| pedro@example.com | 123456 | Pedro Oliveira |
| ana@example.com | 123456 | Ana Costa |
| carlos@example.com | 123456 | Carlos Souza |

---

## 📚 Documentação

### Documentação

**📚 [Ver Documentação Completa](./Docs/README.md)**

#### Documentos Principais

- **[SPEC.md](./Docs/SPEC.md)** - Especificação técnica completa
- **[DEPLOY.md](./Docs/DEPLOY.md)** - Guia completo de deploy
- **[STATUS_PROJETO.md](./Docs/STATUS_PROJETO.md)** - Status atual do projeto
- **[README-CHEF-VIRTUAL.md](./Docs/README-CHEF-VIRTUAL.md)** - 📖 Documentação completa do Chef Virtual (RAG, STT/TTS, monitoramento)
- **[STATUS-CHEF-VIRTUAL.md](./Docs/STATUS-CHEF-VIRTUAL.md)** - Status detalhado e lições aprendidas do Chef Virtual
- **[licoes-aprendidas.md](./Docs/licoes-aprendidas.md)** - Lições aprendidas durante o desenvolvimento
- **[plano-de-acao.md](./Docs/plano-de-acao.md)** - Plano de desenvolvimento detalhado
- **[supabase.md](./Docs/supabase.md)** - Plano de migração para Supabase
- **[status-migracao-supabase.md](./Docs/status-migracao-supabase.md)** - Status da migração Supabase

### Endpoints Principais da API

**Autenticação:**
- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Autenticar usuário

**Recomendações:**
- `GET /api/recommendations?limit=10&refresh=false` - Obter recomendações personalizadas
- `GET /api/recommendations/{restaurant_id}/insight` - Obter insight específico

**Restaurantes:**
- `GET /api/restaurants` - Listar restaurantes (com paginação e filtros)
- `GET /api/restaurants/{id}` - Detalhes de um restaurante

**Pedidos:**
- `GET /api/orders` - Histórico de pedidos do usuário
- `POST /api/orders` - Criar novo pedido

**Usuário:**
- `GET /api/users/me` - Informações do usuário autenticado
- `GET /api/users/me/preferences` - Preferências agregadas

**Onboarding:**
- `POST /api/onboarding/complete` - Completar onboarding e gerar perfil de sabor (vetor sintético)

**Monitoramento:**
- `GET /health` - Health check da aplicação

Consulte a documentação Swagger (`/docs`) para detalhes completos de todos os endpoints.

---

## 🏗️ Estrutura do Projeto

```
tastematch/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/          # Endpoints da API
│   │   │   └── deps.py          # Dependências (auth, db)
│   │   ├── core/
│   │   │   ├── embeddings.py    # Geração de embeddings
│   │   │   ├── recommender.py   # Lógica de recomendação
│   │   │   ├── llm_service.py   # Integração Groq API
│   │   │   └── security.py      # JWT e hash de senhas
│   │   ├── database/
│   │   │   ├── models.py        # Modelos SQLAlchemy
│   │   │   ├── crud.py          # Operações CRUD
│   │   │   └── base.py          # Configuração SQLAlchemy
│   │   ├── models/              # Schemas Pydantic
│   │   ├── config.py            # Configurações
│   │   └── main.py              # Entry point FastAPI
│   ├── alembic/                 # Migrations
│   ├── scripts/
│   │   ├── init_db.py           # Inicializar banco
│   │   ├── seed_data.py         # Popular dados (com embeddings)
│   │   └── test_*.py            # Scripts de teste manual
│   └── docs/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # Componentes Shadcn/UI
│   │   │   └── features/        # Componentes de negócio
│   │   ├── hooks/               # Custom hooks React
│   │   ├── lib/                 # Cliente API e utils
│   │   ├── pages/               # Telas (Login, Dashboard)
│   │   ├── types/               # Interfaces TypeScript
│   │   └── App.tsx              # Componente principal
│   └── package.json
├── data/                        # Dados de exemplo
├── Docs/                        # Documentação adicional (especificações, deploy, análises)
├── .env.example                 # Template de variáveis
├── requirements.txt             # Dependências Python
├── Docs/SPEC.md                 # Especificação técnica
├── Docs/plano-de-acao.md        # Plano de desenvolvimento
├── Docs/STATUS_PROJETO.md       # Status atual
└── README.md                    # Este arquivo
```

---

## 🎯 Funcionalidades Implementadas

### ✅ Backend Completo

- **Autenticação JWT:** Registro, login, proteção de rotas
- **CRUD Completo:** Usuários, restaurantes, pedidos
- **Sistema de Recomendações:**
  - Embeddings semânticos (sentence-transformers)
  - Cálculo de similaridade coseno
  - Algoritmo personalizado com pesos (recência, rating)
  - Cold start (fallback para restaurantes populares)
  - Cache de preferências do usuário
- **GenAI Integration:**
  - Geração de insights contextualizados (Groq API)
  - Retry com backoff exponencial
  - Cache de insights (TTL 7 dias)
  - Fallback para erros da API
- **Validação:** Pydantic para validação de dados
- **Documentação:** Swagger UI automático

### ✅ Frontend Funcional

- **Autenticação:** Login e registro funcionando
- **Dashboard:** Visualização de recomendações
- **Cards de Restaurantes:** Exibição de detalhes e insights
- **Proteção de Rotas:** Redirecionamento automático se não autenticado
- **Integração Completa:** Cliente API com interceptors JWT
- **UI Moderna:** Shadcn/UI + Tailwind CSS

### ⏳ Pendente (Melhorias)

- Melhorias de UX (toasts, loading states mais visuais)
- Testes automatizados (pytest)
- Histórico de pedidos no frontend (feature adicional)

---

## 🔧 Configuração Detalhada

### Variáveis de Ambiente

Veja `.env.example` para todas as variáveis. Principais:

```env
# Aplicação
APP_NAME=TasteMatch
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=sua-chave-secreta-aqui

# Banco de Dados
DATABASE_URL=sqlite:///./tastematch.db

# JWT
JWT_SECRET_KEY=sua-chave-jwt-aqui
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Groq API (OBRIGATÓRIA para insights)
GROQ_API_KEY=sua-groq-api-key-aqui

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Obter API Key do Groq

A Groq API é **gratuita** e pode ser configurada em minutos:

1. Acesse: https://console.groq.com
2. Crie uma conta (gratuito, sem cartão de crédito)
3. Gere uma API key na dashboard
4. Copie a chave e adicione no arquivo `.env` como `GROQ_API_KEY=sua-chave-aqui`

**Modelo usado:** `llama-3.3-70b-versatile` (atualizado de llama-3.1 devido a depreciação)

---

## 🧪 Testes

### Testes Manuais (Implementados)

```bash
cd backend

# Testar endpoints de autenticação
python scripts/test_auth_endpoints.py

# Testar endpoints de recomendações
python scripts/test_recommendations_endpoints.py
```

### Testes Automatizados (Pendente)

```bash
cd backend
pytest tests/  # Quando implementado
```

---

## 🐛 Troubleshooting

### Problema: ImportError com sentence-transformers

**Solução:** Verifique se as versões no `requirements.txt` estão corretas. Versões testadas:
- `sentence-transformers==2.3.1`
- `torch==2.1.2`
- `transformers==4.35.2`

### Problema: Erro de CORS no frontend

**Solução:** Verifique se o backend está configurado para aceitar requisições do frontend. O CORS está configurado para:
- `http://localhost:5173`
- `http://localhost:5174`
- `http://127.0.0.1:5174`

### Problema: Token JWT inválido

**Solução:** Verifique se o `JWT_SECRET_KEY` está configurado corretamente no `.env`. Se mudar, será necessário fazer login novamente.

### Problema: Erro ao gerar insights (Groq API)

**Solução:** 
- Verifique se `GROQ_API_KEY` está configurada corretamente
- Verifique sua quota na Groq (gratuita, mas tem limites)
- O sistema tem retry automático e fallback genérico

---

## 📦 Deploy em Produção ✅

### 🌐 Acessar Aplicação

**Frontend:** https://tastematch.netlify.app  
**Backend API:** https://tastematch-api.fly.dev  
**Documentação API:** https://tastematch-api.fly.dev/docs

### Plataformas Utilizadas

- **Backend:** Fly.io (São Paulo, Brasil) - v42
- **Frontend:** Netlify
- **Banco de Dados:** Supabase PostgreSQL (São Paulo, Brasil) com pgvector

### Status do Deploy

✅ **Deploy completo e funcionando!**

- ✅ Backend deployado e validado
- ✅ Frontend deployado e validado
- ✅ Integração end-to-end funcionando
- ✅ Autenticação funcionando
- ✅ CORS configurado
- ✅ Variáveis de ambiente configuradas

**Para detalhes completos do deploy, consulte:**
- [DEPLOY.md](./Docs/DEPLOY.md) - Guia completo de deploy
- [Docs/README.md](./Docs/README.md) - Índice completo da documentação

### Como Fazer Deploy (Para Referência)

**Backend (Fly.io):**
```bash
cd backend
fly launch
fly secrets set GROQ_API_KEY=your-key
fly secrets set DATABASE_URL=postgresql://...
fly deploy
```

**Frontend (Netlify):**
```bash
cd frontend
npm run build
netlify deploy --prod
```

---

## 🎓 Contexto do Projeto

Este projeto foi desenvolvido como parte da preparação para o **Programa de Estágio GenAI 2026 do iFood**, demonstrando:

- ✅ Conhecimento em **agentes de IA**
- ✅ Aplicação de **GenAI** para insights contextualizados
- ✅ Uso de **embeddings e vetores semânticos** com busca otimizada
- ✅ Integração de IA em sistemas reais com arquitetura escalável
- ✅ Foco em **impacto de negócio** e boas práticas de engenharia
- ✅ Stack moderna (FastAPI, React, TypeScript)

---

## 📊 Estatísticas do Projeto

- **Arquivos Python:** ~30 arquivos
- **Arquivos TypeScript/React:** ~18 arquivos
- **Endpoints API:** 11 endpoints
- **Modelos de Dados:** 5 modelos principais
- **Linhas de Código:** ~1.860+ linhas
- **Tempo de Desenvolvimento:** ~40-50 horas

---

## 🤝 Contribuindo

Este é um projeto de demonstração técnica. Para desenvolvimento:

1. Consulte [SPEC.md](./SPEC.md) como referência técnica
2. Siga a estrutura de pastas definida
3. Use Conventional Commits
4. Mantenha código limpo e documentado

---

## 📝 Notas de Versão

**v1.0.0 (Atual)** - MVP Funcional:
- ✅ Backend completo com FastAPI
- ✅ Sistema de recomendações com embeddings
- ✅ Integração GenAI (Groq API)
- ✅ Frontend React + TypeScript + Shadcn/UI
- ✅ Autenticação JWT completa
- ✅ Cache de embeddings e insights
- ✅ Retry robusto para API externa
- ✅ Documentação completa (SPEC.md, README-CHEF-VIRTUAL.md)
- ✅ Chef Virtual com RAG, STT/TTS e monitoramento LLM

**Próximas versões planejadas:**
- Melhorias de UX no frontend
- Testes automatizados
- Popular banco com dados reais
- Features adicionais (histórico completo, favoritos)
- Dashboard de métricas LLM (Chef Virtual)
- Cache de respostas frequentes (Chef Virtual)

---

## 📄 Licença

Projeto de demonstração técnica - Uso educacional.

---

## 🔗 Links Úteis

- **Documentação FastAPI:** https://fastapi.tiangolo.com
- **Shadcn/UI:** https://ui.shadcn.com
- **Groq API:** https://console.groq.com
- **sentence-transformers:** https://www.sbert.net

---

**Desenvolvido com ❤️ para demonstrar capacidade técnica em IA e desenvolvimento de sistemas.**

**Última atualização:** 29/11/2025  
**Status:** ✅ MVP Funcional - **DEPLOYADO EM PRODUÇÃO** - **Migração Supabase Concluída**

🌐 **Acesse agora:** https://tastematch.netlify.app

### 🎉 Migração para Supabase Concluída (29/11/2025)

- ✅ Banco de dados migrado para Supabase PostgreSQL
- ✅ Extensão pgvector habilitada
- ✅ 24 restaurantes com embeddings regenerados
- ✅ Base RAG migrada (64 documentos)
- ✅ Configurações otimizadas para Supabase (connection pooling)
- ✅ API v42 em produção funcionando

**Documentação da migração:**
- [status-migracao-supabase.md](./Docs/status-migracao-supabase.md) - Status completo da migração
- [supabase.md](./Docs/supabase.md) - Plano e guia de migração
