# Dockerfile OTIMIZADO para TasteMatch Backend
# Reduz uso de espaço em disco durante build (PyTorch CPU-only)

FROM python:3.11-slim

WORKDIR /app

# Instalar apenas dependências essenciais e limpar imediatamente
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements
COPY requirements.txt .

# ESTRATÉGIA: Instalar PyTorch CPU-only primeiro (muito menor: ~500MB vs ~2GB)
# PyTorch CPU é suficiente para embeddings (não precisa de GPU em produção)
RUN pip install --no-cache-dir torch==2.1.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Instalar todas as dependências do requirements.txt (exceto torch que já foi instalado)
# Criar requirements temporário sem torch para evitar conflito de versão
RUN grep -v "^torch==" requirements.txt > /tmp/requirements-no-torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements-no-torch.txt && \
    rm /tmp/requirements-no-torch.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip && \
    rm -rf /tmp/*

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
# OTIMIZAÇÃO MEMÓRIA: 1 worker ao invés de 2 para reduzir uso de memória em ~50%
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

