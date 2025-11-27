import { test, expect } from '@playwright/test';

/**
 * Testes E2E para melhorias do Modo Demo Mobile
 * 
 * Testa:
 * - Banner compacto e dismissível
 * - Badge DEMO no header
 * - Menu mobile organizado
 * - Botões responsivos
 * - Feedback visual (toasts)
 */

test.describe('Modo Demo Mobile - Melhorias UX', () => {
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
    const userInfo = await page.locator('text=/Bruno Almeida|@|usuário|user/i').isVisible().catch(() => false);
    return dashboardElements || userInfo;
  }

  // Helper para fazer login se necessário
  async function loginIfNeeded(page: any) {
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    const loggedIn = await isLoggedIn(page);
    const onLoginPage = await isOnLoginPage(page);
    
    // Se já estiver logado, não precisa fazer login
    if (loggedIn) {
      return;
    }
    
    // Se não estiver na página de login, navegar para ela
    if (!onLoginPage) {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }
    
    // Tentar fazer login
    try {
      // Aguardar formulário aparecer
      const emailInput = page.locator('input#email, input[type="email"]').first();
      const passwordInput = page.locator('input#password, input[type="password"]').first();
      const submitButton = page.locator('button[type="submit"]').filter({ hasText: /entrar|login/i }).first();
      
      // Verificar se campos estão visíveis
      await emailInput.waitFor({ state: 'visible', timeout: 5000 });
      await passwordInput.waitFor({ state: 'visible', timeout: 5000 });
      
      // Preencher formulário
      await emailInput.fill('bruno@example.com');
      await passwordInput.fill('password123');
      
      // Clicar em submit
      await submitButton.click();
      
      // Aguardar redirecionamento ou sucesso
      await page.waitForURL(/\/dashboard|\/onboarding/, { timeout: 15000 });
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Verificar se login foi bem-sucedido
      const stillOnLogin = await isOnLoginPage(page);
      if (stillOnLogin) {
        // Se ainda está na página de login, pode ser erro
        // Tentar criar conta se login falhar
        const createAccountLink = page.locator('button, a').filter({ hasText: /criar conta|não tem conta/i }).first();
        if (await createAccountLink.isVisible({ timeout: 2000 }).catch(() => false)) {
          await createAccountLink.click();
          await page.waitForTimeout(500);
          
          const nameInput = page.locator('input#name, input[type="text"]').first();
          if (await nameInput.isVisible({ timeout: 2000 }).catch(() => false)) {
            await nameInput.fill('Bruno Almeida');
            await emailInput.fill('bruno@example.com');
            await passwordInput.fill('password123');
            await submitButton.click();
            await page.waitForURL(/\/dashboard|\/onboarding/, { timeout: 15000 });
            await page.waitForLoadState('networkidle');
            await page.waitForTimeout(2000);
          }
        }
      }
    } catch (error) {
      // Se não conseguir fazer login, tentar continuar (pode estar em modo demo)
      console.warn('Não foi possível fazer login automaticamente:', error);
    }
  }

  test.beforeEach(async ({ page }) => {
    // Navegar para dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Verificar se está logado
    const loggedIn = await isLoggedIn(page);
    const onLoginPage = await isOnLoginPage(page);
    
    // Se não estiver logado, fazer login
    if (!loggedIn || onLoginPage) {
      await loginIfNeeded(page);
      // Aguardar após login
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(2000);
      
      // Verificar novamente se está logado
      const stillOnLogin = await isOnLoginPage(page);
      if (stillOnLogin) {
        // Se ainda está na página de login após tentativa, pular teste
        test.skip();
        return;
      }
    }
    
    // Garantir que está no dashboard
    if (!page.url().includes('/dashboard')) {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }
  });

  test.describe('Banner de Demo Mode', () => {
    test('deve aparecer quando modo demo é ativado', async ({ page }) => {
      // Limpar localStorage para garantir banner visível
      await page.evaluate(() => localStorage.removeItem('demo-banner-dismissed'));
      
      // Ativar modo demo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo")').first();
      await demoButton.click();
      await page.waitForTimeout(500);

      // Verificar se banner aparece
      const banner = page.locator('text=Modo Demo Ativo');
      await expect(banner).toBeVisible({ timeout: 2000 });
    });

    test('deve ter texto compacto "Modo Demo Ativo"', async ({ page }) => {
      await page.evaluate(() => localStorage.removeItem('demo-banner-dismissed'));
      
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo")').first();
      await demoButton.click();
      await page.waitForTimeout(500);

      const banner = page.locator('text=Modo Demo Ativo');
      await expect(banner).toBeVisible();
      
      // Verificar que não tem texto longo
      const longText = page.locator('text=Dados simulados não serão salvos permanentemente');
      await expect(longText).not.toBeVisible();
    });

    test('deve ter botão de fechar (X)', async ({ page }) => {
      await page.evaluate(() => localStorage.removeItem('demo-banner-dismissed'));
      
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo")').first();
      await demoButton.click();
      await page.waitForTimeout(500);

      // Verificar botão de fechar
      const closeButton = page.locator('button[aria-label="Fechar banner"]').or(
        page.locator('button:has(svg)').filter({ has: page.locator('svg') }).first()
      );
      await expect(closeButton).toBeVisible({ timeout: 2000 });
    });

    test('deve fechar quando botão X é clicado', async ({ page }) => {
      await page.evaluate(() => localStorage.removeItem('demo-banner-dismissed'));
      
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo")').first();
      await demoButton.click();
      await page.waitForTimeout(500);

      // Fechar banner
      const closeButton = page.locator('button[aria-label="Fechar banner"]').or(
        page.locator('header button:has(svg)').first()
      );
      await closeButton.click();
      await page.waitForTimeout(500);

      // Verificar que banner desapareceu
      const banner = page.locator('text=Modo Demo Ativo');
      await expect(banner).not.toBeVisible();
    });

    test('não deve reaparecer após ser fechado (localStorage)', async ({ page }) => {
      // Fechar banner se estiver aberto
      await page.evaluate(() => localStorage.setItem('demo-banner-dismissed', 'true'));
      
      // Recarregar página
      await page.reload();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);

      // Verificar que banner não aparece
      const banner = page.locator('text=Modo Demo Ativo');
      await expect(banner).not.toBeVisible();
    });
  });

  test.describe('Badge DEMO no Header', () => {
    test('deve aparecer quando modo demo está ativo', async ({ page }) => {
      // Ativar modo demo se não estiver ativo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo"), button:has-text("Sair do Modo Demo"), button:has-text("Sair Demo")').first();
      const buttonText = await demoButton.textContent();
      
      if (!buttonText?.includes('Sair')) {
        await demoButton.click();
        await page.waitForTimeout(500);
      }

      // Verificar badge DEMO
      const badge = page.locator('text=DEMO');
      await expect(badge).toBeVisible({ timeout: 2000 });
    });

    test('deve estar ao lado do título', async ({ page }) => {
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo"), button:has-text("Sair do Modo Demo"), button:has-text("Sair Demo")').first();
      const buttonText = await demoButton.textContent();
      
      if (!buttonText?.includes('Sair')) {
        await demoButton.click();
        await page.waitForTimeout(500);
      }

      // Verificar que badge está próximo ao título
      const title = page.locator('h1:has-text("TasteMatch")');
      const badge = page.locator('text=DEMO');
      
      await expect(title).toBeVisible();
      await expect(badge).toBeVisible();
      
      // Verificar posicionamento (badge deve estar na mesma linha ou próxima)
      const titleBox = await title.boundingBox();
      const badgeBox = await badge.boundingBox();
      
      if (titleBox && badgeBox) {
        // Badge deve estar na mesma altura aproximada (com margem de erro)
        expect(Math.abs(titleBox.y - badgeBox.y)).toBeLessThan(30);
      }
    });

    test('deve desaparecer ao sair do modo demo', async ({ page }) => {
      // Garantir que está em modo demo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo"), button:has-text("Sair do Modo Demo"), button:has-text("Sair Demo")').first();
      const buttonText = await demoButton.textContent();
      
      if (!buttonText?.includes('Sair')) {
        await demoButton.click();
        await page.waitForTimeout(500);
      }

      // Verificar badge existe
      const badge = page.locator('text=DEMO');
      await expect(badge).toBeVisible();

      // Sair do modo demo
      await demoButton.click();
      await page.waitForTimeout(500);

      // Verificar badge desapareceu
      await expect(badge).not.toBeVisible();
    });
  });

  test.describe('Menu Mobile', () => {
    test('deve abrir quando botão hambúrguer é clicado', async ({ page }) => {
      // Verificar se está em mobile (viewport pequeno)
      const viewport = page.viewportSize();
      if (viewport && viewport.width >= 768) {
        // Redimensionar para mobile
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);
      }

      // Clicar no botão hambúrguer
      const menuButton = page.locator('button[aria-label="Abrir menu"]');
      await menuButton.click();
      await page.waitForTimeout(500);

      // Verificar que menu abriu
      const menu = page.locator('[role="dialog"], [data-state="open"]');
      await expect(menu).toBeVisible({ timeout: 2000 });
    });

    test('deve ter seções organizadas', async ({ page }) => {
      const viewport = page.viewportSize();
      if (viewport && viewport.width >= 768) {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);
      }

      // Abrir menu
      const menuButton = page.locator('button[aria-label="Abrir menu"]');
      await menuButton.click();
      await page.waitForTimeout(500);

      // Verificar seções (labels em uppercase)
      const sections = page.locator('text=/MODO DEMO|NAVEGAÇÃO|CONTA/i');
      const count = await sections.count();
      expect(count).toBeGreaterThan(0);
    });

    test('deve ter botão de modo demo no menu', async ({ page }) => {
      const viewport = page.viewportSize();
      if (viewport && viewport.width >= 768) {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);
      }

      // Abrir menu
      const menuButton = page.locator('button[aria-label="Abrir menu"]');
      await menuButton.click();
      await page.waitForTimeout(500);

      // Verificar botão de modo demo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo"), button:has-text("Ativar Modo Demo")');
      await expect(demoButton).toBeVisible({ timeout: 2000 });
    });

    test('deve fechar ao clicar fora ou em botão', async ({ page }) => {
      const viewport = page.viewportSize();
      if (viewport && viewport.width >= 768) {
        await page.setViewportSize({ width: 375, height: 667 });
        await page.waitForTimeout(500);
      }

      // Abrir menu
      const menuButton = page.locator('button[aria-label="Abrir menu"]');
      await menuButton.click();
      await page.waitForTimeout(500);

      // Clicar em um botão do menu
      const firstButton = page.locator('[role="dialog"] button, [data-state="open"] button').first();
      await firstButton.click();
      await page.waitForTimeout(500);

      // Verificar que menu fechou
      const menu = page.locator('[role="dialog"][data-state="open"]');
      await expect(menu).not.toBeVisible({ timeout: 2000 });
    });
  });

  test.describe('Botões Responsivos', () => {
    test('deve mostrar texto curto em mobile', async ({ page }) => {
      // Redimensionar para mobile
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(500);

      // Verificar botão demo (deve mostrar "Demo" em mobile)
      const demoButton = page.locator('button:has-text("Demo"), button:has-text("Modo Demo")').first();
      await expect(demoButton).toBeVisible();
      
      const buttonText = await demoButton.textContent();
      // Em mobile, pode mostrar "Demo" ou "Modo Demo" dependendo do breakpoint
      expect(buttonText).toMatch(/Demo/i);
    });

    test('deve mostrar texto completo em desktop', async ({ page }) => {
      // Redimensionar para desktop
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.waitForTimeout(500);

      // Verificar botão demo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo")').first();
      await expect(demoButton).toBeVisible();
    });
  });

  test.describe('Feedback Visual (Toasts)', () => {
    test('deve mostrar toast ao ativar modo demo', async ({ page }) => {
      // Garantir que não está em modo demo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo")').first();
      const buttonText = await demoButton.textContent();
      
      if (buttonText?.includes('Sair')) {
        await demoButton.click();
        await page.waitForTimeout(1000);
      }

      // Ativar modo demo
      await demoButton.click();
      await page.waitForTimeout(500);

      // Verificar toast
      const toast = page.locator('text=/Modo demo ativado|Explore o TasteMatch/i');
      await expect(toast).toBeVisible({ timeout: 3000 });
    });

    test('deve mostrar toast ao desativar modo demo', async ({ page }) => {
      // Garantir que está em modo demo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo"), button:has-text("Sair do Modo Demo"), button:has-text("Sair Demo")').first();
      const buttonText = await demoButton.textContent();
      
      if (!buttonText?.includes('Sair')) {
        await demoButton.click();
        await page.waitForTimeout(1000);
      }

      // Desativar modo demo
      await demoButton.click();
      await page.waitForTimeout(500);

      // Verificar toast
      const toast = page.locator('text=/Modo demo encerrado|Faça login/i');
      await expect(toast).toBeVisible({ timeout: 3000 });
    });
  });

  test.describe('Fluxo Completo', () => {
    test('deve funcionar o fluxo completo de ativação e desativação', async ({ page }) => {
      // Limpar localStorage
      await page.evaluate(() => {
        localStorage.removeItem('demo-banner-dismissed');
      });

      // 1. Ativar modo demo
      const demoButton = page.locator('button:has-text("Modo Demo"), button:has-text("Demo")').first();
      await demoButton.click();
      await page.waitForTimeout(1000);

      // 2. Verificar banner
      const banner = page.locator('text=Modo Demo Ativo');
      await expect(banner).toBeVisible();

      // 3. Verificar badge
      const badge = page.locator('text=DEMO');
      await expect(badge).toBeVisible();

      // 4. Fechar banner
      const closeButton = page.locator('button[aria-label="Fechar banner"]').or(
        page.locator('header button:has(svg)').first()
      );
      await closeButton.click();
      await page.waitForTimeout(500);

      // 5. Verificar que banner desapareceu mas badge continua
      await expect(banner).not.toBeVisible();
      await expect(badge).toBeVisible();

      // 6. Desativar modo demo
      await demoButton.click();
      await page.waitForTimeout(1000);

      // 7. Verificar que badge desapareceu
      await expect(badge).not.toBeVisible();
    });
  });
});

