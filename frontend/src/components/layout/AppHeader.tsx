import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { Menu, X, Info } from 'lucide-react';
import { MobileMenu } from './MobileMenu';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface AppHeaderProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  demoModeBar?: ReactNode; // Barra de Demo Mode opcional
  isDemoMode?: boolean; // Indica se está em modo demo
  className?: string;
}

export function AppHeader({ 
  title, 
  subtitle, 
  children, 
  demoModeBar,
  isDemoMode = false,
  mobileMenuSections,
  className 
}: AppHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  // Verificar se banner foi fechado anteriormente
  useEffect(() => {
    if (isDemoMode) {
      const dismissed = localStorage.getItem('demo-banner-dismissed');
      setBannerDismissed(dismissed === 'true');
    } else {
      setBannerDismissed(false);
    }
  }, [isDemoMode]);

  const handleDismissBanner = () => {
    setBannerDismissed(true);
    localStorage.setItem('demo-banner-dismissed', 'true');
  };

  return (
    <>
      <header className={cn("bg-card border-b border-border", className)}>
        {/* Barra de Demo Mode Compacta e Dismissível */}
        {demoModeBar && isDemoMode && !bannerDismissed && (
          <div className="bg-blue-600 text-white px-3 py-1.5 flex items-center justify-between gap-2 text-xs md:text-sm">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <Info className="w-3 h-3 md:w-4 md:h-4 flex-shrink-0" />
              <span className="truncate">Modo Demo Ativo</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 md:h-6 md:w-6 text-white hover:bg-blue-700 flex-shrink-0"
              onClick={handleDismissBanner}
              aria-label="Fechar banner"
            >
              <X className="w-3 h-3 md:w-4 md:h-4" />
            </Button>
          </div>
        )}
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Título e Subtítulo com Badge DEMO */}
            <div className="flex items-center gap-2">
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100">
                    {title}
                  </h1>
                  {isDemoMode && (
                    <span className="px-2 py-0.5 text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded-full">
                      DEMO
                    </span>
                  )}
                </div>
                {subtitle && (
                  <p className="text-xs md:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                    {subtitle}
                  </p>
                )}
              </div>
            </div>

            {/* Desktop: Ações inline */}
            <div className="hidden md:flex items-center gap-4">
              {children}
            </div>

            {/* Mobile: Botão hambúrguer */}
            <div className="md:hidden">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setMobileMenuOpen(true)}
                aria-label="Abrir menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <MobileMenu
        open={mobileMenuOpen}
        onOpenChange={setMobileMenuOpen}
        title={title}
        sections={mobileMenuSections}
      >
        {children}
      </MobileMenu>
    </>
  );
}

