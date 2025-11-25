#!/bin/bash
# Script wrapper para executar seed em background no Fly.io
# Uso: fly ssh console -a tastematch-api -C "bash /app/scripts/run_seed_background.sh"

cd /app
nohup python scripts/seed_production.py > /tmp/seed.log 2>&1 &
SEED_PID=$!

echo "✅ Seed iniciado em background (PID: $SEED_PID)"
echo "📝 Logs sendo salvos em /tmp/seed.log"
echo ""
echo "Para acompanhar os logs em tempo real:"
echo "  tail -f /tmp/seed.log"
echo ""
echo "Para verificar o status:"
echo "  ps aux | grep seed_production"
echo ""
echo "O processo continuará rodando mesmo se você sair do SSH."

