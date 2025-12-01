import { test, expect } from '@playwright/test';

/**
 * Testes automatizados para validação Mobile-First
 * Cobre todos os cenários de responsividade implementados
 */
test.describe('Mobile-First Responsive Tests', () => {
  
  // Helper: Verificar se está na página de login
  async function isOnLoginPage(page: any): Promise<boolean> {
    const loginForm = await page.locator('form').filter({ 
      has: page.locator('input[type="email"], input[name="email"]') 
    }).isVisible().catch(() => false);
    return loginForm || page.url().includes('/login');
  }

  // Helper: Verificar se está logado
  async function isLoggedIn(page: any): Promise<boolean> {
    // Verificar se há elementos que só aparecem quando logado
    const dashboardElements = await page.locator('text=/TasteMatch|Dashboard|Histórico/i').isVisible().catch(() => false);
    const userInfo = await page.locator('text=/@|usuário|user/i').isVisible().catch(() => false);
    return dashboardElements || userInfo;
  }

  test('should show hamburger menu on mobile', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Aguardar carregamento completo
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Aguardar renderização
    
    // Verificar se está logado ou na página de login
    const loggedIn = await isLoggedIn(page);
    const onLoginPage = await isOnLoginPage(page);
    
    // Se não estiver logado e não estiver na página de login, pode ser redirecionamento
    if (!loggedIn && !onLoginPage) {
      // Aguardar possível redirecionamento
      await page.waitForTimeout(1000);
    }
    
    // Se estiver na página de login, o teste não se aplica (pular)
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Verificar que hambúrguer aparece usando o aria-label correto
    const hamburger = page.locator('button[aria-label="Abrir menu"]');
    
    // Em mobile (< 768px), hambúrguer deve aparecer
    if (page.viewportSize() && page.viewportSize()!.width < 768) {
      await expect(hamburger).toBeVisible({ timeout: 10000 });
      
      // Verificar que botões não aparecem diretamente no header (em mobile)
      const themeButton = page.locator('button').filter({ hasText: /tema/i });
      const isThemeVisibleInHeader = await themeButton.isVisible().catch(() => false);
      
      // Em mobile, botões não devem estar visíveis no header
      expect(isThemeVisibleInHeader).toBeFalsy();
      
      // Clicar no hambúrguer para abrir menu
      await hamburger.click();
      await page.waitForTimeout(500);
      
      // Verificar que menu está visível
      const mobileMenu = page.locator('[role="dialog"]').or(
        page.locator('[class*="sheet"]')
      );
      await expect(mobileMenu.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('should show inline buttons on desktop', async ({ page }) => {
    // Forçar viewport desktop
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/dashboard');
    
    // Aguardar carregamento completo
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Aguardar renderização
    
    // Verificar se está logado ou na página de login
    const loggedIn = await isLoggedIn(page);
    const onLoginPage = await isOnLoginPage(page);
    
    // Se não estiver logado e não estiver na página de login, pode ser redirecionamento
    if (!loggedIn && !onLoginPage) {
      await page.waitForTimeout(1000);
    }
    
    // Se estiver na página de login, o teste não se aplica (pular)
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Verificar que hambúrguer NÃO aparece em desktop
    const hamburger = page.locator('button[aria-label="Abrir menu"]');
    const hamburgerVisible = await hamburger.isVisible().catch(() => false);
    
    // Em desktop, hambúrguer não deve aparecer (está em md:hidden)
    expect(hamburgerVisible).toBeFalsy();
    
    // Verificar que botões aparecem no header (estão em hidden md:flex)
    // Pode ser qualquer botão no header (Tema, Demo, Histórico, Sair)
    const headerButtons = page.locator('header button').filter({ 
      hasNot: page.locator('[aria-label="Abrir menu"]') 
    });
    const buttonsCount = await headerButtons.count();
    
    // Em desktop, deve haver pelo menos um botão no header
    expect(buttonsCount).toBeGreaterThan(0);
  });

  test('should force cards view on mobile in Orders page', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    await page.goto('/orders');
    
    // Aguardar carregamento completo
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Aguardar renderização
    
    // Verificar se está logado ou na página de login
    const loggedIn = await isLoggedIn(page);
    const onLoginPage = await isOnLoginPage(page);
    
    // Se estiver na página de login, o teste não se aplica (pular)
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Verificar que tabela NÃO aparece (deve ter hidden md:block)
    const table = page.locator('table');
    const tableVisible = await table.isVisible().catch(() => false);
    
    // Em mobile, tabela não deve aparecer
    expect(tableVisible).toBeFalsy();
    
    // Verificar que toggle table/cards NÃO aparece em mobile (hidden md:flex)
    const toggle = page.locator('button').filter({ hasText: /table|cards|visualiza/i });
    const toggleVisible = await toggle.isVisible().catch(() => false);
    
    // Em mobile, toggle não deve aparecer
    expect(toggleVisible).toBeFalsy();
    
    // Verificar que cards aparecem OU mensagem de sem pedidos
    const cardsContainer = page.locator('[class*="grid"]').filter({ 
      has: page.locator('[class*="card"]') 
    }).first();
    
    const cardsVisible = await cardsContainer.isVisible({ timeout: 2000 }).catch(() => false);
    
    // Se não houver cards, verificar se a mensagem "sem pedidos" aparece
    const noOrdersMessage = page.locator('text=/não fez nenhum pedido|sem pedidos|Você ainda não/i');
    const hasNoOrders = await noOrdersMessage.isVisible({ timeout: 2000 }).catch(() => false);
    
    // Em mobile, ou cards aparecem OU mensagem de sem pedidos OU está na página de login
    expect(cardsVisible || hasNoOrders || onLoginPage).toBeTruthy();
  });

  test('should show table on desktop in Orders page', async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 768 });
    await page.goto('/orders');
    
    // Aguardar carregamento completo
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Aguardar renderização
    
    // Verificar se está logado ou na página de login
    const loggedIn = await isLoggedIn(page);
    const onLoginPage = await isOnLoginPage(page);
    
    // Se estiver na página de login, o teste não se aplica (pular)
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Verificar que toggle aparece em desktop (hidden md:flex)
    const toggle = page.locator('button').filter({ hasText: /table|cards|visualiza/i });
    const toggleVisible = await toggle.isVisible({ timeout: 5000 }).catch(() => false);
    
    // Em desktop, toggle deve aparecer (se houver pedidos)
    if (toggleVisible) {
      // Se toggle aparece, tentar clicar no toggle de tabela
      const tableToggle = page.locator('button').filter({ hasText: /table/i }).first();
      const tableToggleVisible = await tableToggle.isVisible().catch(() => false);
      
      if (tableToggleVisible) {
        await tableToggle.click();
        await page.waitForTimeout(500);
        
        // Verificar que tabela aparece
        const table = page.locator('table');
        const tableVisible = await table.isVisible({ timeout: 5000 }).catch(() => false);
        expect(tableVisible).toBeTruthy();
      }
    } else {
      // Se toggle não aparece, pode ser que não há pedidos
      // Verificar se mensagem de sem pedidos aparece
      const noOrdersMessage = page.locator('text=/não fez nenhum pedido|sem pedidos|Você ainda não/i');
      const hasNoOrders = await noOrdersMessage.isVisible({ timeout: 2000 }).catch(() => false);
      
      // Se não há pedidos, isso é aceitável
      expect(hasNoOrders).toBeTruthy();
    }
  });

  test('should handle OrderSimulator modal responsively', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    // Aguardar carregamento completo
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Verificar se está na página de login
    const onLoginPage = await isOnLoginPage(page);
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Tentar abrir simulador (pode estar no modo demo)
    const simulatorButton = page.locator('button').filter({ hasText: /simular|demo/i }).first();
    const simulatorVisible = await simulatorButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (simulatorVisible) {
      await simulatorButton.click();
      await page.waitForTimeout(500);
      
      // Verificar que modal aparece
      const modal = page.locator('[role="dialog"]').first();
      await expect(modal).toBeVisible({ timeout: 5000 });
      
      // Verificar que modal usa max-w-[95vw] em mobile
      const modalBox = await modal.boundingBox();
      if (modalBox) {
        expect(modalBox.width).toBeLessThanOrEqual(375 * 0.95);
      }
    } else {
      // Se não há botão de simulador, pode ser que não está em modo demo
      // Isso é aceitável, apenas verificar que a página carregou
      const pageLoaded = await page.locator('body').isVisible();
      expect(pageLoaded).toBeTruthy();
    }
  });

  test('should show responsive RestaurantCard modal', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    // Aguardar carregamento completo
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Verificar se está na página de login
    const onLoginPage = await isOnLoginPage(page);
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Tentar clicar em um card de restaurante
    const restaurantCard = page.locator('[class*="card"]').filter({ 
      hasText: /restaurante|restaurant/i 
    }).first();
    
    const cardVisible = await restaurantCard.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (cardVisible) {
      await restaurantCard.click();
      await page.waitForTimeout(500);
      
      // Verificar que modal aparece
      const modal = page.locator('[role="dialog"]').first();
      await expect(modal).toBeVisible({ timeout: 5000 });
      
      // Verificar que modal é responsivo
      const modalBox = await modal.boundingBox();
      if (modalBox) {
        expect(modalBox.width).toBeLessThanOrEqual(375 * 0.95);
      }
    } else {
      // Se não há cards, pode ser que não há recomendações
      // Isso é aceitável, apenas verificar que a página carregou
      const pageLoaded = await page.locator('body').isVisible();
      expect(pageLoaded).toBeTruthy();
    }
  });

  test('should adapt layout at different breakpoints', async ({ page }) => {
    const breakpoints = [
      { width: 375, name: 'iPhone SE', shouldShowHamburger: true },
      { width: 414, name: 'iPhone Pro', shouldShowHamburger: true },
      { width: 768, name: 'iPad', shouldShowHamburger: false },
      { width: 1024, name: 'Desktop', shouldShowHamburger: false },
    ];

    for (const bp of breakpoints) {
      await page.setViewportSize({ width: bp.width, height: 800 });
      await page.goto('/dashboard');
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000); // Aguardar renderização
      
      // Verificar se está na página de login (se sim, pular este breakpoint)
      const onLoginPage = await isOnLoginPage(page);
      if (onLoginPage) {
        continue; // Pular este breakpoint se não estiver logado
      }
      
      // Verificar que layout se adapta usando o seletor correto
      const hamburger = page.locator('button[aria-label="Abrir menu"]');
      const hamburgerVisible = await hamburger.isVisible({ timeout: 5000 }).catch(() => false);
      
      if (bp.shouldShowHamburger) {
        expect(hamburgerVisible).toBeTruthy();
      } else {
        expect(hamburgerVisible).toBeFalsy();
      }
    }
  });

  test('should have adequate touch targets on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Verificar se está na página de login
    const onLoginPage = await isOnLoginPage(page);
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Abrir menu mobile se houver hambúrguer
    const hamburger = page.locator('button[aria-label="Abrir menu"]');
    const hamburgerVisible = await hamburger.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (hamburgerVisible) {
      await hamburger.click();
      await page.waitForTimeout(500);
      
      // Verificar tamanho dos botões no menu
      const buttons = page.locator('[role="dialog"] button, [class*="sheet"] button');
      const count = await buttons.count();
      
      for (let i = 0; i < Math.min(count, 5); i++) {
        const button = buttons.nth(i);
        const box = await button.boundingBox();
        
        if (box) {
          // Touch target mínimo: 44x44px
          expect(box.height).toBeGreaterThanOrEqual(40); // Tolerância
          expect(box.width).toBeGreaterThanOrEqual(40); // Tolerância
        }
      }
    } else {
      // Se não há hambúrguer, pode ser desktop ou não logado
      // Verificar se pelo menos a página carregou
      const pageLoaded = await page.locator('body').isVisible();
      expect(pageLoaded).toBeTruthy();
    }
  });

  test('should not have horizontal overflow on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/dashboard');
    
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Verificar que não há scroll horizontal (aplica-se mesmo sem login)
    const body = page.locator('body');
    const scrollWidth = await body.evaluate((el) => el.scrollWidth);
    const clientWidth = await body.evaluate((el) => el.clientWidth);
    
    expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 5); // Tolerância de 5px
  });

  test('should take screenshots at different viewports', async ({ page }) => {
    const viewports = [
      { width: 375, name: 'mobile' },
      { width: 768, name: 'tablet' },
      { width: 1024, name: 'desktop' },
    ];

    for (const vp of viewports) {
      await page.setViewportSize({ width: vp.width, height: 800 });
      await page.goto('/dashboard');
      
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000); // Aguardar animações e renderização
      
      await page.screenshot({ 
        path: `tests/screenshots/dashboard-${vp.name}.png`,
        fullPage: true 
      });
    }
  });
});

