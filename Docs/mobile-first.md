# Plano de Ação: Mobile-First Responsive Refactor (ATUALIZADO)

## Objetivo
Transformar a aplicação TasteMatch para ser verdadeiramente mobile-first, garantindo excelente experiência em dispositivos móveis enquanto mantém funcionalidade desktop, com capacidade de reversão completa se necessário.

## Estratégia de Reversão

### Antes de Iniciar
1. Criar branch separada: `git checkout -b feature/mobile-first-refactor`
2. **IMPORTANTE:** Adicionar todos os arquivos (incluindo novos): `git add .`
3. Fazer commit do estado atual: `git commit -m "checkpoint: estado antes do refactor mobile-first"`
4. Criar tag de backup: `git tag -a mobile-first-checkpoint -m "Backup antes do refactor mobile-first"`

**Nota:** O uso de `git add .` antes do commit garante que arquivos novos (não rastreados) também sejam incluídos no backup.

### Se Algo Der Errado
```bash
# Opção 1: Voltar para o commit anterior
git reset --hard mobile-first-checkpoint

# Opção 2: Voltar para a branch principal
git checkout main
# Ou fazer merge seletivo dos arquivos que funcionaram

# Opção 3: Reverter apenas um arquivo específico
git checkout mobile-first-checkpoint -- frontend/src/pages/Dashboard.tsx
```

## ⚠️ Melhorias Críticas Aplicadas (Baseado em Análise)

### 1. Pattern de Composição (Evitar Prop Drilling)
**Problema:** Passar muitas props individuais torna o componente difícil de manter.
**Solução:** Usar Pattern de Composição com slots para ações.

### 2. Tabelas em Mobile (Forçar Cards)
**Problema:** Tabelas são difíceis de usar em mobile.
**Solução:** Forçar visualização de Cards automaticamente em mobile.

### 3. Viewport Dinâmico (dvh)
**Problema:** `100vh` quebra quando teclado virtual abre.
**Solução:** Usar `dvh` (Dynamic Viewport Height) para altura dinâmica.

### 4. Reaproveitar shadcn/ui
**Problema:** Criar menu do zero é trabalhoso e propenso a bugs.
**Solução:** Usar componente `Sheet` do shadcn/ui se disponível.

## Fase 1: Criar Componente Header Reutilizável

### 1.1 Criar Componente Base Header (COM PATTERN DE COMPOSIÇÃO)
**Arquivo:** `frontend/src/components/layout/AppHeader.tsx` (NOVO)

**Funcionalidades:**
- Menu hambúrguer para mobile (Menu icon do lucide-react)
- **Pattern de Composição:** Aceitar `actions` como slot em vez de props individuais
- Layout responsivo que:
  - Desktop: mostra todos os botões em linha
  - Mobile: mostra logo + hambúrguer, menu desliza de lado ou dropdown

**API do Componente (Pattern de Composição com `children`):**
```tsx
// Opção 1: Usar children diretamente (mais React-like, recomendado)
<AppHeader title="Dashboard" subtitle="Recomendações personalizadas">
  <Button onClick={toggleDemo}>Demo Mode</Button>
  <Button variant="outline">Export</Button>
</AppHeader>

// Opção 2: Usar prop actions (alternativa)
<AppHeader 
  title="Dashboard"
  subtitle="Recomendações personalizadas"
  actions={
    <>
      <Button onClick={toggleDemo}>Demo Mode</Button>
      <Button variant="outline">Export</Button>
    </>
  }
/>
```

**Recomendação:** Usar `children` é mais flexível e idiomático em React. O componente decide automaticamente onde renderizar (menu mobile ou header desktop).

**Breakpoints:**
- Mobile (< md): Menu hambúrguer + drawer/dropdown
- Desktop (>= md): Menu completo em linha

### 1.2 Verificar/Criar Componente Sheet (shadcn/ui)
**Arquivo:** `frontend/src/components/ui/sheet.tsx` (VERIFICAR SE EXISTE)

**Ação:**
1. Verificar se o componente Sheet já existe em `frontend/src/components/ui/`
2. Se não existir, instalar via shadcn/ui: `npx shadcn-ui@latest add sheet`
3. Se não for possível usar Sheet, criar `MobileMenu.tsx` simples usando Dialog existente

**Vantagens do Sheet:**
- Acessibilidade já implementada
- Overlay automático
- Foco de teclado gerenciado
- Animações suaves
- Botão de fechar automático

**Funcionalidades do Menu Mobile:**
- Drawer/Sidebar que desliza da direita/esquerda
- Lista de ações disponíveis (recebidas via `children` ou prop `actions`)
- Overlay escuro quando aberto
- Animações suaves de entrada/saída
- Fechamento ao clicar no overlay ou botão fechar
- **UX:** Posicionar botões de ação na parte inferior do drawer (mais fácil de alcançar com polegar)
- **Scroll:** Adicionar `overscroll-behavior-y: none` no body quando menu aberto para evitar scroll da página de fundo

## Fase 2: Atualizar Dashboard

### 2.1 Refatorar Header do Dashboard
**Arquivo:** `frontend/src/pages/Dashboard.tsx`

**Mudanças:**
- Substituir header inline pelo componente `AppHeader`
- **Usar Pattern de Composição:** Passar `actions` como slot em vez de props individuais
- Botões ficam no menu mobile quando em telas pequenas

**Exemplo de Uso (Recomendado - usando children):**
```tsx
<AppHeader
  title="TasteMatch"
  subtitle="Recomendações personalizadas para você"
>
  <Button onClick={() => setIsDemoMode(!isDemoMode)}>
    {isDemoMode ? <X className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
    {isDemoMode ? 'Sair do Modo Demo' : 'Modo Demo'}
  </Button>
  {isDemoMode && (
    <Button onClick={handleResetSimulation}>Resetar</Button>
  )}
  <Link to="/orders">
    <Button variant="outline">Histórico</Button>
  </Link>
  <Button onClick={logout}>Sair</Button>
</AppHeader>
```

**Nota:** O AppHeader renderiza os `children` automaticamente no menu mobile (quando pequeno) ou na barra superior (quando desktop).

**Ajustes Mobile-First:**
- Header: Stack vertical em mobile, horizontal em desktop
- Título: Texto menor em mobile (`text-xl md:text-2xl`)
- Botões na seção "Restaurantes Recomendados": Stack vertical em mobile

**Linhas a modificar:**
- Linha 48-115: Substituir header por `<AppHeader />`
- Linha 140-165: Ajustar layout para stack em mobile (`flex-col md:flex-row`)

### 2.2 Ajustar Layout do Modo Demo
**Arquivo:** `frontend/src/pages/Dashboard.tsx`

**Mudanças:**
- Grid do painel LLM + Terminal: garantir stack vertical em mobile
- Linha 121: Já está `grid-cols-1 lg:grid-cols-4` (ok, mas verificar)

## Fase 3: Atualizar Orders Page

### 3.1 Refatorar Header do Orders
**Arquivo:** `frontend/src/pages/Orders.tsx`

**Mudanças:**
- Substituir header inline pelo componente `AppHeader`
- Usar Pattern de Composição para ações
- Linha 30-54: Substituir por `<AppHeader />`

### 3.2 Ajustar Controles de Visualização (FORÇAR CARDS EM MOBILE)
**Arquivo:** `frontend/src/pages/Orders.tsx`

**Mudanças CRÍTICAS:**
- **Forçar Cards em Mobile:** Não depender do usuário escolher visualização
  - Tabela: `hidden md:block` (ocultar em mobile, mostrar em desktop)
  - Cards: `block md:hidden` (mostrar em mobile, ocultar em desktop)
- Linha 59-95: Layout `flex-col md:flex-row` para stack em mobile
- Botões de visualização (table/cards): Manter apenas para desktop (`hidden md:flex`)

**Código de Exemplo:**
```tsx
{/* Desktop: Mostrar toggle de visualização */}
<div className="hidden md:flex items-center gap-2">
  <Button onClick={() => setViewMode('table')}>Table</Button>
  <Button onClick={() => setViewMode('cards')}>Cards</Button>
</div>

{/* Conteúdo: Tabela só em desktop, Cards sempre visíveis em mobile */}
{viewMode === 'table' ? (
  <div className="hidden md:block">
    <OrderTable orders={orders} />
  </div>
) : null}

<div className="block md:hidden">
  <div className="grid grid-cols-1 gap-6">
    {orders.map((order) => (
      <OrderCard key={order.id} order={order} />
    ))}
  </div>
</div>

{/* Desktop: Cards opcionais */}
{viewMode === 'cards' && (
  <div className="hidden md:grid grid-cols-2 lg:grid-cols-3 gap-6">
    {orders.map((order) => (
      <OrderCard key={order.id} order={order} />
    ))}
  </div>
)}
```

## Fase 4: Ajustar Componentes Específicos

### 4.1 OrderSimulator (VIEWPORT DINÂMICO)
**Arquivo:** `frontend/src/components/features/OrderSimulator.tsx`

**Ajustes:**
- Dialog: Garantir full-width em mobile (`max-w-[95vw]` em mobile)
- Grid de personas: Já está `grid-cols-1 md:grid-cols-3` (ok)
- **Terminal de AI:** Usar `dvh` para altura dinâmica
  - Mudar de `h-[200px]` ou `h-screen` para `h-[60dvh] md:h-[600px]`
  - Isso evita que o teclado virtual cubra o terminal

**Código de Exemplo:**
```tsx
// ANTES (problema com teclado):
<div className="h-[200px] overflow-y-auto">

// DEPOIS (funciona com teclado):
<div className="h-[60dvh] md:h-[600px] overflow-y-auto">
```

### 4.2 RestaurantCard
**Arquivo:** `frontend/src/components/features/RestaurantCard.tsx`

**Ajustes:**
- Dialog modal: Responsivo para mobile
- Grid no modal (linha 120): Ajustar para stack em mobile (`grid-cols-1 md:grid-cols-2`)

### 4.3 LLMInsightPanel
**Arquivo:** `frontend/src/components/features/LLMInsightPanel.tsx`

**Ajustes:**
- Textos: Tamanhos responsivos (`text-xs md:text-sm`)
- Badges: Stack em mobile se necessário

## Fase 5: Ajustes Finais e Testes

### 5.1 Login Page
**Arquivo:** `frontend/src/pages/Login.tsx`

**Ajustes:**
- Card: Já tem `w-full max-w-md` (ok)
- Padding: Garantir espaçamento adequado em mobile

### 5.2 Testes de Responsividade
**Breakpoints a testar:**
- Mobile: 375px, 414px (iPhone)
- Tablet: 768px
- Desktop: 1024px, 1280px

**Navegadores:**
- Chrome DevTools mobile
- Firefox mobile view
- Safari mobile (se disponível)

**Testes Específicos por Dispositivo:**
- ✅ **iPhone SE (375px):** Verificar se botões não quebram linha indevidamente
- ✅ **Android Grande (Pixel/Samsung - 414px):** Testar abertura do teclado no Terminal AI
- ✅ **iPad/Tablet (768px):** Verificar transição entre menu hambúrguer e menu inline
- ✅ **Orientação Landscape:** Girar o celular e verificar se o menu funciona corretamente
- ✅ Menu hambúrguer abre e fecha corretamente
- ✅ Teclado virtual não quebra layout
- ✅ Tabela não aparece em mobile (apenas cards)
- ✅ Touch targets têm no mínimo 44x44px
- ✅ Não há overflow horizontal

### 5.3 Ajustes de Performance e UX
- Verificar se animações do menu mobile não causam lag
- Testar abertura/fechamento do drawer
- Verificar renderização condicional (não renderizar componentes desnecessários)
- **Overscroll Behavior:** Implementar `overscroll-behavior-y: none` quando menu mobile está aberto
- **Botões no Drawer:** Posicionar ações principais na parte inferior do drawer para melhor alcance com polegar

## Estrutura de Arquivos

### Arquivos Novos
- `frontend/src/components/layout/AppHeader.tsx`
- `frontend/src/components/ui/sheet.tsx` (se não existir - verificar primeiro)
- `frontend/src/components/layout/index.ts` (exportações)

### Arquivos Modificados
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Orders.tsx`
- `frontend/src/components/features/OrderSimulator.tsx`
- `frontend/src/components/features/RestaurantCard.tsx`
- `frontend/src/components/features/LLMInsightPanel.tsx`
- `frontend/src/pages/Login.tsx`

## Checklist de Tarefas

- [ ] **Backup:** Criar branch e backup do estado atual (`git add .` antes do commit)
- [ ] **Verificar Sheet:** Verificar se `sheet.tsx` existe, se não, instalar via shadcn/ui
- [ ] **AppHeader:** Criar componente AppHeader.tsx com Pattern de Composição (slots)
- [ ] **MobileMenu:** Usar Sheet do shadcn/ui ou criar wrapper simples
- [ ] **Dashboard Header:** Refatorar Dashboard.tsx para usar AppHeader com composição
- [ ] **Orders Header:** Refatorar Orders.tsx para usar AppHeader com composição
- [ ] **Orders Table:** Forçar Cards em mobile, ocultar tabela automaticamente
- [ ] **OrderSimulator:** Ajustar terminal para usar `dvh` (altura dinâmica)
- [ ] **RestaurantCard:** Ajustar modal para responsividade mobile
- [ ] **LLMInsightPanel:** Ajustar textos e layouts responsivos
- [ ] **Testes:** Testar responsividade em múltiplos breakpoints e navegadores
- [ ] **Polimento:** Ajustes finais e polimento (animações, touch targets, performance)

## Critérios de Sucesso

1. ✅ Header funcional em mobile com menu hambúrguer
2. ✅ Todos os botões acessíveis em mobile via menu
3. ✅ Layouts stack corretamente em mobile (< 768px)
4. ✅ Textos legíveis e botões com tamanho adequado para toque (mínimo 44x44px)
5. ✅ Modais e dialogs funcionam bem em mobile
6. ✅ Não há overflow horizontal
7. ✅ Experiência desktop mantida intacta
8. ✅ **Tabela não aparece em mobile** (apenas cards)
9. ✅ **Teclado virtual não quebra layout** (usando dvh)
10. ✅ **AppHeader usa Pattern de Composição** (não prop drilling)

## Pontos de Rollback

**Rollback Parcial (por fase):**
- Fase 1: Reverter apenas componentes novos, manter páginas como estão
- Fase 2-3: Reverter apenas mudanças nas páginas específicas
- Fase 4-5: Ajustes menores, reversão simples

**Rollback Total:**
- Git reset para tag `mobile-first-checkpoint`
- Ou fazer merge seletivo dos arquivos que funcionaram

## Notas Técnicas

- **Breakpoints Tailwind:** `sm:`, `md:`, `lg:`, `xl:`
- **Mobile-first:** Estilos base para mobile, depois adicionar `md:`, `lg:`
- **Menu hambúrguer:** Usar ícone `Menu` do lucide-react
- **Sheet Component:** Usar componente Sheet do shadcn/ui (se disponível) em vez de criar do zero
- **Pattern de Composição:** Evitar prop drilling, usar slots (`actions` como children)
- **Viewport Dinâmico:** Usar `dvh` ao invés de `vh` para altura (evita problemas com teclado)
- **Transições:** Usar Tailwind `transition` e `duration` classes
- **Touch targets:** Mínimo 44x44px (padrão iOS/Android)
- **Tabelas em Mobile:** Sempre forçar Cards, nunca mostrar tabela (usar `hidden md:block`)
- **Overscroll Behavior:** Adicionar `overscroll-behavior-y: none` no body quando menu mobile estiver aberto para evitar rolar a página de fundo
- **Unidades CSS:** Preferir `rem` para fontes e paddings. Usar `dvh` para alturas que ocupam a tela toda
- **Pattern de Composição:** Usar `children` diretamente é mais idiomático em React do que prop `actions`

## Comandos Git para Reversão

```bash
# Antes de começar - criar backup (CORRIGIDO)
git checkout -b feature/mobile-first-refactor
git add .  # ADICIONAR ESTA LINHA - importante para arquivos novos
git commit -m "checkpoint: estado antes do refactor mobile-first"
git tag -a mobile-first-checkpoint -m "Backup antes do refactor mobile-first"

# Se precisar reverter tudo
git reset --hard mobile-first-checkpoint

# Se precisar reverter apenas um arquivo
git checkout mobile-first-checkpoint -- frontend/src/pages/Dashboard.tsx

# Se tudo funcionar bem, fazer merge
git checkout main
git merge feature/mobile-first-refactor
```

## Melhorias Opcionais (Futuro)

### Bottom Navigation Bar (Opcional)
Para uma experiência ainda melhor em mobile, considerar:
- Bottom Navigation Bar fixa (como Instagram/Spotify) apenas para mobile
- Contém ações principais (Dashboard, Pedidos, etc.)
- Header fica apenas com Logo e Configurações
- **Nota:** Complexo para implementar agora, manter hambúrguer por enquanto

### Tipografia Fluida (Opcional)
- Configurar `tailwind.config.js` para tamanhos base que funcionem bem em ambos
- Ou usar CSS `clamp()` para tipografia fluida
- **Nota:** Seguir padrão `md:` é mais seguro para refactor rápido

## Riscos Identificados e Mitigados

### ✅ Risco 1: Prop Drilling
**Mitigação:** Pattern de Composição implementado (slots)

### ✅ Risco 2: Tabelas em Mobile
**Mitigação:** Forçar Cards automaticamente, ocultar tabela

### ✅ Risco 3: Teclado Virtual Quebrando Layout
**Mitigação:** Usar `dvh` ao invés de `vh`

### ✅ Risco 4: Componente Menu Complexo
**Mitigação:** Reaproveitar Sheet do shadcn/ui

### ✅ Risco 5: Perda de Arquivos no Backup
**Mitigação:** Usar `git add .` antes do commit
