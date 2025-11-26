import { useState } from 'react';
import type { ReactNode } from 'react';
import { Menu } from 'lucide-react';
import { MobileMenu } from './MobileMenu';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface AppHeaderProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  demoModeBar?: ReactNode; // Barra de Demo Mode opcional
  className?: string;
}

export function AppHeader({ 
  title, 
  subtitle, 
  children, 
  demoModeBar,
  className 
}: AppHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <>
      <header className={cn("bg-card border-b border-border", className)}>
        {/* Barra de Demo Mode (se fornecida) */}
        {demoModeBar && (
          <div className="bg-blue-600 text-white px-4 py-2 text-center text-sm font-medium">
            {demoModeBar}
          </div>
        )}
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            {/* Título e Subtítulo */}
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100">
                {title}
              </h1>
              {subtitle && (
                <p className="text-xs md:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                  {subtitle}
                </p>
              )}
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
      >
        {children}
      </MobileMenu>
    </>
  );
}

