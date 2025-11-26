# TasteMatch - Especificação Técnica Completa

> **Agente de Recomendação Inteligente para Delivery**  
> Documentação para desenvolvimento colaborativo (Desenvolvedor + IA)  
> Versão: 1.2.0 | Última atualização: 2025-11-26

---

## 📋 Índice

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Stack Tecnológica](#3-stack-tecnológica)
4. [Modelos de Dados](#4-modelos-de-dados)
5. [Endpoints da API](#5-endpoints-da-api)
6. [Lógica de Recomendação](#6-lógica-de-recomendação)
7. [Geração de Insights com GenAI](#7-geração-de-insights-com-genai)
8. [Estrutura de Pastas do Projeto](#8-estrutura-de-pastas-do-projeto)
9. [Instalação e Configuração](#9-instalação-e-configuração)
10. [Guia de Desenvolvimento](#10-guia-de-desenvolvimento)
11. [Testes e Validação](#11-testes-e-validação)
12. [Deploy e Produção](#12-deploy-e-produção)
13. [Roadmap e Melhorias Futuras](#13-roadmap-e-melhorias-futuras)

---

## 1. Visão Geral do Projeto

### 1.1 Propósito

O **TasteMatch** é um agente de recomendação inteligente que utiliza IA generativa e machine learning para fornecer recomendações personalizadas de restaurantes e pratos baseadas no histórico de pedidos dos usuários.

### 1.2 Contexto de Negócio

**Problema que resolve:**
- Usuários ficam sobrecarregados com muitas opções de restaurantes
- Restaurantes novos ou com pouca visibilidade não são descobertos
- Recomendações genéricas não atendem preferências individuais
- Falta de contexto personalizado nas sugestões

**Solução:**
- Sistema de recomendação baseado em embeddings semânticos
- Análise de padrões de comportamento do usuário
- Recomendações contextualizadas com insights em linguagem natural
- Personalização em tempo real baseada em histórico

### 1.3 Público-Alvo

- **Primário:** Usuários de plataformas de delivery que fazem pedidos regularmente
- **Secundário:** Restaurantes parceiros que buscam maior visibilidade

### 1.4 Casos de Uso Principais

1. **Recomendação Personalizada**
   - Usuário acessa a plataforma → Sistema analisa histórico → Gera recomendações personalizadas

2. **Insights Contextualizados**
   - Usuário visualiza restaurante → Sistema gera insight explicando por que foi recomendado

3. **Descoberta de Novos Restaurantes**
   - Sistema identifica restaurantes similares aos favoritos do usuário
   - Sugere opções com base em padrões de preferência

### 1.5 Alinhamento com Vaga GenAI iFood

- Demonstra conhecimento em **agentes de IA** (core da vaga)
- Aplica **GenAI** para geração de insights contextualizados
- Utiliza **embeddings e vetores semânticos** (mencionado na entrevista)
- Foca em **impacto de negócio** (aumento de conversão de pedidos)
- Implementa **recomendações personalizadas** (tema da entrevista)
- Mostra capacidade de **integrar IA em sistemas reais**

---

## 2. Arquitetura do Sistema

### 2.1 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  (HTML/CSS/JS ou React Minimal)                             │
│  - Dashboard de recomendações                               │
│  - Visualização de insights                                 │
│  - Histórico de recomendações                               │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────▼────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Users      │  │ Recommender  │  │   Insights   │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Embeddings  │  │    LLM       │  │   Database   │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌─────────▼──────────┐
│   DATABASE     │      │   EXTERNAL APIs    │
│   (SQLite/     │      │   - Groq API       │
│   PostgreSQL)  │      │   - Embeddings     │
└────────────────┘      └────────────────────┘
```

### 2.2 Fluxo de Dados Principal

#### Fluxo de Recomendação

1. **Coleta de Dados**
   - Sistema simula histórico de pedidos (dados de exemplo)
   - Armazena em banco de dados estruturado

2. **Geração de Embeddings**
   - Restaurantes e preferências do usuário são convertidos em embeddings vetoriais
   - Usa sentence-transformers para embeddings semânticos

3. **Cálculo de Similaridade**
   - Compara embeddings do usuário com restaurantes disponíveis
   - Calcula similaridade coseno entre vetores

4. **Ranking e Filtragem**
   - Ordena restaurantes por similaridade
   - Aplica filtros (disponibilidade, avaliações mínimas, etc.)
   - Retorna top N recomendações

5. **Geração de Insights**
   - LLM gera explicação contextualizada das recomendações
   - Formato em linguagem natural, explicando o "porquê"

6. **Apresentação ao Usuário**
   - Frontend exibe recomendações ordenadas
   - Mostra insights gerados para cada recomendação

### 2.3 Componentes Principais

#### Backend API (FastAPI)
- **Responsabilidade:** Orquestrar todos os serviços, expor endpoints REST
- **Tecnologia:** FastAPI, Python 3.11+
- **Principais módulos:**
  - Users Service (autenticação, gestão de usuários)
  - Recommender Service (lógica de recomendação)
  - Insights Service (integração com LLM)
  - Embeddings Service (geração e cache de embeddings)
  - Database Service (camada de acesso a dados)

#### Frontend
- **Responsabilidade:** Interface de usuário, visualização de recomendações, consumo da API REST
- **Tecnologia:** HTML5, CSS3, JavaScript (Vanilla) ou React minimal
- **Principais telas:**
  - Dashboard de recomendações
  - Detalhes de restaurante
  - Histórico de recomendações
  - Visualização de insights
- **Comunicação:** Faz requisições HTTP para o backend, exibe dados formatados ao usuário

#### Banco de Dados
- **Responsabilidade:** Persistência de dados estruturados
- **Tecnologia:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Dados armazenados:**
  - Usuários e perfis
  - Restaurantes e informações
  - Histórico de pedidos
  - Recomendações geradas
  - Embeddings cacheados

#### Serviços de IA
- **Embeddings Service:**
  - Gera embeddings de restaurantes e preferências
  - Cache de embeddings para performance
  - Modelo: sentence-transformers (all-MiniLM-L6-v2)

- **LLM Service:**
  - Gera insights contextualizados
  - Integração com Groq API (Llama 3.1) ou OpenAI
  - Prompt engineering para respostas consistentes

---

## 3. Stack Tecnológica

### 3.1 Backend

#### Core Framework
- **FastAPI 0.104+**
  - **Justificativa:** Performance excelente, documentação automática (Swagger), tipagem forte com Pydantic, suporte assíncrono nativo
  - **Uso:** API REST principal, validação de dados, geração automática de docs

#### Linguagem
- **Python 3.11+**
  - **Justificativa:** Ecossistema robusto para IA/ML, bibliotecas maduras, suporte a async/await

#### Validação e Schemas
- **Pydantic 2.0+**
  - **Justificativa:** Validação automática de dados, serialização JSON, type hints

#### Banco de Dados
- **SQLAlchemy 2.0+** (ORM)
  - **Justificativa:** Abstração de banco, migrations, queries type-safe
- **Alembic** (Migrations)
  - **Justificativa:** Gerenciamento de versões de schema, migrations versionadas
- **SQLite** (desenvolvimento)
  - **Justificativa:** Simplicidade, zero configuração, adequado para POC
- **PostgreSQL** (produção)
  - **Justificativa:** Robusto, escalável, suporte completo a JSON, suporte a pgvector para busca vetorial otimizada
- **pgvector** (Extensão PostgreSQL)
  - **Justificativa:** Busca vetorial nativa no banco, escalável para milhões de registros, melhor performance que cálculos em memória

#### IA e Machine Learning
- **sentence-transformers**
  - **Justificativa:** Embeddings de alta qualidade, modelos pré-treinados, fácil integração
  - **Modelo:** `sentence-transformers/all-MiniLM-L6-v2` (balance entre qualidade e performance)

- **pandas**
  - **Justificativa:** Manipulação de dados, análise de histórico

- **numpy**
  - **Justificativa:** Operações matemáticas, cálculos vetoriais

- **scikit-learn**
  - **Justificativa:** Similaridade coseno, normalização, utilitários ML

#### LLM Integration
- **groq** (SDK Groq API)
  - **Justificativa:** Performance alta, baixo custo, modelos Llama 3.1 de qualidade
  - **Modelos disponíveis:** `llama-3.1-8b-instant` (rápido) ou `llama-3.1-70b-versatile` (melhor qualidade)
  - **Alternativa:** `openai` (SDK OpenAI) se preferir GPT

#### Utilitários
- **python-dotenv**
  - **Justificativa:** Gerenciamento de variáveis de ambiente

- **httpx** ou **requests**
  - **Justificativa:** Clientes HTTP para APIs externas

- **uvicorn**
  - **Justificativa:** ASGI server para FastAPI

### 3.2 Frontend

#### Opção 1: Vanilla (Simples)
- **HTML5, CSS3, JavaScript (ES6+)**
  - **Justificativa:** Sem dependências, fácil de entender, rápido para POC

#### Opção 2: React Minimal
- **React 18+**
- **Vite** (build tool)
- **Justificativa:** Componentização, reatividade, melhor UX

**Escolha recomendada para POC:** Vanilla (mais simples, foca no backend/IA)

### 3.3 Deploy

- **Backend:** Fly.io ou Railway
  - **Justificativa:** Suporte a Python, fácil deploy, plano gratuito
- **Frontend:** Netlify ou Vercel
  - **Justificativa:** Deploy automático, CDN, gratuito para projetos pequenos

### 3.4 Ferramentas de Desenvolvimento

- **poetry** ou **pip + venv** (gerenciamento de dependências)
- **black** (formatação de código)
- **flake8** ou **ruff** (linting)
- **pytest** (testes)

---

## 4. Modelos de Dados

### 4.1 Schema do Banco de Dados

#### Tabela: `users`

Armazena informações dos usuários.

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos:**
- `id`: Identificador único (PK)
- `email`: Email do usuário (único, para login)
- `name`: Nome completo
- `password_hash`: Hash da senha usando **bcrypt** (algoritmo seguro com salt automático por usuário via `passlib[bcrypt]`)
- `created_at`: Data de criação
- `updated_at`: Data de última atualização

#### Tabela: `restaurants`

Armazena informações dos restaurantes.

```sql
CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    cuisine_type VARCHAR(100) NOT NULL,  -- Ex: "italiana", "japonesa", "brasileira"
    description TEXT,
    rating DECIMAL(2,1) DEFAULT 0.0,  -- 0.0 a 5.0
    price_range VARCHAR(10),  -- "low", "medium", "high"
    location VARCHAR(255),
    embedding Vector(384),  -- Embedding vetorial usando pgvector (384 dimensões do modelo all-MiniLM-L6-v2)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Campos:**
- `id`: Identificador único (PK)
- `name`: Nome do restaurante
- `cuisine_type`: Tipo de culinária
- `description`: Descrição textual
- `rating`: Avaliação média (0.0 a 5.0)
- `price_range`: Faixa de preço
- `location`: Localização/endereço
- `embedding`: Embedding vetorial usando tipo `Vector(384)` do pgvector (PostgreSQL) ou TEXT/JSON (SQLite para desenvolvimento)
- **Nota:** Em produção, usar PostgreSQL com extensão pgvector para busca vetorial otimizada
- Timestamps de auditoria

#### Tabela: `orders`

Armazena histórico de pedidos dos usuários.

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    restaurant_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    total_amount DECIMAL(10,2),
    items TEXT,  -- JSON array de itens pedidos
    rating INTEGER,  -- 1 a 5 (opcional)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);
```

**Campos:**
- `id`: Identificador único (PK)
- `user_id`: Referência ao usuário (FK)
- `restaurant_id`: Referência ao restaurante (FK)
- `order_date`: Data/hora do pedido
- `total_amount`: Valor total do pedido
- `items`: JSON com itens pedidos
- `rating`: Avaliação do pedido (opcional, 1-5)
- Timestamps

#### Tabela: `recommendations`

Armazena recomendações geradas para usuários.

```sql
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    restaurant_id INTEGER NOT NULL,
    similarity_score DECIMAL(5,4) NOT NULL,  -- 0.0 a 1.0
    insight_text TEXT,  -- Insight gerado pelo LLM
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);
```

**Campos:**
- `id`: Identificador único (PK)
- `user_id`: Usuário para quem a recomendação foi gerada (FK)
- `restaurant_id`: Restaurante recomendado (FK)
- `similarity_score`: Score de similaridade (0.0 a 1.0)
- `insight_text`: Texto do insight gerado pelo LLM
- `generated_at`: Data/hora de geração

#### Tabela: `user_preferences`

Armazena preferências agregadas dos usuários (cache de embeddings).

```sql
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    preference_embedding TEXT NOT NULL,  -- JSON array do embedding agregado
    favorite_cuisines TEXT,  -- JSON array
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

**Campos:**
- `id`: Identificador único (PK)
- `user_id`: Referência ao usuário (FK, único)
- `preference_embedding`: Embedding agregado das preferências do usuário (Vector(384) em PostgreSQL ou TEXT/JSON em SQLite)
- `favorite_cuisines`: Lista de culinárias favoritas (JSON)
- `last_updated`: Data de última atualização

### 4.2 Modelos Pydantic

#### User Model

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### Restaurant Model

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RestaurantBase(BaseModel):
    name: str
    cuisine_type: str
    description: Optional[str] = None
    rating: float = Field(ge=0.0, le=5.0, default=0.0)
    price_range: Optional[str] = None  # "low", "medium", "high"
    location: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantResponse(RestaurantBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RestaurantWithScore(RestaurantResponse):
    similarity_score: float
    insight: Optional[str] = None
```

#### Order Model

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal

class OrderBase(BaseModel):
    restaurant_id: int
    order_date: datetime
    total_amount: Optional[Decimal] = None
    items: Optional[List[Dict]] = None
    rating: Optional[int] = Field(ge=1, le=5, default=None)

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### Recommendation Model

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RecommendationResponse(BaseModel):
    restaurant: RestaurantResponse
    similarity_score: float = Field(ge=0.0, le=1.0)
    insight: Optional[str] = None
    generated_at: datetime
```

---

## 5. Endpoints da API

### 5.1 Base URL

```
Development: http://localhost:8000
Production: https://tastematch-api.fly.dev
```

### 5.2 Autenticação

Todos os endpoints (exceto `/auth/*` e `/health`) requerem autenticação via Bearer Token (JWT).

**Header:**
```
Authorization: Bearer <token>
```

**Segurança:**
- Senhas são hashadas usando **bcrypt** com salt automático por usuário
- Tokens JWT com expiração configurável (padrão: 24 horas)
- **Melhoria Futura:** Implementar refresh tokens para maior segurança

### 5.3 Endpoints de Autenticação

#### POST /auth/register

Registra novo usuário.

**Request:**
```json
{
  "email": "user@example.com",
  "name": "João Silva",
  "password": "senha123"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "João Silva",
    "created_at": "2025-01-27T10:00:00Z"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Erros:**
- `400 Bad Request`: Email já existe, validação falhou
- `422 Unprocessable Entity`: Dados inválidos

---

#### POST /auth/login

Autentica usuário existente.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "senha123"
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "João Silva"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Erros:**
- `401 Unauthorized`: Credenciais inválidas

**Segurança:**
- Senha é validada usando bcrypt antes de gerar token JWT
- Token contém informações do usuário (id, email) e expiração
- Senha nunca é retornada na resposta

---

#### GET /health

Endpoint de health check para monitoramento da aplicação.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-01-27T10:00:00Z"
}
```

**Uso:**
- Monitoramento de saúde da aplicação (Kubernetes, Fly.io, etc.)
- Verificação de disponibilidade antes de deploy
- Health checks automáticos de infraestrutura

---

### 5.4 Endpoints de Recomendações

#### GET /api/recommendations

Obtém recomendações personalizadas para o usuário autenticado.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (opcional, padrão: 10): Número de recomendações a retornar (1-50)
- `refresh` (opcional, padrão: false): Se `true`, recalcula recomendações

**Response (200 OK):**
```json
{
  "recommendations": [
    {
      "restaurant": {
        "id": 5,
        "name": "Pizzaria Bella",
        "cuisine_type": "italiana",
        "description": "Pizzas artesanais",
        "rating": 4.5,
        "price_range": "medium",
        "location": "Centro",
        "created_at": "2025-01-20T10:00:00Z"
      },
      "similarity_score": 0.87,
      "insight": "Recomendamos este restaurante porque você costuma pedir comida italiana e ele tem ótimas avaliações (4.5 estrelas). Baseado no seu histórico, você aprecia restaurantes de qualidade média e este se alinha perfeitamente com suas preferências.",
      "generated_at": "2025-01-27T10:00:00Z"
    }
  ],
  "count": 1,
  "generated_at": "2025-01-27T10:00:00Z"
}
```

**Erros:**
- `401 Unauthorized`: Token inválido ou ausente
- `404 Not Found`: Usuário não encontrado

**Lógica:**
1. Verifica se há vetor sintético do onboarding (prioridade)
2. Se não houver, verifica se há preferências cached do usuário
3. Se não houver ou `refresh=true`, calcula novo embedding do usuário baseado no histórico
4. Se usuário não tem pedidos e não tem vetor sintético, retorna restaurantes populares (cold start)
5. Calcula similaridade com todos os restaurantes
6. Ordena por similaridade
7. Gera insights com LLM para top N restaurantes
8. Retorna recomendações ordenadas

---

#### GET /api/recommendations/{restaurant_id}/insight

Gera insight específico para um restaurante recomendado.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "restaurant_id": 5,
  "insight": "Este restaurante combina perfeitamente com suas preferências porque você já pediu de restaurantes italianos similares 3 vezes no último mês. Além disso, ele está na mesma faixa de preço que você costuma escolher e tem avaliações altas (4.5 estrelas).",
  "generated_at": "2025-01-27T10:00:00Z"
}
```

**Erros:**
- `401 Unauthorized`: Token inválido
- `404 Not Found`: Restaurante não encontrado

---

#### GET /api/recommendations/chef-choice

Obtém a recomendação única do Chef para o usuário autenticado, escolhida a partir do top 3 de restaurantes recomendados.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `refresh` (opcional, padrão: false): Se `true`, força recálculo das recomendações antes da escolha do Chef

**Response (200 OK):**
```json
{
  "restaurant": {
    "id": 5,
    "name": "Pizzaria Bella",
    "cuisine_type": "italiana",
    "description": "Pizzas artesanais",
    "rating": 4.5,
    "price_range": "medium",
    "location": "Centro",
    "created_at": "2025-01-20T10:00:00Z"
  },
  "similarity_score": 0.83,
  "explanation": "Eu escolhi Pizzaria Bella especialmente para você porque você costuma pedir comida italiana bem avaliada e este restaurante tem um histórico excelente de avaliações.",
  "reasoning": [
    "Alta similaridade com suas preferências",
    "Excelente avaliação (4.5/5.0)"
  ],
  "confidence": 0.92,
  "generated_at": "2025-01-27T10:00:00Z"
}
```

**Erros:**
- `401 Unauthorized`: Token inválido ou ausente
- `404 Not Found`: Não há recomendações suficientes para o usuário

---

### 5.5 Endpoints de Restaurantes

#### GET /api/restaurants

Lista todos os restaurantes (paginação opcional).

**Query Parameters:**
- `page` (opcional, padrão: 1): Número da página
- `limit` (opcional, padrão: 20): Itens por página
- `cuisine_type` (opcional): Filtrar por tipo de culinária
- `min_rating` (opcional): Rating mínimo

**Response (200 OK):**
```json
{
  "restaurants": [
    {
      "id": 1,
      "name": "Sushi House",
      "cuisine_type": "japonesa",
      "description": "Sushi fresco",
      "rating": 4.8,
      "price_range": "high",
      "location": "Jardins"
    }
  ],
  "total": 50,
  "page": 1,
  "limit": 20
}
```

---

#### GET /api/restaurants/{restaurant_id}

Obtém detalhes de um restaurante específico.

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Sushi House",
  "cuisine_type": "japonesa",
  "description": "Sushi fresco e autêntico",
  "rating": 4.8,
  "price_range": "high",
  "location": "Jardins",
  "created_at": "2025-01-15T10:00:00Z"
}
```

**Erros:**
- `404 Not Found`: Restaurante não encontrado

---

### 5.6 Endpoints de Pedidos

#### GET /api/orders

Lista histórico de pedidos do usuário autenticado.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (opcional, padrão: 20): Número de pedidos
- `offset` (opcional, padrão: 0): Paginação

**Response (200 OK):**
```json
{
  "orders": [
    {
      "id": 1,
      "restaurant_id": 3,
      "restaurant_name": "Burger King",
      "order_date": "2025-01-26T19:30:00Z",
      "total_amount": 45.90,
      "items": [{"name": "Whopper", "quantity": 1}],
      "rating": 5,
      "created_at": "2025-01-26T19:30:00Z"
    }
  ],
  "total": 15,
  "count": 1
}
```

---

#### POST /api/orders

Cria um novo pedido (simulação).

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "restaurant_id": 3,
  "order_date": "2025-01-27T12:00:00Z",
  "total_amount": 45.90,
  "items": [
    {"name": "Whopper", "quantity": 1, "price": 25.90},
    {"name": "Batata Frita", "quantity": 1, "price": 10.00}
  ],
  "rating": 5
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "user_id": 1,
  "restaurant_id": 3,
  "order_date": "2025-01-27T12:00:00Z",
  "total_amount": 45.90,
  "items": [...],
  "rating": 5,
  "created_at": "2025-01-27T12:00:00Z"
}
```

**Erros:**
- `400 Bad Request`: Restaurante não encontrado, dados inválidos
- `401 Unauthorized`: Token inválido

---

### 5.7 Endpoints de Usuário

#### GET /api/users/me

Obtém informações do usuário autenticado.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "João Silva",
  "created_at": "2025-01-20T10:00:00Z"
}
```

---

#### GET /api/users/me/preferences

Obtém preferências agregadas do usuário.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "user_id": 1,
  "favorite_cuisines": ["italiana", "japonesa", "hamburgueria"],
  "total_orders": 15,
  "average_order_value": 42.50,
  "last_updated": "2025-01-27T10:00:00Z"
}
```

---

### 5.8 Documentação Automática

FastAPI gera documentação automática:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## 6. Lógica de Recomendação

### 6.1 Algoritmo de Recomendação

O TasteMatch utiliza **collaborative filtering baseado em embeddings semânticos** combinado com **filtragem baseada em conteúdo**.

#### Passo 1: Geração de Embeddings de Restaurantes

Cada restaurante é representado por um embedding vetorial baseado em:
- Nome do restaurante
- Tipo de culinária
- Descrição
- Localização

**Exemplo de código:**
```python
from sentence_transformers import SentenceTransformer
from pgvector.sqlalchemy import Vector
import numpy as np

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def generate_restaurant_embedding(restaurant):
    """Gera embedding vetorial para um restaurante."""
    text = f"{restaurant.name} {restaurant.cuisine_type} {restaurant.description}"
    embedding = model.encode(text, normalize_embeddings=True)
    # Retorna array numpy para uso com pgvector
    return embedding
```

**Armazenamento:**
- Em PostgreSQL: usar tipo `Vector(384)` do pgvector
- Em SQLite: serializar como JSON array no campo TEXT

#### Passo 2: Cálculo de Preferências do Usuário

O embedding do usuário é calculado como média ponderada dos embeddings dos restaurantes que ele pediu:

```python
import numpy as np

def calculate_user_preference_embedding(user_id, orders, restaurants):
    """Calcula embedding agregado das preferências do usuário."""
    restaurant_embeddings = []
    weights = []
    
    for order in orders:
        restaurant = next(r for r in restaurants if r.id == order.restaurant_id)
        if restaurant.embedding:
            embedding = json.loads(restaurant.embedding)
            # Peso baseado na frequência e recência
            weight = calculate_weight(order.order_date, order.rating)
            restaurant_embeddings.append(embedding)
            weights.append(weight)
    
    if not restaurant_embeddings:
        return None
    
    # Média ponderada
    user_embedding = np.average(restaurant_embeddings, axis=0, weights=weights)
    return user_embedding.tolist()

def calculate_weight(order_date, rating):
    """Calcula peso baseado em recência e rating."""
    days_ago = (datetime.now() - order_date).days
    recency_weight = max(0, 1 - (days_ago / 365))  # Decai ao longo do ano
    rating_weight = rating / 5.0 if rating else 0.5
    return recency_weight * rating_weight
```

#### Passo 3: Cálculo de Similaridade

Usa **similaridade coseno** entre o embedding do usuário e dos restaurantes.

**Abordagem Recomendada (Produção com PostgreSQL + pgvector):**

Delegar cálculo ao banco de dados para melhor performance e escalabilidade:

```python
from sqlalchemy import select
from app.database.models import Restaurant
from pgvector.sqlalchemy import Vector
import numpy as np

def get_similar_restaurants(db, user_embedding_vector, limit=10, min_rating=3.0):
    """
    Busca restaurantes similares diretamente no banco usando pgvector.
    Usa operador de distância cosseno nativo do PostgreSQL.
    """
    # Converter embedding do usuário para formato pgvector
    user_vec = np.array(user_embedding_vector)
    
    stmt = (
        select(Restaurant)
        .where(Restaurant.rating >= min_rating)
        .order_by(
            Restaurant.embedding.cosine_distance(user_vec)
        )
        .limit(limit)
    )
    
    return db.execute(stmt).scalars().all()
```

**Abordagem Alternativa (SQLite para desenvolvimento):**

Para SQLite ou quando pgvector não está disponível, calcular em memória:

```python
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def calculate_similarity(user_embedding, restaurant_embedding):
    """Calcula similaridade coseno entre dois embeddings."""
    user_vec = np.array(user_embedding).reshape(1, -1)
    rest_vec = np.array(restaurant_embedding).reshape(1, -1)
    similarity = cosine_similarity(user_vec, rest_vec)[0][0]
    return float(similarity)
```

**Nota de Performance:**
- **pgvector:** Escalável para milhões de registros, cálculo otimizado no banco
- **Cálculo em memória:** Adequado apenas para POC com poucos restaurantes (< 1000)

#### Passo 4: Ranking e Filtragem

1. Calcula similaridade com todos os restaurantes
2. Filtra restaurantes já pedidos recentemente (opcional)
3. Ordena por similaridade (maior primeiro)
4. Aplica filtros adicionais:
   - Rating mínimo (ex: >= 3.0)
   - Restaurantes ativos
5. Retorna top N restaurantes

```python
def generate_recommendations(user_id, limit=10, exclude_recent=True):
    """Gera recomendações personalizadas para um usuário."""
    # 1. Obter dados
    user = get_user(user_id)
    orders = get_user_orders(user_id)
    restaurants = get_all_restaurants()
    
    # 2. Calcular embedding do usuário
    user_embedding = calculate_user_preference_embedding(user_id, orders, restaurants)
    if not user_embedding:
        return get_popular_restaurants(limit)  # Fallback
    
    # 3. Calcular similaridades
    recommendations = []
    recent_restaurant_ids = set(order.restaurant_id for order in orders[:10]) if exclude_recent else set()
    
    for restaurant in restaurants:
        if restaurant.id in recent_restaurant_ids:
            continue
        
        if restaurant.rating < 3.0:  # Filtro de rating mínimo
            continue
        
        restaurant_embedding = json.loads(restaurant.embedding)
        similarity = calculate_similarity(user_embedding, restaurant_embedding)
        
        recommendations.append({
            "restaurant": restaurant,
            "similarity_score": similarity
        })
    
    # 4. Ordenar e retornar top N
    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)
    return recommendations[:limit]
```

### 6.2 Estratégias de Personalização

#### Filtragem Colaborativa
- Baseada em padrões de outros usuários similares
- "Usuários que pediram X também pediram Y"

#### Filtragem Baseada em Conteúdo
- Baseada em características dos restaurantes
- "Você gosta de culinária italiana, então recomendamos restaurantes italianos"

#### Híbrida (Implementada)
- Combina ambas as abordagens via embeddings semânticos
- Embeddings capturam similaridades tanto de conteúdo quanto de comportamento

### 6.3 Tratamento de Cold Start

**Problema:** Usuário novo sem histórico de pedidos.

**Solução:**
1. Se usuário não tem pedidos, retorna restaurantes populares (maior rating)
2. Ou retorna restaurantes novos (mais recentes)
3. Após primeiro pedido, começa a personalizar

```python
def get_recommendations_with_fallback(user_id, limit=10):
    """Gera recomendações com fallback para cold start."""
    orders = get_user_orders(user_id)
    
    if len(orders) == 0:
        # Cold start: retornar populares
        return get_popular_restaurants(limit)
    
    return generate_recommendations(user_id, limit)
```

### 6.4 Extração de Padrões do Usuário

O sistema extrai padrões comportamentais do histórico de pedidos para enriquecer o contexto das recomendações:

```python
from datetime import datetime
from collections import Counter

def extract_user_patterns(user_id, orders):
    """Extrai padrões comportamentais do usuário."""
    patterns = {
        "favorite_cuisines": [],
        "preferred_days": [],
        "preferred_hours": [],
        "average_order_value": 0.0,
        "total_orders": len(orders)
    }
    
    if not orders:
        return patterns
    
    # Culinárias favoritas (top 3)
    cuisine_counts = Counter([o.restaurant.cuisine_type for o in orders])
    patterns["favorite_cuisines"] = [cuisine for cuisine, _ in cuisine_counts.most_common(3)]
    
    # Dias da semana preferidos
    day_counts = Counter([o.order_date.weekday() for o in orders])
    patterns["preferred_days"] = [day for day, _ in day_counts.most_common(3)]
    
    # Horários preferidos (manhã, tarde, noite)
    hour_ranges = []
    for o in orders:
        hour = o.order_date.hour
        if 6 <= hour < 12:
            hour_ranges.append("manhã")
        elif 12 <= hour < 18:
            hour_ranges.append("tarde")
        else:
            hour_ranges.append("noite")
    patterns["preferred_hours"] = list(set(hour_ranges))
    
    # Ticket médio
    total_amount = sum([o.total_amount or 0 for o in orders])
    patterns["average_order_value"] = total_amount / len(orders) if orders else 0.0
    
    return patterns
```

**Uso dos Padrões:**
- Enriquecer prompts para geração de insights
- Melhorar recomendações baseadas em contexto temporal
- Personalizar mensagens e sugestões

### 6.5 Cache e Performance

- **Cache de embeddings de restaurantes:** Embeddings são gerados uma vez e armazenados no banco (usando pgvector em produção)
- **Cache de preferências do usuário:** Embedding do usuário é recalculado apenas quando necessário
- **Busca vetorial otimizada:** Usar pgvector para queries eficientes mesmo com milhões de restaurantes
- **Atualização incremental:** Recalcula apenas quando novo pedido é feito (se não for `refresh=true`)

---

## 7. Geração de Insights com GenAI

### 7.1 Visão Geral

O TasteMatch utiliza **Large Language Models (LLMs)** para gerar insights contextualizados em linguagem natural, explicando **por que** um restaurante foi recomendado para o usuário.

### 7.2 Estratégia de Geração

#### Abordagem: Prompt Engineering Contextualizado

O sistema envia ao LLM:
1. **Contexto do usuário:** Histórico de pedidos, preferências, padrões
2. **Informações do restaurante:** Nome, tipo de culinária, rating, características
3. **Score de similaridade:** O quão similar é ao perfil do usuário
4. **Instruções claras:** Formato esperado, tom, comprimento

### 7.3 Estrutura de Prompts

#### Template Base

```
Você é um assistente de recomendações da TasteMatch. 
Seu papel é explicar de forma clara e natural por que um restaurante foi recomendado para um usuário.

CONTEXTO DO USUÁRIO:
- Nome: {user_name}
- Total de pedidos: {total_orders}
- Culinárias favoritas: {favorite_cuisines}
- Padrões: {user_patterns}
- Pedidos recentes: {recent_orders_summary}

RESTAURANTE RECOMENDADO:
- Nome: {restaurant_name}
- Tipo: {cuisine_type}
- Avaliação: {rating}/5.0
- Descrição: {description}
- Score de similaridade: {similarity_score}

INSTRUÇÕES:
- Explique de forma natural e conversacional por que este restaurante foi recomendado
- Mencione conexões com o histórico do usuário (ex: "você costuma pedir comida italiana")
- Destaque características relevantes (rating, tipo de culinária)
- Seja específico e personalizado
- Mantenha o texto entre 2-3 frases
- Use tom amigável e profissional

Gere o insight:
```

#### Exemplo de Prompt Preenchido

```
Você é um assistente de recomendações da TasteMatch. 
Seu papel é explicar de forma clara e natural por que um restaurante foi recomendado para um usuário.

CONTEXTO DO USUÁRIO:
- Nome: João Silva
- Total de pedidos: 15
- Culinárias favoritas: italiana, japonesa, hamburgueria
- Padrões: Costuma pedir às sextas-feiras, prefere restaurantes com rating >= 4.0
- Pedidos recentes: Pizzaria Domino (2x), Sushi House (1x)

RESTAURANTE RECOMENDADO:
- Nome: Pizzaria Bella
- Tipo: italiana
- Avaliação: 4.5/5.0
- Descrição: Pizzas artesanais com ingredientes frescos
- Score de similaridade: 0.87

INSTRUÇÕES:
- Explique de forma natural e conversacional por que este restaurante foi recomendado
- Mencione conexões com o histórico do usuário
- Destaque características relevantes
- Seja específico e personalizado
- Mantenha o texto entre 2-3 frases
- Use tom amigável e profissional

Gere o insight:
```

### 7.4 Implementação com Groq API

#### Configuração

```python
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_insight(user_context, restaurant, similarity_score):
    """Gera insight contextualizado usando Groq LLM."""
    
    prompt = build_insight_prompt(user_context, restaurant, similarity_score)
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",  # ou "llama-3.1-8b-instant" (mais rápido)
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em recomendações personalizadas de restaurantes. Seja claro, específico e natural."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,  # Balance entre criatividade e consistência
            max_tokens=150
        )
        
        insight = response.choices[0].message.content.strip()
        return insight
        
    except Exception as e:
        # Fallback: insight genérico
        return f"Recomendamos {restaurant.name} baseado nas suas preferências."
```

### 7.5 Otimizações e Cache

#### Cache de Insights

Para evitar chamadas repetidas à API:
- Cache insights por combinação `user_id + restaurant_id`
- TTL de 7 dias (insights podem mudar com novo histórico)
- Recalcular apenas se histórico mudou significativamente

```python
def get_cached_insight(user_id, restaurant_id):
    """Busca insight em cache."""
    recommendation = get_recommendation(user_id, restaurant_id)
    if recommendation and recommendation.insight_text:
        # Verificar se ainda é recente (< 7 dias)
        if (datetime.now() - recommendation.generated_at).days < 7:
            return recommendation.insight_text
    return None
```

#### Batching

Gerar insights para múltiplas recomendações em paralelo:

```python
import asyncio

async def generate_insights_batch(user_context, recommendations):
    """Gera insights para múltiplas recomendações em paralelo."""
    tasks = [
        generate_insight_async(user_context, rec.restaurant, rec.similarity_score)
        for rec in recommendations
    ]
    insights = await asyncio.gather(*tasks)
    return insights
```

### 7.6 Tratamento de Erros

#### Estratégias de Fallback

1. **Se API LLM falhar:**
   - Retornar insight genérico baseado em template
   - Ex: "Recomendamos {restaurant.name} baseado nas suas preferências."

2. **Se API demorar muito (> 5s):**
   - Usar insight cached mesmo que antigo
   - Ou retornar insight genérico

3. **Se prompt for muito longo:**
   - Resumir contexto do usuário
   - Priorizar informações mais relevantes

### 7.7 Alternativas de LLM

#### Opção 1: Groq API (Recomendado)
- **Modelos disponíveis:**
  - `llama-3.1-70b-versatile` (melhor qualidade, recomendado para insights)
  - `llama-3.1-8b-instant` (mais rápido, menor custo)
- **Vantagens:** Muito rápido, baixo custo, boa qualidade
- **Uso:** Produção

#### Opção 2: OpenAI API
- **Modelos disponíveis:**
  - `gpt-4o-mini` (recomendado, balance qualidade/custo)
  - `gpt-3.5-turbo` (mais rápido, menor custo)
- **Vantagens:** Excelente qualidade, muito confiável
- **Desvantagem:** Mais caro que Groq

#### Opção 3: Modelo Local (Avançado)
- **Modelo:** Ollama + Llama 3.1
- **Vantagens:** Zero custo, privacidade total
- **Desvantagem:** Requer infraestrutura local, mais lento

**Recomendação:** Groq API com `llama-3.1-70b-versatile` para POC e produção inicial.

---

## 8. Estrutura de Pastas do Projeto

### 8.1 Estrutura Completa

```
tastematch/
├── README.md                    # Documentação principal do projeto
├── SPEC.md                      # Este documento (especificação técnica)
├── .env.example                 # Template de variáveis de ambiente
├── .gitignore                   # Arquivos ignorados pelo Git
├── pyproject.toml               # Dependências do Poetry (ou requirements.txt)
├── docker-compose.yml           # Orquestração de serviços (PostgreSQL + API)
│
├── backend/                     # Backend FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point da aplicação
│   │   ├── config.py            # Configurações (env vars, settings)
│   │   │
│   │   ├── api/                 # Endpoints da API
│   │   │   ├── __init__.py
│   │   │   ├── deps.py          # Dependências compartilhadas (auth, db)
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py      # /auth/register, /auth/login
│   │   │       ├── recommendations.py  # /api/recommendations
│   │   │       ├── restaurants.py      # /api/restaurants
│   │   │       ├── orders.py           # /api/orders
│   │   │       └── users.py            # /api/users
│   │   │
│   │   ├── core/                # Lógica de negócio principal
│   │   │   ├── __init__.py
│   │   │   ├── security.py      # JWT, hash de senhas
│   │   │   ├── embeddings.py    # Geração de embeddings
│   │   │   ├── recommender.py   # Lógica de recomendação
│   │   │   └── llm_service.py   # Integração com LLM (Groq)
│   │   │
│   │   ├── models/              # Modelos Pydantic
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── restaurant.py
│   │   │   ├── order.py
│   │   │   └── recommendation.py
│   │   │
│   │   ├── database/            # Camada de banco de dados
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Base de configuração SQLAlchemy
│   │   │   ├── models.py        # Modelos SQLAlchemy (ORM)
│   │   │   ├── schemas.py       # Schemas de criação/atualização
│   │   │   └── crud.py          # Operações CRUD
│   │   │
│   │   └── utils/               # Utilitários
│   │       ├── __init__.py
│   │       └── helpers.py       # Funções auxiliares
│   │
│   ├── tests/                   # Testes
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_recommendations.py
│   │   └── conftest.py          # Fixtures pytest
│   │
│   ├── scripts/                 # Scripts auxiliares
│   │   ├── init_db.py           # Inicializar banco de dados
│   │   ├── seed_data.py         # Popular com dados de exemplo
│   │   └── generate_embeddings.py  # Gerar embeddings dos restaurantes
│   │
│   ├── Dockerfile               # Imagem Docker para backend
│   └── alembic/                 # Migrations (se usar Alembic)
│       └── versions/
│
├── frontend/                    # Frontend
│   ├── index.html               # Página principal
│   ├── styles.css               # Estilos
│   ├── app.js                   # Lógica JavaScript
│   ├── api.js                   # Cliente HTTP para API
│   └── assets/                  # Imagens, ícones
│
├── data/                        # Dados de exemplo/seeding
│   ├── restaurants.json         # Lista de restaurantes exemplo
│   └── sample_orders.json       # Pedidos de exemplo
│
└── docs/                        # Documentação adicional
    ├── api.md                   # Documentação da API (opcional)
    └── deployment.md            # Guia de deploy (opcional)
```

### 8.2 Convenções de Nomenclatura

#### Arquivos Python
- **Snake_case:** `recommendations.py`, `llm_service.py`
- **Classes:** `PascalCase:` `UserModel`, `RecommendationService`
- **Funções/variáveis:** `snake_case:` `generate_recommendations`, `user_id`

#### Endpoints da API
- **kebab-case:** `/api/recommendations`, `/api/users/me`
- **Plural para recursos:** `/restaurants` (não `/restaurant`)

#### Banco de Dados
- **snake_case:** `user_preferences`, `created_at`
- **Tabelas no plural:** `users`, `restaurants`, `orders`

### 8.3 Separação de Responsabilidades

- **`api/routes/`:** Apenas roteamento, validação de entrada/saída
- **`core/`:** Lógica de negócio pura (sem dependência de framework)
- **`database/`:** Apenas acesso a dados, sem lógica de negócio
- **`models/`:** Apenas schemas de validação (Pydantic)

---

## 9. Instalação e Configuração

### 9.1 Pré-requisitos

- **Python 3.11+**
- **pip** ou **poetry** (gerenciador de dependências)
- **Git**

### 9.2 Configuração do Ambiente

#### Opção A: Usando Docker Compose (Recomendado)

A forma mais simples e reprodutível de executar o projeto:

```bash
# 1. Clonar o repositório (se aplicável)
git clone <repo-url>
cd tastematch

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env e adicionar GROQ_API_KEY

# 3. Iniciar serviços com Docker Compose
docker-compose up -d

# A API estará disponível em http://localhost:8000
```

**Vantagens:**
- Configuração automática do PostgreSQL com pgvector
- Sem necessidade de instalar dependências manualmente
- Ambiente isolado e reprodutível

#### Opção B: Instalação Manual

#### Passo 1: Clonar/Criar Projeto

```bash
cd /home/brunoadsba/ifood
mkdir tastematch
cd tastematch
```

#### Passo 2: Criar Ambiente Virtual

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

#### Passo 3: Instalar Dependências

**Opção A: Usando pip + requirements.txt**

```bash
pip install -r requirements.txt
```

**Opção B: Usando Poetry (recomendado)**

```bash
poetry install
poetry shell
```

#### Passo 4: Configurar Variáveis de Ambiente

Copiar `.env.example` para `.env` e preencher:

```bash
cp .env.example .env
```

Editar `.env`:

```env
# Aplicação
APP_NAME=TasteMatch
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production

# Banco de Dados
DATABASE_URL=sqlite:///./tastematch.db

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Groq API (para insights)
GROQ_API_KEY=your-groq-api-key-here

# OpenAI API (alternativa ao Groq)
OPENAI_API_KEY=optional-openai-api-key

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

#### Passo 5: Inicializar Banco de Dados

```bash
cd backend
python scripts/init_db.py
python scripts/seed_data.py  # Popular com dados de exemplo
python scripts/generate_embeddings.py  # Gerar embeddings dos restaurantes
```

#### Passo 6: Executar Aplicação

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

A API estará disponível em: `http://localhost:8000`

### 9.3 Arquivo requirements.txt

```
# Core
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Banco de Dados
sqlalchemy==2.0.23
alembic==1.12.1
pgvector==0.2.4  # Para busca vetorial otimizada (PostgreSQL)

# Autenticação
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4  # Hash de senhas com bcrypt (salt automático)
python-multipart==0.0.6

# IA e ML
sentence-transformers==2.2.2
numpy==1.24.3
pandas==2.1.3
scikit-learn==1.3.2

# LLM
groq==0.4.1
# ou openai==1.3.5 (alternativa)

# Utilitários
python-dotenv==1.0.0
httpx==0.25.1

# Testes
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
```

### 9.4 Arquivo .env.example

```env
# Aplicação
APP_NAME=TasteMatch
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=change-this-in-production

# Banco de Dados
DATABASE_URL=sqlite:///./tastematch.db

# JWT
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Groq API
GROQ_API_KEY=your-groq-api-key

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 9.5 Obter API Keys

#### Groq API Key
1. Acessar: https://console.groq.com
2. Criar conta (gratuito)
3. Gerar API key
4. Copiar para `.env`

#### OpenAI API Key (Opcional)
1. Acessar: https://platform.openai.com
2. Criar conta
3. Adicionar créditos
4. Gerar API key

---

## 10. Guia de Desenvolvimento

### 10.1 Fluxo de Trabalho Recomendado

#### Fase 1: Setup Inicial
1. ✅ Criar estrutura de pastas
2. ✅ Configurar ambiente virtual
3. ✅ Instalar dependências
4. ✅ Configurar `.env`
5. ✅ Inicializar banco de dados

#### Fase 2: Backend Core
1. ✅ Criar modelos de banco (SQLAlchemy)
2. ✅ Criar modelos Pydantic
3. ✅ Implementar autenticação (JWT)
4. ✅ Implementar CRUD básico (usuários, restaurantes)

#### Fase 3: Lógica de Recomendação
1. ✅ Implementar geração de embeddings
2. ✅ Implementar cálculo de similaridade
3. ✅ Implementar algoritmo de recomendação
4. ✅ Testar com dados de exemplo

#### Fase 4: Integração com LLM
1. ✅ Implementar serviço de LLM (Groq)
2. ✅ Criar templates de prompts
3. ✅ Integrar geração de insights
4. ✅ Implementar cache de insights

#### Fase 5: Frontend
1. ✅ Criar interface básica
2. ✅ Integrar com API
3. ✅ Exibir recomendações
4. ✅ Exibir insights

#### Fase 6: Refinamento
1. ✅ Adicionar tratamento de erros
2. ✅ Otimizar performance
3. ✅ Adicionar testes
4. ✅ Documentar

### 10.2 Como Usar Este Documento com IA

#### Para o Desenvolvedor:
1. Use este documento como referência técnica completa
2. Siga a estrutura de pastas definida
3. Implemente os endpoints conforme especificação
4. Consulte exemplos de código quando necessário

#### Para a IA (Cursor, ChatGPT, etc.):
1. **Contexto:** Sempre referencie este documento como contexto
   - "Baseado na especificação do TasteMatch em SPEC.md..."
   - "Seguindo a arquitetura definida em SPEC.md..."

2. **Prompting Estruturado:**
   ```
   Baseado na especificação técnica do TasteMatch (SPEC.md):
   - Implementar endpoint GET /api/recommendations
   - Usar a lógica de recomendação definida na seção 6
   - Seguir estrutura de pastas da seção 8
   - Usar modelos Pydantic da seção 4.2
   ```

3. **Desenvolvimento Incremental:**
   - Implementar uma seção/funcionalidade por vez
   - Validar contra especificação
   - Atualizar documentação se necessário

### 10.3 Padrões de Código

#### FastAPI: Estrutura de Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.base import get_db
from app.models.recommendation import RecommendationResponse
from app.core.recommender import generate_recommendations
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

@router.get("", response_model=RecommendationResponse)
async def get_recommendations(
    limit: int = 10,
    refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtém recomendações personalizadas para o usuário."""
    try:
        recommendations = generate_recommendations(
            user_id=current_user.id,
            limit=limit,
            refresh=refresh,
            db=db
        )
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Tratamento de Erros

```python
from fastapi import HTTPException

# Sempre use HTTPException para erros HTTP
if not user:
    raise HTTPException(status_code=404, detail="User not found")

# Use try/except para erros inesperados
try:
    result = risky_operation()
except SpecificError as e:
    raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

#### Logging

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.info("Starting operation")
    try:
        result = do_something()
        logger.info(f"Operation successful: {result}")
        return result
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}", exc_info=True)
        raise
```

### 10.4 Convenções de Commit

Use Conventional Commits:

```
feat: adicionar endpoint de recomendações
fix: corrigir cálculo de similaridade
docs: atualizar README
refactor: reorganizar estrutura de pastas
test: adicionar testes para recomendações
```

---

## 11. Testes e Validação

### 11.1 Estratégia de Testes

#### Testes Unitários
- Testar funções puras (cálculo de similaridade, geração de embeddings)
- Mockar dependências externas (API LLM, banco de dados)

#### Testes de Integração
- Testar endpoints completos (com banco de dados de teste)
- Testar fluxo de recomendação end-to-end

#### Testes de API
- Usar `httpx.AsyncClient` para testar endpoints FastAPI
- Validar schemas de resposta

### 11.2 Dados de Exemplo

#### Script de Seeding

Criar `backend/scripts/seed_data.py` com:
- 20-30 restaurantes de exemplo (diferentes tipos de culinária)
- 5-10 usuários de exemplo
- 50-100 pedidos de exemplo (histórico variado)

### 11.3 Exemplo de Teste

```python
# backend/tests/test_recommendations.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_recommendations(auth_headers):
    """Testa obtenção de recomendações."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/recommendations?limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 5
        assert "similarity_score" in data["recommendations"][0]
```

### 11.4 Validação de Recomendações

#### Métricas a Validar
- **Precisão:** Recomendações são relevantes?
- **Diversidade:** Recomendações são variadas?
- **Performance:** Resposta em < 1 segundo?

#### Testes Manuais
1. Criar usuário com histórico específico
2. Verificar se recomendações fazem sentido
3. Validar insights gerados

---

## 12. Deploy e Produção

### 12.1 Configuração de Deploy

#### Fly.io (Recomendado para Backend)

**Arquivo: `backend/fly.toml`**

```toml
app = "tastematch-api"
primary_region = "gru"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  DATABASE_URL = "postgresql://..."
  GROQ_API_KEY = "..."

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

**Comandos:**
```bash
cd backend
fly launch
fly secrets set GROQ_API_KEY=...
fly deploy
```

#### Netlify (Frontend)

**Arquivo: `netlify.toml`**

```toml
[build]
  command = "echo 'No build needed'"
  publish = "frontend"

[[redirects]]
  from = "/api/*"
  to = "https://tastematch-api.fly.dev/api/:splat"
  status = 200
  force = true
```

### 12.2 Variáveis de Ambiente de Produção

- `ENVIRONMENT=production`
- `DEBUG=False`
- `DATABASE_URL=postgresql://...` (PostgreSQL em produção)
- `SECRET_KEY=` (gerar chave segura)
- `GROQ_API_KEY=` (configurar)

### 12.3 Configuração CORS

Para permitir requisições do frontend (Netlify/Vercel) ao backend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tastematch.netlify.app",  # Frontend em produção
        "http://localhost:3000",  # Frontend em desenvolvimento
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Importante:** Configurar CORS corretamente evita erros de "CORS policy" no navegador.

### 12.4 Monitoramento Básico

- **Logs:** Usar logging estruturado com níveis apropriados (INFO em dev, WARNING/ERROR em prod)
- **Health Check:** Endpoint `/health` para verificar status da aplicação e banco
- **Métricas:** Contar recomendações geradas, tempo de resposta, taxa de erro

---

## 13. Roadmap e Melhorias Futuras

### 13.1 Features Opcionais (Fase 2)

- **Filtros Avançados:** Preço, distância, horário de funcionamento
- **A/B Testing:** Testar diferentes algoritmos de recomendação
- **Feedback Loop:** Permitir usuário avaliar recomendações
- **Notificações:** Alertar sobre novos restaurantes similares
- **Refresh Tokens:** Implementar refresh tokens para melhor segurança e UX
- **Normalização de Dados:** Criar tabela `order_items` relacional para análises mais granulares

### 13.2 Otimizações Planejadas

- **Cache Redis:** Cachear recomendações por usuário (TTL 1 hora)
- **Batch Processing:** Processar recomendações em background
- **Modelo de Embedding Customizado:** Treinar modelo específico para restaurantes
- **Clustering de Preferências:** Em vez de média única, criar múltiplos clusters de interesse do usuário (ex: "Cluster Almoço Saudável" vs "Cluster Jantar Junk Food") para melhor personalização

### 13.3 Escalabilidade

- **Múltiplos Workers:** Usar Gunicorn com múltiplos workers
- **Load Balancer:** Distribuir carga entre instâncias
- **CDN:** Servir frontend via CDN
- **IDs Não Sequenciais:** Migrar para UUID ou ULID para sistemas distribuídos (segurança e escalabilidade)

### 13.4 Melhorias de Modelagem

- **UUID/ULID para IDs:** Em produção, usar IDs não sequenciais para melhor segurança e escalabilidade em ambientes distribuídos
- **Tabela order_items:** Normalizar estrutura de pedidos para permitir análises mais detalhadas de preferências por prato

---

## Conclusão

Este documento serve como **fonte única de verdade** para o desenvolvimento do TasteMatch. Use-o como referência completa durante todo o ciclo de desenvolvimento, tanto para orientação humana quanto para instruir IAs de desenvolvimento.

**Princípios do Projeto:**
- ✅ Código limpo e bem estruturado
- ✅ Documentação clara e completa
- ✅ Foco em valor de negócio (recomendações relevantes)
- ✅ Performance e escalabilidade consideradas desde o início
- ✅ Facilidade de manutenção e extensão

**Boa sorte no desenvolvimento! 🚀**

---

**Última atualização:** 2025-01-27  
**Versão do documento:** 1.0.0  
**Autor:** Equipe TasteMatch

