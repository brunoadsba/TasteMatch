# TasteMatch

> **Agente de Recomendação Inteligente para Delivery**  
> Sistema de recomendações personalizadas utilizando IA generativa e machine learning

[![Status](https://img.shields.io/badge/status-MVP%20Funcional-success)]()
[![Backend](https://img.shields.io/badge/backend-FastAPI-blue)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb)]()
[![IA](https://img.shields.io/badge/IA-Groq%20LLM-orange)]()

---

## Sobre o Projeto

O **TasteMatch** é um sistema de recomendação inteligente que utiliza embeddings semânticos, similaridade vetorial e IA generativa para fornecer recomendações personalizadas de restaurantes, explicando o raciocínio por trás de cada sugestão.

### Principais Funcionalidades

- **Sistema de Recomendações**: Embeddings semânticos com algoritmo de similaridade coseno
- **Onboarding Gamificado**: Criação de perfil de sabor em 3 etapas com geração de vetor sintético
- **Chef Virtual**: Chatbot conversacional com RAG (Retrieval-Augmented Generation), suporte a áudio (STT/TTS) e filtro semântico rigoroso
- **GenAI Integration**: Insights contextualizados usando Groq API com retry robusto e cache
- **Autenticação JWT**: Sistema completo de autenticação e autorização
- **Interface Moderna**: React + TypeScript + Shadcn/UI com design mobile-first responsivo

### Status Atual

O projeto está **rodando localmente** para desenvolvimento e testes.

- Backend: FastAPI (Python 3.11+)
- Frontend: React + Vite + TypeScript
- Banco de Dados: PostgreSQL com pgvector (via Docker)
- IA/ML: sentence-transformers, scikit-learn
- GenAI: Groq API (Llama 3.3 70B, Llama 3.1 8B Instant)

---

## Tecnologias

### Backend
- FastAPI 0.104+ (Python 3.11+)
- SQLAlchemy 2.0+ com Alembic
- PostgreSQL com pgvector
- LangChain 0.3.27 (RAG, LLM integration)
- Groq API SDK 0.36.0 (LLM, Whisper STT)
- Edge-TTS (text-to-speech)
- JWT + Bcrypt para autenticação

### IA/ML
- sentence-transformers (all-MiniLM-L6-v2)
- scikit-learn (similaridade coseno)
- pandas, numpy

### Frontend
- React 18+ com TypeScript
- Vite
- Shadcn/UI + Tailwind CSS v3
- React Router
- Axios

---

## Início Rápido

### Pré-requisitos

- Python 3.11+
- Node.js 18+ e npm
- Docker (para banco de dados local)
- Git

### Instalação

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

#### 3. Configure Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite .env e configure (obrigatório: GROQ_API_KEY)
nano .env
```

**Variáveis obrigatórias:**
- `GROQ_API_KEY` - Obtenha em https://console.groq.com
- `JWT_SECRET_KEY` - Gere uma chave aleatória
- `SECRET_KEY` - Gere uma chave aleatória
- `DATABASE_URL` - PostgreSQL local: `postgresql://tastematch:tastematch_dev@localhost:5432/tastematch`

#### 4. Inicialize o Banco de Dados

```bash
# Iniciar PostgreSQL via Docker
docker-compose up -d postgres

# Aplicar migrations
cd backend
alembic upgrade head

# Popular com dados de exemplo
python scripts/seed_data.py
```

#### 5. Inicie os Serviços

**Backend:**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

A aplicação estará disponível em:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs

### Credenciais de Teste

Após executar o seed:

| Email | Senha |
|-------|-------|
| joao@example.com | 123456 |
| maria@example.com | 123456 |

---

## Estrutura do Projeto

```
tastematch/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # Endpoints da API
│   │   ├── core/            # Lógica de negócio (embeddings, recommender, LLM)
│   │   ├── database/        # Modelos SQLAlchemy e CRUD
│   │   └── models/          # Schemas Pydantic
│   ├── alembic/             # Migrations
│   └── scripts/             # Scripts de seed e testes
├── frontend/
│   └── src/
│       ├── components/      # Componentes React
│       ├── pages/           # Telas (Login, Dashboard, etc)
│       ├── hooks/           # Custom hooks
│       └── lib/             # Cliente API e utils
└── Docs/                    # Documentação técnica
```

---

## API Endpoints

### Autenticação
- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Autenticar usuário

### Recomendações
- `GET /api/recommendations` - Obter recomendações personalizadas
- `GET /api/recommendations/{restaurant_id}/insight` - Obter insight específico

### Restaurantes
- `GET /api/restaurants` - Listar restaurantes (com paginação e filtros)
- `GET /api/restaurants/{id}` - Detalhes de um restaurante

### Pedidos
- `GET /api/orders` - Histórico de pedidos do usuário
- `POST /api/orders` - Criar novo pedido

### Usuário
- `GET /api/users/me` - Informações do usuário autenticado
- `GET /api/users/me/preferences` - Preferências agregadas

### Onboarding
- `POST /api/onboarding/complete` - Completar onboarding e gerar perfil de sabor

### Chef Virtual
- `POST /api/chat/` - Enviar mensagem ao Chef Virtual (texto ou áudio)
- `GET /api/chat/history` - Obter histórico de conversas
- `GET /api/chat/audio/{filename}` - Obter arquivo de áudio gerado

### Monitoramento
- `GET /health` - Health check
- `GET /api/metrics/llm/summary` - Resumo de métricas LLM

Consulte a documentação Swagger (`/docs`) para detalhes completos.

---

## Documentação

- **[STATUS_PROJETO.md](./Docs/STATUS_PROJETO.md)** - Status atual e histórico de desenvolvimento
- **[README-CHEF-VIRTUAL.md](./Docs/README-CHEF-VIRTUAL.md)** - Documentação completa do Chef Virtual
- **[SPEC.md](./Docs/SPEC.md)** - Especificação técnica
- **[DEPLOY.md](./Docs/DEPLOY.md)** - Guia de deploy
- **[SETUP_LOCAL.md](./Docs/SETUP_LOCAL.md)** - Guia detalhado de setup local

---

## Arquitetura

### Sistema de Recomendações

1. **Embeddings**: Geração de vetores semânticos para restaurantes usando sentence-transformers
2. **Perfil do Usuário**: Vetor sintético baseado em preferências e histórico de pedidos
3. **Similaridade**: Cálculo de similaridade coseno entre perfil do usuário e restaurantes
4. **Algoritmo**: Pesos para recência, rating e similaridade semântica
5. **Cold Start**: Fallback para restaurantes populares para novos usuários

### Chef Virtual (RAG)

1. **Busca Semântica**: PGVector para busca vetorial de restaurantes
2. **Hybrid Search**: Combinação de busca exata e semântica
3. **LLM**: Groq API (Llama 3.1 8B Instant) para geração de respostas
4. **Filtro Semântico**: Validação rigorosa para prevenir recomendações incorretas
5. **STT/TTS**: Suporte a áudio via Groq Whisper e Edge-TTS

---

## Troubleshooting

### Erro de CORS
Verifique se o backend está configurado para aceitar requisições do frontend. CORS configurado para `http://localhost:5173` e `http://localhost:5174`.

### Erro ao gerar insights (Groq API)
- Verifique se `GROQ_API_KEY` está configurada corretamente
- Verifique sua quota na Groq (gratuita, mas tem limites)
- O sistema tem retry automático e fallback genérico

### Problema com sentence-transformers
Verifique se as versões no `requirements.txt` estão corretas:
- `sentence-transformers==2.3.1`
- `torch==2.1.2`
- `transformers==4.35.2`

---

## Estatísticas do Projeto

- **Arquivos Python:** 44 arquivos
- **Arquivos TypeScript/React:** 47 arquivos
- **Endpoints API:** 15 endpoints
- **Modelos de Dados:** 5 modelos principais

---

## Changelog

### v1.0.3 (30/11/2025)
- Suporte a queries específicas (sopa, açaí, etc.) com tratamento adequado
- Remoção de seção "Próximos Passos" das respostas do Chef Virtual
- Mensagens claras quando não encontra restaurantes relevantes

### v1.0.2 (29/11/2025)
- Filtro semântico rigoroso para recomendações precisas
- Detecção de interações sociais (saudações, perguntas sobre identidade)
- Formatação de respostas melhorada
- Histórico de conversa inteligente

### v1.0.1 (29/11/2025)
- Correção de erro 500 no endpoint `/api/chat/`
- Atualização Groq SDK para 0.36.0 (suporte a API de áudio)
- Correções de processamento de áudio

### v1.0.0
- MVP funcional completo
- Sistema de recomendações com embeddings
- Integração GenAI (Groq API)
- Chef Virtual com RAG, STT/TTS e monitoramento LLM

---

## Licença

Projeto de demonstração técnica - Uso educacional.

---

## Links Úteis

- [Documentação FastAPI](https://fastapi.tiangolo.com)
- [Shadcn/UI](https://ui.shadcn.com)
- [Groq API](https://console.groq.com)
- [sentence-transformers](https://www.sbert.net)

---

**Última atualização:** 30/11/2025  
**Status:** MVP Funcional - Rodando Localmente
