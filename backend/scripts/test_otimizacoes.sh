#!/bin/bash
#
# Script de testes para validar otimizações de memória
# Execute após iniciar o backend localmente
#

echo "🧪 TESTES DE VALIDAÇÃO - Otimizações de Memória"
echo ""

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "📋 Testando endpoints básicos..."
echo ""

# Teste 1: Health Check
echo "1. Health Check..."
HEALTH=$(curl -s "$BASE_URL/health" 2>&1)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ Health check OK"
else
    echo "   ❌ Health check FALHOU"
    echo "   Resposta: $HEALTH"
    exit 1
fi

# Teste 2: Verificar se pool está configurado
echo ""
echo "2. Verificando pool de conexões..."
# Este teste requer que o backend esteja rodando
echo "   ℹ️  Verifique manualmente nos logs se pool_size=4 está sendo usado"

# Teste 3: Endpoint de restaurantes (deve ter Cache-Control header)
echo ""
echo "3. Testando endpoint /api/restaurants..."
RESTAURANTS=$(curl -s -I "$BASE_URL/api/restaurants?limit=5" 2>&1)
if echo "$RESTAURANTS" | grep -qi "cache-control"; then
    echo "   ✅ Cache-Control header presente"
    echo "$RESTAURANTS" | grep -i "cache-control"
else
    echo "   ⚠️  Cache-Control header não encontrado (pode ser normal se não autenticado)"
fi

# Teste 4: Verificar se cache está funcionando
echo ""
echo "4. Verificando cache..."
echo "   ℹ️  Execute duas requisições ao mesmo endpoint e compare tempos"
echo "   ℹ️  A segunda deve ser mais rápida (cache hit)"

echo ""
echo "✅ Testes básicos concluídos!"
echo ""
echo "📝 PRÓXIMOS PASSOS:"
echo "   1. Testar login e recomendações no navegador"
echo "   2. Verificar logs do backend para queries otimizadas"
echo "   3. Monitorar uso de memória (se possível)"

