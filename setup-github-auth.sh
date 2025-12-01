#!/bin/bash

# Script para configurar autenticação GitHub CLI
# Execute: bash setup-github-auth.sh

echo "🔐 Configuração de Autenticação GitHub CLI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar se gh está instalado
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI não está instalado."
    echo "   Instale com: sudo apt install gh"
    exit 1
fi

echo "✅ GitHub CLI encontrado"
echo ""

# Verificar status atual
echo "📊 Status atual da autenticação:"
gh auth status 2>&1 | head -5
echo ""

# Fazer logout se necessário
read -p "Deseja fazer logout da conta atual? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "🔓 Fazendo logout..."
    gh auth logout -h github.com 2>/dev/null || true
    echo "✅ Logout concluído"
    echo ""
fi

echo "🚀 Iniciando processo de autenticação..."
echo ""
echo "📋 INSTRUÇÕES:"
echo "  1. Quando perguntar sobre protocolo, escolha: HTTPS (use setas e Enter)"
echo "  2. Quando perguntar sobre autenticação, escolha: Login with a web browser"
echo "  3. Um código aparecerá - copie-o"
echo "  4. Um navegador abrirá automaticamente"
echo "  5. Cole o código e autorize o acesso"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Executar login
gh auth login -h github.com

# Verificar se autenticação foi bem-sucedida
if gh auth status &>/dev/null; then
    echo ""
    echo "✅ Autenticação bem-sucedida!"
    echo ""
    echo "🔧 Configurando Git para usar GitHub CLI..."
    gh auth setup-git
    
    echo ""
    echo "✅ Configuração concluída!"
    echo ""
    echo "🎯 Agora você pode fazer push:"
    echo "   git push origin feature/mobile-first-refactor"
else
    echo ""
    echo "❌ Autenticação falhou. Tente novamente."
    exit 1
fi

