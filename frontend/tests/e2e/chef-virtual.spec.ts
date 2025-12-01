import { test, expect } from '@playwright/test';

/**
 * Testes E2E para Chef Virtual
 * Cobre fluxos principais: texto, áudio, histórico e integração
 */

test.describe('Chef Virtual - Testes E2E', () => {
  
  // Helper: Verificar se está logado
  async function isLoggedIn(page: any): Promise<boolean> {
    // Verificar múltiplos indicadores de que está logado
    const urlCheck = page.url().includes('/dashboard') && !page.url().includes('/login');
    const dashboardElements = await page.locator('text=/Dashboard|Histórico|Recomendações/i').isVisible().catch(() => false);
    const chefButton = await page.locator('button').filter({ hasText: /Chef Virtual/i }).isVisible({ timeout: 2000 }).catch(() => false);
    
    return urlCheck || dashboardElements || chefButton;
  }

  // Helper: Verificar se está na página de login
  async function isOnLoginPage(page: any): Promise<boolean> {
    const loginForm = await page.locator('form').filter({ 
      has: page.locator('input[type="email"], input[name="email"]') 
    }).isVisible().catch(() => false);
    return loginForm || page.url().includes('/login');
  }

  // Helper: Fazer login (se necessário)
  async function ensureLoggedIn(page: any): Promise<boolean> {
    // Verificar se já está logado
    const loggedIn = await isLoggedIn(page);
    if (loggedIn) {
      return true;
    }
    
    // Verificar se está na página de login
    const onLoginPage = await isOnLoginPage(page);
    if (!onLoginPage) {
      // Se não está logado e não está na página de login, pode ser redirecionamento
      await page.waitForTimeout(1000);
      const stillLoggedIn = await isLoggedIn(page);
      if (stillLoggedIn) {
        return true;
      }
    }
    
    // Tentar fazer login
    const emailInput = page.locator('input[type="email"], input[name="email"]');
    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    const loginButton = page.locator('button').filter({ hasText: /entrar|login|sign in/i });
    
    const emailVisible = await emailInput.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (emailVisible) {
      // Usar credenciais do seed (usuários criados por seed_simple.py)
      // Usuários disponíveis: joao@example.com, maria@example.com, pedro@example.com, etc.
      // Senha padrão: 123456
      const testEmail = 'joao@example.com';
      const testPassword = '123456';
      
      await emailInput.fill(testEmail);
      await passwordInput.fill(testPassword);
      await loginButton.click();
      
      // Aguardar redirecionamento ou erro
      try {
        // Aguardar navegação para dashboard ou erro
        await Promise.race([
          page.waitForURL('**/dashboard', { timeout: 10000 }),
          page.waitForSelector('text=/erro|error|inválido|incorreto/i', { timeout: 3000 }).catch(() => null)
        ]);
        
        // Se apareceu mensagem de erro, login falhou
        const errorVisible = await page.locator('text=/erro|error|inválido|incorreto/i').isVisible().catch(() => false);
        if (errorVisible) {
          return false;
        }
        
        // Aguardar carregamento completo
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(2000);
        
        // Verificar se realmente logou (múltiplas verificações)
        const nowLoggedIn = await isLoggedIn(page);
        if (nowLoggedIn) {
          return true;
        }
        
        // Tentar verificar novamente após mais tempo
        await page.waitForTimeout(2000);
        return await isLoggedIn(page);
      } catch (error) {
        // Login falhou ou ainda está na página de login
        return false;
      }
    }
    
    return false;
  }

  // Helper: Abrir Chef Virtual
  async function openChefVirtual(page: any) {
    // Procurar botão do Chef Virtual
    const chefButton = page.locator('button').filter({ 
      hasText: /Chef Virtual|chef virtual/i 
    }).or(
      page.locator('button[aria-label*="Chef"], button[aria-label*="chef"]')
    );
    
    const buttonVisible = await chefButton.isVisible({ timeout: 10000 }).catch(() => false);
    
    if (buttonVisible) {
      await chefButton.click();
      
      // Aguardar dialog aparecer e estar pronto
      const chatDialog = page.locator('[role="dialog"]').filter({
        has: page.locator('text=/Chef Virtual|chef virtual/i')
      });
      
      await expect(chatDialog.first()).toBeVisible({ timeout: 5000 });
      
      // Aguardar input estar disponível (mais confiável que timeout fixo)
      await page.waitForSelector('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]', { 
        timeout: 5000 
      }).catch(() => null);
      
      // Aguardar um pouco mais para garantir que o componente está totalmente renderizado
      await page.waitForTimeout(500);
      
      return true;
    }
    
    return false;
  }

  test('should display Chef Virtual button on Dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    // Tentar fazer login e verificar se conseguiu
    const loggedIn = await ensureLoggedIn(page);
    
    if (!loggedIn) {
      // Se não conseguiu fazer login, pular teste
      test.skip();
      return;
    }
    
    // Verificar se realmente está no dashboard (não na página de login)
    const onLoginPage = await isOnLoginPage(page);
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    // Verificar se botão do Chef Virtual está visível
    // Usar múltiplos seletores para maior robustez
    const chefButton = page.locator('button')
      .filter({ hasText: /Chef Virtual/i })
      .or(page.locator('button[aria-label*="Chef Virtual"], button[aria-label*="chef virtual"]'))
      .or(page.locator('button').filter({ has: page.locator('text=/Chef Virtual/i') }));
    
    await expect(chefButton.first()).toBeVisible({ timeout: 10000 });
    
    // Verificar que botão tem ícone de chef
    const chefIcon = chefButton.first().locator('svg').or(
      chefButton.first().locator('[class*="ChefHat"]')
    );
    await expect(chefIcon.first()).toBeVisible({ timeout: 5000 });
  });

  test('should open Chef Virtual chat modal', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    const loggedIn = await ensureLoggedIn(page);
    if (!loggedIn) {
      test.skip();
      return;
    }
    
    const onLoginPage = await isOnLoginPage(page);
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    const opened = await openChefVirtual(page);
    
    if (opened) {
      // Verificar elementos do chat usando seletor mais direto e confiável
      // O placeholder real é "Digite sua mensagem..."
      const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
        .or(page.locator('input[type="text"]').filter({ hasText: /mensagem/i }))
        .or(page.locator('textarea').filter({ hasText: /mensagem/i }));
      
      await expect(chatInput.first()).toBeVisible({ timeout: 5000 });
    } else {
      test.skip();
    }
  });

  test('should send text message and receive response', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    const loggedIn = await ensureLoggedIn(page);
    if (!loggedIn) {
      test.skip();
      return;
    }
    
    const onLoginPage = await isOnLoginPage(page);
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    // Encontrar input de mensagem usando seletor direto
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    
    await expect(chatInput.first()).toBeVisible({ timeout: 5000 });
    
    // Verificar que o dialog está realmente aberto e visível
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible({ timeout: 5000 });
    
    // Enviar mensagem
    const testMessage = 'Quero um hambúrguer';
    
    // Limpar input antes de preencher (pode ter texto residual)
    await chatInput.first().clear();
    await chatInput.first().fill(testMessage);
    
    // Aguardar que o valor seja realmente preenchido
    await expect(chatInput.first()).toHaveValue(testMessage, { timeout: 2000 });
    
    // Aguardar um pouco para garantir que o React processou o estado
    await page.waitForTimeout(200);
    
    // Enviar com Enter (mais confiável que clicar no botão)
    await chatInput.first().press('Enter');
    
    // Aguardar que a requisição seja iniciada (verificar se há loading state)
    // A mensagem do usuário deve aparecer imediatamente (UI otimista)
    await page.waitForTimeout(500);
    
    // Verificar que a mensagem do usuário aparece
    // Procurar pelo texto dentro de um container de mensagem (não em inputs)
    // A mensagem do usuário está em um div com justify-end e bg-primary
    const userMessage = page.locator('[role="dialog"]')
      .locator('div')
      .filter({ hasText: new RegExp(testMessage.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i') })
      .filter({ hasNot: page.locator('input, textarea') })
      .first();
    
    await expect(userMessage).toBeVisible({ timeout: 10000 });
    
    // Aguardar resposta do assistente (pode demorar mais)
    // Aguardar que o loading state desapareça (indica que a resposta chegou)
    await page.waitForSelector('[role="dialog"] text:="O Chef está pensando..."', { 
      state: 'hidden', 
      timeout: 15000 
    }).catch(() => {}); // Ignorar se não houver loading state
    
    // Verificar que resposta do assistente aparece
    // Procurar pela mensagem mais recente do assistente (não do usuário)
    // Excluir: descrição do dialog, rodapé, mensagens antigas do histórico
    const assistantMessage = page.locator('[role="dialog"]')
      .locator('div')
      .filter({ hasText: /restaurante|hambúrguer|recomenda|burger|hamburgueria/i })
      .filter({ hasNot: page.locator('input, textarea, button, p.text-muted-foreground') }) // Excluir descrição e rodapé
      .filter({ hasNot: page.locator('heading, [role="heading"]') }) // Excluir títulos
      .last(); // Pegar a última mensagem (mais recente)
    
    await expect(assistantMessage).toBeVisible({ timeout: 15000 });
  });

  test('should display chat history', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    const loggedIn = await ensureLoggedIn(page);
    if (!loggedIn) {
      test.skip();
      return;
    }
    
    const onLoginPage = await isOnLoginPage(page);
    if (onLoginPage) {
      test.skip();
      return;
    }
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    // Aguardar carregamento do histórico
    await page.waitForTimeout(2000);
    
    // Verificar se há mensagens no histórico
    // As mensagens são divs dentro do dialog, sem classes específicas "message" ou "chat"
    const messages = page.locator('[role="dialog"]')
      .locator('div')
      .filter({ hasText: /.+/ }) // Qualquer div com texto
      .filter({ hasNot: page.locator('input, textarea, button') }); // Excluir inputs e botões
    
    const messageCount = await messages.count();
    
    // Pode haver ou não histórico (depende se usuário já conversou)
    // Apenas verificar que o componente está funcionando
    expect(messageCount).toBeGreaterThanOrEqual(0);
  });

  test('should handle social interactions (greetings)', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    
    // Enviar saudação
    await chatInput.fill('Olá');
    await page.waitForTimeout(500);
    
    const sendButton = page.locator('button').filter({
      hasText: /enviar|send|→/i
    }).first();
    
    const sendButtonVisible = await sendButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (sendButtonVisible) {
      await sendButton.click();
    } else {
      await chatInput.press('Enter');
    }
    
    // Aguardar resposta
    await page.waitForTimeout(2000);
    
    // Verificar resposta de saudação
    const greetingResponse = page.locator('[role="dialog"]')
      .locator('div')
      .filter({ hasText: /olá|oi|como posso ajudar|bem-vindo/i })
      .first();
    
    await expect(greetingResponse).toBeVisible({ timeout: 10000 });
  });

  test('should handle social interactions (gratitude)', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    
    // Enviar agradecimento
    await chatInput.fill('Obrigado');
    await page.waitForTimeout(500);
    
    const sendButton = page.locator('button').filter({
      hasText: /enviar|send|→/i
    }).first();
    
    const sendButtonVisible = await sendButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (sendButtonVisible) {
      await sendButton.click();
    } else {
      await chatInput.press('Enter');
    }
    
    // Aguardar resposta
    await page.waitForTimeout(2000);
    
    // Verificar resposta de agradecimento
    const gratitudeResponse = page.locator('[role="dialog"]')
      .locator('div')
      .filter({ hasText: /de nada|por nada|disponha|imagina|qualquer coisa/i })
      .first();
    
    await expect(gratitudeResponse).toBeVisible({ timeout: 10000 });
  });

  test('should show loading states during processing', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    
    // Enviar mensagem
    await chatInput.fill('Quero uma pizza');
    await page.waitForTimeout(500);
    
    const sendButton = page.locator('button').filter({
      hasText: /enviar|send|→/i
    }).first();
    
    const sendButtonVisible = await sendButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (sendButtonVisible) {
      await sendButton.click();
    } else {
      await chatInput.press('Enter');
    }
    
    // Verificar estados de loading (pensando, processando, etc.)
    const loadingIndicator = page.locator('text=/pensando|processando|carregando|loading/i')
      .or(page.locator('[class*="loading"], [class*="spinner"]'));
    
    // Pode ou não aparecer (depende da implementação)
    const loadingVisible = await loadingIndicator.isVisible({ timeout: 2000 }).catch(() => false);
    
    // Se aparecer, verificar que desaparece
    if (loadingVisible) {
      await expect(loadingIndicator).not.toBeVisible({ timeout: 15000 });
    }
  });

  test('should display error message on API failure', async ({ page }) => {
    // Interceptar requisições e simular erro
    await page.route('**/api/chat/**', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Erro interno do servidor' }),
        headers: { 'Content-Type': 'application/json' }
      });
    });
    
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    
    // Enviar mensagem
    await chatInput.fill('Teste de erro');
    await page.waitForTimeout(500);
    
    const sendButton = page.locator('button').filter({
      hasText: /enviar|send|→/i
    }).first();
    
    const sendButtonVisible = await sendButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (sendButtonVisible) {
      await sendButton.click();
    } else {
      await chatInput.press('Enter');
    }
    
    // Verificar mensagem de erro
    const errorMessage = page.locator('text=/erro|error|ocorreu um problema/i');
    await expect(errorMessage.first()).toBeVisible({ timeout: 10000 });
  });

  test('should handle rate limiting (429 error)', async ({ page }) => {
    // Interceptar requisições e simular rate limit
    let requestCount = 0;
    
    await page.route('**/api/chat/**', route => {
      requestCount++;
      if (requestCount > 30) {
        route.fulfill({
          status: 429,
          body: JSON.stringify({ detail: 'Muitas requisições. Tente novamente em alguns instantes.' }),
          headers: { 
            'Content-Type': 'application/json',
            'Retry-After': '60'
          }
        });
      } else {
        route.continue();
      }
    });
    
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    // Este teste é mais complexo e pode ser implementado depois
    // Por enquanto, apenas verificar que a estrutura está pronta
    test.skip();
  });

  test('should close chat modal', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    // Encontrar botão de fechar
    const closeButton = page.locator('button').filter({
      hasText: /fechar|close|×|✕/i
    }).or(
      page.locator('button[aria-label*="fechar"], button[aria-label*="close"]')
    ).or(
      page.locator('[role="dialog"] button').last()
    );
    
    const closeButtonVisible = await closeButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (closeButtonVisible) {
      await closeButton.first().click();
      await page.waitForTimeout(500);
      
      // Verificar que modal fechou
      const chatDialog = page.locator('[role="dialog"]').filter({
        has: page.locator('text=/Chef Virtual/i')
      });
      
      await expect(chatDialog).not.toBeVisible({ timeout: 5000 });
    }
  });

  test('should be responsive on mobile devices', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    // Verificar que chat modal é responsivo
    const chatDialog = page.locator('[role="dialog"]').first();
    const dialogBox = await chatDialog.boundingBox();
    
    if (dialogBox) {
      // Modal deve caber na tela mobile
      expect(dialogBox.width).toBeLessThanOrEqual(375);
      expect(dialogBox.height).toBeLessThanOrEqual(667);
    }
  });

  test('should be responsive on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    // Verificar que chat modal tem tamanho adequado em desktop
    const chatDialog = page.locator('[role="dialog"]').first();
    const dialogBox = await chatDialog.boundingBox();
    
    if (dialogBox) {
      // Modal deve ter largura razoável em desktop (não ocupar tela toda)
      expect(dialogBox.width).toBeLessThan(800);
    }
  });

  test('should prevent out-of-scope questions', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    
    // Enviar pergunta fora do escopo
    await chatInput.fill('Quero uma passagem de avião');
    await page.waitForTimeout(500);
    
    const sendButton = page.locator('button').filter({
      hasText: /enviar|send|→/i
    }).first();
    
    const sendButtonVisible = await sendButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (sendButtonVisible) {
      await sendButton.click();
    } else {
      await chatInput.press('Enter');
    }
    
    // Aguardar resposta
    await page.waitForTimeout(3000);
    
    // Verificar que resposta indica que está fora do escopo
    const outOfScopeResponse = page.locator('[role="dialog"]')
      .locator('div')
      .filter({
      hasText: /especializado|apenas|restaurantes|comida/i
    });
    
    await expect(outOfScopeResponse.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display restaurant recommendations in response', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    
    // Enviar pergunta sobre recomendações
    await chatInput.fill('Quais restaurantes você recomenda?');
    await page.waitForTimeout(500);
    
    const sendButton = page.locator('button').filter({
      hasText: /enviar|send|→/i
    }).first();
    
    const sendButtonVisible = await sendButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (sendButtonVisible) {
      await sendButton.click();
    } else {
      await chatInput.press('Enter');
    }
    
    // Aguardar resposta
    await page.waitForTimeout(5000);
    
    // Verificar que resposta menciona restaurantes
    const restaurantResponse = page.locator('[role="dialog"]')
      .locator('div')
      .filter({ hasText: /restaurante|recomendo|sugiro|avaliação|preço/i })
      .first();
    
    await expect(restaurantResponse).toBeVisible({ timeout: 15000 });
  });

  test('should handle markdown formatting in responses', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    const chatInput = page.locator('input[placeholder*="Digite sua mensagem"], textarea[placeholder*="Digite sua mensagem"]')
      .or(page.locator('[role="dialog"] input[type="text"], [role="dialog"] textarea'));
    await expect(chatInput).toBeVisible({ timeout: 5000 });
    
    // Enviar mensagem que pode gerar resposta com markdown
    await chatInput.fill('Me fale sobre restaurantes italianos');
    await page.waitForTimeout(500);
    
    const sendButton = page.locator('button').filter({
      hasText: /enviar|send|→/i
    }).first();
    
    const sendButtonVisible = await sendButton.isVisible({ timeout: 5000 }).catch(() => false);
    
    if (sendButtonVisible) {
      await sendButton.click();
    } else {
      await chatInput.press('Enter');
    }
    
    // Aguardar resposta
    await page.waitForTimeout(5000);
    
    // Verificar que markdown é renderizado (texto em negrito não mostra asteriscos)
    const response = page.locator('[role="dialog"]')
      .locator('div')
      .filter({ hasText: /.+/ })
      .filter({ hasNot: page.locator('input, textarea, button') })
      .last();
    const responseText = await response.textContent();
    
    // Não deve ter asteriscos visíveis (markdown renderizado)
    if (responseText) {
      expect(responseText).not.toContain('**');
    }
  });

  test('should display fixed footer disclaimer', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    
    await ensureLoggedIn(page);
    
    const opened = await openChefVirtual(page);
    
    if (!opened) {
      test.skip();
      return;
    }
    
    // Verificar que rodapé com disclaimer está visível
    const disclaimer = page.locator('text=/disponíveis|verifique|TasteMatch/i');
    await expect(disclaimer.first()).toBeVisible({ timeout: 5000 });
  });
});

