# Chef Virtual - Documentação Completa

**Versão**: 1.0.3  
**Data**: 30/11/2025  
**Status**: ✅ 100% Completo - Rodando Localmente

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Instalação e Configuração](#instalação-e-configuração)
4. [Uso](#uso)
5. [Monitoramento](#monitoramento)
6. [Troubleshooting](#troubleshooting)
7. [Lições Aprendidas](#lições-aprendidas)
8. [Referências](#referências)

---

## 🎯 Visão Geral

O **Chef Virtual** é um chatbot conversacional integrado ao TasteMatch que ajuda usuários a encontrar restaurantes e pratos usando inteligência artificial. O sistema utiliza:

- **RAG (Retrieval-Augmented Generation)** com PGVector para busca semântica
- **Hybrid Search** combinando busca exata e semântica
- **LLM Groq** (Llama-3.1-8b-instant) para geração de respostas
- **STT/TTS** para suporte a áudio (Groq Whisper + Edge-TTS)
- **Monitoramento completo** de métricas LLM

### Funcionalidades Principais

- ✅ Chat conversacional sobre restaurantes e comida
- ✅ Recomendações personalizadas baseadas em preferências
- ✅ Suporte a texto e áudio (gravação e reprodução)
- ✅ Histórico de conversas persistido
- ✅ Prevenção de alucinação e validação de respostas
- ✅ Interações sociais naturais (saudações, agradecimentos)
- ✅ Filtro semântico rigoroso para recomendações precisas
- ✅ Tratamento inteligente de queries específicas (sopa, açaí, churrasco, etc.)
- ✅ Respostas limpas sem seções desnecessárias
- ✅ Monitoramento de latência, tokens e custo
- ✅ Rate limiting (30 requisições/minuto)

---

## 🏗️ Arquitetura

### Componentes Principais

```
┌─────────────────┐
│   Frontend      │
│   (React)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│  RAG   │ │   LLM   │
│Service │ │  Groq   │
└────┬───┘ └────┬─────┘
     │          │
     ▼          ▼
┌──────────┐ ┌──────────┐
│ PGVector │ │Monitoring│
│(Postgres)│ │  (DB)    │
└──────────┘ └──────────┘
```

### Fluxo de Dados

1. **Usuário envia mensagem** (texto ou áudio)
2. **Backend processa**:
   - Se áudio: STT (Groq Whisper) → texto
   - RAG busca contexto relevante (PGVector + Hybrid Search)
   - LLM gera resposta (Groq Llama)
   - Monitoramento coleta métricas
3. **Resposta retornada**:
   - Texto formatado
   - Opcionalmente: áudio (TTS via Edge-TTS)

### Tecnologias

- **Backend**: FastAPI, Python 3.10+
- **Frontend**: React, TypeScript
- **Banco de Dados**: PostgreSQL com PGVector
- **LLM**: Groq (Llama-3.1-8b-instant)
- **Embeddings**: HuggingFace (paraphrase-multilingual-MiniLM-L12-v2)
- **STT**: Groq Whisper API
- **TTS**: Edge-TTS
- **Rate Limiting**: slowapi

---

## 🚀 Instalação e Configuração

### Pré-requisitos

- Python 3.10+
- PostgreSQL 16+ com extensão pgvector
- Node.js 18+ (para frontend)
- Docker (opcional, para PostgreSQL)

### Backend

1. **Instalar dependências**:
```bash
cd tastematch/backend
pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente** (`.env`):
```env
DATABASE_URL=postgresql://tastematch:tastematch_dev@localhost:5432/tastematch
GROQ_API_KEY=sua_chave_groq_aqui
SECRET_KEY=sua_chave_secreta_aqui
```

3. **Executar migrations**:
```bash
alembic upgrade head
```

4. **Inicializar base de conhecimento**:
```bash
python -c "from app.core.knowledge_base import update_knowledge_base; from app.database.base import get_db; update_knowledge_base(next(get_db()))"
```

5. **Iniciar servidor**:
```bash
uvicorn app.main:app --reload
```

### Frontend

1. **Instalar dependências**:
```bash
cd tastematch/frontend
npm install
```

2. **Configurar variáveis** (`.env`):
```env
VITE_API_URL=http://localhost:8000
```

3. **Iniciar servidor de desenvolvimento**:
```bash
npm run dev
```

### Docker (PostgreSQL)

```bash
cd tastematch
docker-compose up -d postgres
```

---

## 💻 Uso

### API Endpoints

#### `POST /api/chat/`
Envia mensagem ao Chef Virtual.

**Request**:
```json
{
  "message": "Quero uma pizza"
}
```

**Response**:
```json
{
  "answer": "Recomendo a Pizzaria Bella...",
  "audio_url": "http://localhost:8000/api/chat/audio/response_123.mp3",
  "source_documents": [...],
  "validation": {
    "confidence_score": 0.95,
    "total_sources": 5,
    "restaurant_sources": 3
  }
}
```

#### `GET /api/chat/history`
Obtém histórico de conversas.

#### `GET /api/llm/summary`
Obtém resumo de métricas LLM.

**Query Parameters**:
- `days` (opcional): Número de dias (1-90, padrão: 7)
- `user_id` (opcional): ID do usuário

**Response**:
```json
{
  "user_id": 1,
  "days": 7,
  "summary": {
    "total_calls": 150,
    "total_tokens": 318000,
    "total_cost_usd": 0.0159,
    "avg_latency_ms": 650,
    "error_rate": 0.0
  },
  "timestamp": "2025-01-XXT..."
}
```

### Frontend

O Chef Virtual está disponível no Dashboard através de um botão flutuante (FAB) no canto inferior direito.

**Funcionalidades**:
- Chat em tempo real
- Gravação de áudio
- Reprodução de respostas em áudio
- Histórico de conversas
- Estados visuais (listening, thinking, speaking)

---

## 📊 Monitoramento

### Métricas Coletadas

O sistema coleta automaticamente:

- **Latência**: Tempo de resposta do LLM (ms)
- **Tokens**: Input, output e total
- **Custo**: Estimado em USD (baseado em preços Groq)
- **Tamanho da resposta**: Caracteres
- **Erros**: Mensagens de erro (se houver)

### Visualização

1. **Endpoint de métricas**: `GET /api/llm/summary`
2. **Banco de dados**: Tabela `llm_metrics`
3. **Logs estruturados**: Console/arquivo de log

### Exemplo de Consulta SQL

```sql
-- Últimas 10 chamadas
SELECT 
    model,
    total_tokens,
    latency_ms,
    estimated_cost_usd,
    created_at
FROM llm_metrics
ORDER BY created_at DESC
LIMIT 10;

-- Resumo diário
SELECT 
    DATE(created_at) as date,
    COUNT(*) as calls,
    SUM(total_tokens) as tokens,
    SUM(estimated_cost_usd) as cost,
    AVG(latency_ms) as avg_latency
FROM llm_metrics
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de conexão com banco
```
OperationalError: connection to server at "localhost" failed
```
**Solução**: Verificar se PostgreSQL está rodando:
```bash
docker ps | grep postgres
# ou
systemctl status postgresql
```

#### 2. Erro "GROQ_API_KEY não configurada"
**Solução**: Adicionar `GROQ_API_KEY` no arquivo `.env`

#### 3. Rate limit excedido (429)
**Solução**: Aguardar 1 minuto ou aumentar limite no código (não recomendado)

#### 4. Embeddings não encontrados
**Solução**: Inicializar base de conhecimento:
```bash
python -c "from app.core.knowledge_base import update_knowledge_base; from app.database.base import get_db; update_knowledge_base(next(get_db()))"
```

#### 5. Erro ao processar áudio
**Solução**: Verificar se FFmpeg está instalado:
```bash
ffmpeg -version
```

### Logs

Logs estruturados são gerados automaticamente. Em produção, configure para arquivo:

```python
# app/core/logging_config.py
file_handler = logging.FileHandler('app.log')
```

---

## 📚 Lições Aprendidas

### 1. Escolha de Tecnologias

**PGVector vs FAISS**:
- ✅ PGVector: Persistência garantida, backup automático, integrado ao banco
- ❌ FAISS: Requer volume persistente, mais complexo de gerenciar
- **Decisão**: PGVector foi a melhor escolha para produção

**Hybrid Search**:
- ✅ Combina busca exata (SQL) + semântica (embeddings)
- ✅ Melhor precisão para nomes de restaurantes
- ✅ Prioriza resultados exatos sobre semânticos

### 2. Prompt Engineering

**Desafios**:
- LLM tendia a ser verboso e repetitivo
- Frases desnecessárias ("Com base no contexto", "Eu diria que")
- Repetição de perguntas do usuário

**Soluções**:
- Regras explícitas no prompt
- Post-processamento com `clean_answer()`
- Detecção de interações sociais (bypass do LLM)
- Temperatura reduzida (0.5) para respostas mais diretas

### 3. Monitoramento

**Importância**:
- Essencial para entender custos e performance
- Permite otimizações baseadas em dados reais
- Facilita debugging de problemas

**Implementação**:
- Callback LangChain para captura automática
- Armazenamento no banco para análise histórica
- Logs estruturados para observabilidade

### 4. Rate Limiting

**Necessidade**:
- Groq API tem limite de 30 RPM (free tier)
- Protege contra uso excessivo
- Evita custos inesperados

**Implementação**:
- `slowapi` para rate limiting
- Por usuário autenticado (fallback para IP)
- Em memória (pode migrar para Redis em produção)

### 5. Prevenção de Alucinação

**Estratégias**:
- Validação pós-resposta contra contexto
- Extração e validação de nomes de restaurantes
- Fallback para respostas genéricas
- Guardrails no prompt

### 6. UX e Interações Sociais

**Descoberta**:
- LLM não é necessário para interações simples
- Respostas pré-definidas são mais rápidas e naturais
- Bypass do LLM para saudações, agradecimentos, despedidas

**Implementação**:
- `detect_social_interaction()` antes do LLM
- Respostas variadas e naturais
- Reduz latência e custo

### 7. Testes E2E

**Desafios**:
- Playwright requer login
- Seletores precisam ser robustos
- Timing é crítico (aguardar LLM)

**Soluções**:
- Helpers reutilizáveis (`ensureLoggedIn`, `openChefVirtual`)
- Timeouts adequados (15s para respostas LLM)
- Seletores específicos (scoped dentro de `[role="dialog"]`)

---

## 📖 Referências

### Documentação

- [LangChain Documentation](https://python.langchain.com/)
- [PGVector](https://github.com/pgvector/pgvector)
- [Groq API](https://console.groq.com/docs)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Playwright](https://playwright.dev/)

### Arquivos do Projeto

- `tastematch/Docs/chef-virtual.md` - Plano de implementação original
- `tastematch/Docs/STATUS-CHEF-VIRTUAL.md` - Status detalhado do projeto
- `tastematch/backend/test_monitoring.py` - Script de teste de monitoramento

### Código Principal

- `backend/app/core/chef_chat.py` - Lógica do Chef Virtual
- `backend/app/core/rag_service.py` - Serviço RAG
- `backend/app/core/llm_monitoring.py` - Monitoramento LLM
- `frontend/src/components/features/ChefChat.tsx` - Componente de chat

---

## 🎯 Próximos Passos (Opcional)

### Melhorias Futuras

1. **Cache de Respostas**: Reduzir chamadas LLM para perguntas frequentes
2. **Redis para Rate Limiting**: Compartilhar limite entre instâncias
3. **Retry com Backoff**: Melhorar resiliência para erros 429
4. **Dashboard de Métricas**: Visualização gráfica de métricas
5. **Alertas**: Notificações para latência alta ou erros
6. **Multi-idioma**: Suporte a outros idiomas além de português

### Testes Pendentes

- Testes E2E de áudio (requer permissões de microfone)
- Testes de carga (stress testing)
- Testes de integração com diferentes modelos LLM

---

**Última Atualização**: 2025-01-XX  
**Mantenedor**: Equipe TasteMatch

