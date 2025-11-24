# TasteMatch 🍽️

> **Agente de Recomendação Inteligente para Delivery**

Sistema de recomendações personalizadas que utiliza IA generativa e machine learning para sugerir restaurantes baseado no histórico de pedidos dos usuários.

---

## 📋 Sobre o Projeto

O **TasteMatch** é um agente de recomendação inteligente que:

- 🎯 Analisa padrões de comportamento do usuário através de embeddings semânticos
- 🤖 Gera recomendações personalizadas usando similaridade vetorial
- 💡 Cria insights contextualizados com IA generativa explicando **por quê** cada restaurante foi recomendado
- ⚡ Processa recomendações em tempo real com cache inteligente

### Tecnologias Principais

- **Backend:** FastAPI, Python 3.11+
- **IA/ML:** sentence-transformers, pandas, scikit-learn, pgvector
- **LLM:** Groq API (Llama 3.1) para geração de insights
- **Banco de Dados:** SQLite (dev) / PostgreSQL com pgvector (prod)
- **Frontend:** HTML/CSS/JavaScript (Vanilla)
- **Infraestrutura:** Docker Compose para desenvolvimento local

---

## 🚀 Início Rápido

### Pré-requisitos

- **Opção A (Docker):** Docker e Docker Compose instalados
- **Opção B (Manual):** Python 3.11+, pip ou poetry, Git

### Instalação

#### Opção A: Usando Docker Compose (Recomendado)

A forma mais simples e reprodutível:

1. **Clone o repositório:**
```bash
git clone <repo-url>
cd tastematch
```

2. **Configure variáveis de ambiente:**
```bash
cp .env.example .env
# Edite .env e adicione sua GROQ_API_KEY
```

3. **Inicie os serviços:**
```bash
docker-compose up -d
```

Pronto! A API estará disponível em `http://localhost:8000`

- **Documentação Swagger:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

#### Opção B: Instalação Manual

1. **Clone o repositório:**
```bash
git clone <repo-url>
cd tastematch
```

2. **Crie e ative ambiente virtual:**
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale dependências:**
```bash
pip install -r requirements.txt
```

**Nota sobre dependências ML:**
- `sentence-transformers` requer PyTorch, que será instalado automaticamente
- Em sistemas Linux/Mac, geralmente funciona sem configuração adicional
- Se encontrar problemas, consulte: https://pytorch.org/get-started/locally/

4. **Configure variáveis de ambiente:**
```bash
cp .env.example .env
# Edite .env e preencha as variáveis necessárias (especialmente GROQ_API_KEY)
```

5. **Inicialize o banco de dados:**
```bash
cd backend
python scripts/init_db.py
python scripts/seed_data.py
python scripts/generate_embeddings.py
```

6. **Execute a aplicação:**
```bash
uvicorn app.main:app --reload --port 8000
```

A API estará disponível em: `http://localhost:8000`

- **Documentação Swagger:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 📚 Documentação

### Documentação Completa

Consulte **[SPEC.md](./SPEC.md)** para a especificação técnica completa do projeto, incluindo:

- Arquitetura detalhada
- Modelos de dados
- Especificação completa de endpoints
- Lógica de recomendação
- Geração de insights com GenAI
- Guia de desenvolvimento
- Estrutura de pastas

### Endpoints Principais

- `POST /auth/register` - Registrar novo usuário
- `POST /auth/login` - Autenticar usuário
- `GET /api/recommendations` - Obter recomendações personalizadas
- `GET /api/restaurants` - Listar restaurantes
- `GET /api/orders` - Histórico de pedidos
- `GET /health` - Health check da aplicação

Consulte a documentação Swagger (`/docs`) para detalhes completos de todos os endpoints.

---

## 🏗️ Estrutura do Projeto

```
tastematch/
├── backend/          # API FastAPI
├── frontend/         # Interface do usuário
├── data/            # Dados de exemplo
├── docs/            # Documentação adicional
├── docker-compose.yml # Orquestração de serviços
├── SPEC.md          # Especificação técnica completa
└── README.md        # Este arquivo
```

---

## 🎯 Funcionalidades

### Recomendações Personalizadas

O sistema analisa o histórico de pedidos do usuário e gera recomendações baseadas em:

- Similaridade semântica (embeddings)
- Padrões de preferência (culinárias favoritas)
- Avaliações e ratings
- Recência dos pedidos

### Insights com IA

Cada recomendação inclui um insight gerado por LLM explicando:

- Por que o restaurante foi recomendado
- Conexões com o histórico do usuário
- Características relevantes

### Performance

- Cache de embeddings e recomendações
- Busca vetorial otimizada com pgvector (PostgreSQL)
- Processamento assíncrono
- Respostas em < 1 segundo

### Escalabilidade

- Busca vetorial nativa no banco de dados (pgvector)
- Suporta milhares de restaurantes sem degradação de performance
- Arquitetura preparada para produção

---

## 🐳 Executando com Docker

Docker Compose é a forma mais recomendada para executar o projeto localmente:

### Comandos Úteis

```bash
# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Parar serviços
docker-compose down

# Reconstruir containers
docker-compose up -d --build

# Executar comandos no container
docker-compose exec api python scripts/init_db.py
```

### O que o Docker Compose inclui:

- **PostgreSQL** com extensão pgvector para busca vetorial otimizada
- **FastAPI Backend** com hot-reload
- Configuração automática de variáveis de ambiente
- Volumes persistentes para banco de dados

---

## 🔧 Configuração

### Variáveis de Ambiente

Veja `.env.example` para todas as variáveis necessárias. Principais:

- `GROQ_API_KEY` - **Obrigatória** para geração de insights (gratuita, consulte seção abaixo)
- `DATABASE_URL` - URL do banco de dados (configurada automaticamente com Docker)
- `JWT_SECRET_KEY` - Chave para autenticação JWT
- `SECRET_KEY` - Chave secreta da aplicação

### Obter API Key do Groq

A Groq API é **gratuita** e pode ser configurada em minutos:

1. Acesse: https://console.groq.com
2. Crie uma conta (gratuito, sem necessidade de cartão de crédito)
3. Gere uma API key na dashboard
4. Copie a chave e adicione no arquivo `.env` como `GROQ_API_KEY=sua-chave-aqui`

**Modelos disponíveis:**
- `llama-3.1-70b-versatile` (melhor qualidade, recomendado)
- `llama-3.1-8b-instant` (mais rápido, menor custo)

---

## 🧪 Testes

```bash
cd backend
pytest tests/
```

Para executar testes com Docker:
```bash
docker-compose exec api pytest tests/
```

---

## 📦 Deploy

### Backend (Fly.io)

```bash
cd backend
fly launch
fly secrets set GROQ_API_KEY=your-key
fly secrets set DATABASE_URL=postgresql://...
fly deploy
```

**Nota:** Configure CORS no FastAPI para permitir requisições do frontend. Veja `SPEC.md` seção 12.3.

### Frontend (Netlify)

```bash
cd frontend
netlify deploy
```

**Importante:** Configure as variáveis de ambiente do backend no Netlify (se necessário para proxy).

---

## 🤝 Contribuindo

Este é um projeto de demonstração técnica. Para desenvolvimento:

1. Consulte [SPEC.md](./SPEC.md) como referência técnica
2. Siga a estrutura de pastas definida
3. Use Conventional Commits
4. Mantenha código limpo e documentado

---

## 📄 Licença

Projeto de demonstração técnica - Uso educacional.

---

## 🎓 Contexto

Este projeto foi desenvolvido como parte da preparação para o **Programa de Estágio GenAI 2026 do iFood**, demonstrando:

- Conhecimento em agentes de IA
- Aplicação de GenAI para insights contextualizados
- Uso de embeddings e vetores semânticos com busca otimizada (pgvector)
- Integração de IA em sistemas reais com arquitetura escalável
- Foco em impacto de negócio e boas práticas de engenharia
- DevOps básico (Docker, CI/CD ready)

---

**Desenvolvido com ❤️ para demonstrar capacidade técnica em IA e desenvolvimento de sistemas.**

---

## 📝 Notas de Versão

**v1.1.0** - Melhorias implementadas:
- ✅ Suporte a pgvector para busca vetorial otimizada
- ✅ Docker Compose para desenvolvimento local
- ✅ Segurança aprimorada (bcrypt explícito)
- ✅ Documentação completa de padrões e configurações
- ✅ Endpoint /health para monitoramento
- ✅ Melhorias de escalabilidade e performance

Para detalhes técnicos completos, consulte [SPEC.md](./SPEC.md).

