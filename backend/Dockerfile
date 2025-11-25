# Dockerfile OTIMIZADO para TasteMatch Backend
# Reduz uso de espaço em disco durante build (PyTorch CPU-only)

FROM python:3.11-slim

WORKDIR /app

# Instalar apenas dependências essenciais e limpar imediatamente
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements
COPY requirements.txt .

# ESTRATÉGIA: Instalar PyTorch CPU-only primeiro (muito menor: ~500MB vs ~2GB)
# PyTorch CPU é suficiente para embeddings (não precisa de GPU em produção)
RUN pip install --no-cache-dir torch==2.1.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Instalar dependências leves primeiro (sem torch, que já foi instalado)
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    email-validator==2.3.0 \
    sqlalchemy==2.0.23 \
    alembic==1.12.1 \
    psycopg2-binary==2.9.9 \
    pgvector==0.2.4 \
    python-jose[cryptography]==3.3.0 \
    bcrypt==4.1.2 \
    python-multipart==0.0.6 \
    groq==0.4.1 \
    python-dotenv==1.0.0 \
    httpx==0.25.1 \
    requests==2.31.0 \
    && pip cache purge

# Instalar dependências pesadas de ML em grupo separado
RUN pip install --no-cache-dir \
    numpy==1.26.2 \
    pandas==2.1.4 \
    scikit-learn==1.3.2 \
    transformers==4.35.2 \
    huggingface-hub==0.20.0 \
    sentence-transformers==2.3.1 \
    && pip cache purge \
    && rm -rf /root/.cache/pip \
    && rm -rf /tmp/*

# Copiar código da aplicação
COPY . .

# Criar diretório para logs
RUN mkdir -p /app/logs

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expor porta
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

