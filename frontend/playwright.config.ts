import { defineConfig, devices } from '@playwright/test';

/**
 * Configuração do Playwright para testes E2E mobile-first
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['list'],
  ],
  
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    // Forçar uso do Chromium completo (não headless shell)
    channel: 'chromium',
    headless: false, // Executar com interface gráfica para debug
  },

  projects: [
    // Mobile devices (usando Chromium com viewports customizados)
    {
      name: 'Mobile iPhone SE',
      use: { 
        viewport: { width: 375, height: 667 },
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        deviceScaleFactor: 2,
      },
    },
    {
      name: 'Mobile iPhone 12 Pro',
      use: { 
        viewport: { width: 390, height: 844 },
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        deviceScaleFactor: 3,
      },
    },
    {
      name: 'Mobile Android',
      use: { 
        viewport: { width: 393, height: 851 },
        userAgent: 'Mozilla/5.0 (Linux; Android 11; Pixel 5)',
        deviceScaleFactor: 2.75,
      },
    },
    
    // Tablet
    {
      name: 'Tablet iPad',
      use: { 
        viewport: { width: 1024, height: 1366 },
        userAgent: 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)',
        deviceScaleFactor: 2,
      },
    },
    
    // Desktop
    {
      name: 'Desktop Chrome',
      use: { 
        ...devices['Desktop Chrome'],
      },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});

