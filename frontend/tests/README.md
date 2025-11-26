# Testes E2E - Mobile-First

Este diretório contém testes automatizados usando Playwright para validar a implementação mobile-first do TasteMatch.

## 📋 Estrutura

```
tests/
├── e2e/
│   └── mobile-first.spec.ts    # Testes de responsividade mobile-first
└── screenshots/                  # Screenshots gerados pelos testes
```

## 🚀 Como Executar

### Instalar navegadores (primeira vez)
```bash
npm run test:e2e:install
```

### Executar todos os testes
```bash
npm run test:e2e
```

### Executar apenas testes mobile
```bash
npm run test:e2e:mobile
```

### Executar apenas testes desktop
```bash
npm run test:e2e:desktop
```

### Executar com UI interativa
```bash
npm run test:e2e:ui
```

### Ver relatório HTML
```bash
npm run test:e2e:report
```

## 🧪 Testes Implementados

### 1. Menu Hambúrguer em Mobile
- Valida que o menu hambúrguer aparece em mobile
- Verifica que botões estão no menu, não no header

### 2. Header Desktop
- Valida que botões aparecem inline em desktop
- Verifica que hambúrguer não aparece

### 3. Cards Forçados em Orders (Mobile)
- Valida que apenas cards aparecem em mobile
- Verifica que tabela está oculta
- Verifica que toggle não aparece

### 4. Tabela em Desktop (Orders)
- Valida que toggle aparece em desktop
- Verifica que tabela aparece quando selecionada

### 5. OrderSimulator Modal Responsivo
- Valida que modal usa `max-w-[95vw]` em mobile
- Verifica que terminal usa `dvh`

### 6. RestaurantCard Modal Responsivo
- Valida que modal é responsivo
- Verifica grid interno adapta para mobile

### 7. Breakpoints Intermediários
- Testa em 375px, 414px, 768px, 1024px
- Valida transições entre breakpoints

### 8. Touch Targets
- Valida que botões têm tamanho mínimo de 44x44px
- Verifica acessibilidade em mobile

### 9. Sem Overflow Horizontal
- Valida que não há scroll horizontal em mobile

### 10. Screenshots Comparativos
- Gera screenshots em diferentes viewports
- Útil para comparação visual

## 📱 Viewports Testados

- **Mobile iPhone SE**: 375x667
- **Mobile iPhone 12 Pro**: 390x844
- **Mobile Android (Pixel 5)**: 393x851
- **Tablet iPad**: 1024x1366
- **Desktop Chrome**: 1280x720

## 🔧 Configuração

A configuração está em `playwright.config.ts`:

- **Base URL**: `http://localhost:5173`
- **Web Server**: Inicia automaticamente `npm run dev`
- **Retries**: 2 em CI, 0 localmente
- **Screenshots**: Apenas em falhas
- **Videos**: Apenas em falhas

## 📝 Notas

- Os testes assumem que o backend está rodando
- Login pode ser necessário (ajustar conforme necessário)
- Alguns testes podem precisar de dados no banco (pedidos, restaurantes)

## 🐛 Troubleshooting

### Erro: "Browser not found"
```bash
npm run test:e2e:install
```

### Erro: "Port 5173 already in use"
- Pare o servidor de desenvolvimento manual
- Ou ajuste a porta no `playwright.config.ts`

### Testes falhando por timing
- Aumentar `timeout` no `playwright.config.ts`
- Adicionar `await page.waitForLoadState('networkidle')`

## 📊 Relatórios

Após executar os testes, um relatório HTML é gerado em:
```
playwright-report/
```

Para visualizar:
```bash
npm run test:e2e:report
```

