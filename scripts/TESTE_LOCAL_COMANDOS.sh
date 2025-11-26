#!/bin/bash
# Script para testar localmente - TasteMatch

echo "🚀 Iniciando testes locais..."
echo ""

# Verificar se já está rodando
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Backend já está rodando na porta 8000"
    echo "   Para parar: pkill -f 'uvicorn app.main:app'"
else
    echo "✅ Iniciando backend na porta 8000..."
    echo "   Abra um novo terminal e execute:"
    echo "   cd /home/brunoadsba/ifood/tastematch/backend"
    echo "   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    echo ""
fi

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Frontend já está rodando na porta 5173"
else
    echo "✅ Para iniciar frontend:"
    echo "   Abra outro terminal e execute:"
    echo "   cd /home/brunoadsba/ifood/tastematch/frontend"
    echo "   npm run dev"
    echo ""
fi

echo "📋 Checklist de testes:"
echo "   1. Backend: http://localhost:8000/health"
echo "   2. Frontend: http://localhost:5173"
echo "   3. Verificar correções aplicadas"
echo ""
echo "   Consulte TESTE_LOCAL.md para detalhes completos"

