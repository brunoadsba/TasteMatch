#!/bin/bash

# Script para instalar navegadores e executar testes E2E
# Uso: ./run-tests.sh

set -e

echo "📦 Instalando navegadores do Playwright..."
npx playwright install chromium

echo ""
echo "🚀 Executando testes E2E..."
npm run test:e2e -- --project="Mobile iPhone SE" --reporter=list

echo ""
echo "✅ Testes concluídos!"
echo ""
echo "Para ver relatório HTML: npm run test:e2e:report"

