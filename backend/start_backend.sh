#!/bin/bash
# Script para iniciar o backend TasteMatch

cd "$(dirname "$0")"

echo "🚀 Iniciando backend TasteMatch..."
echo "📁 Diretório: $(pwd)"
echo ""

# Verificar se Python está disponível
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    exit 1
fi

# Verificar se uvicorn está instalado
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn não está instalado!"
    echo "   Instale com: pip install uvicorn[standard]"
    exit 1
fi

echo "✅ Dependências verificadas"
echo "🌐 Iniciando servidor em http://localhost:8000"
echo "📚 Documentação: http://localhost:8000/docs"
echo ""
echo "Pressione Ctrl+C para parar"
echo ""

python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

