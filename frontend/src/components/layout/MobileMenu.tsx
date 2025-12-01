import { useEffect } from 'react';
import type { ReactNode } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';

interface MobileMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  children: ReactNode;
  sections?: Array<{
    label?: string;
    items: ReactNode;
  }>;
  onCloseMenu?: () => void; // Função para fechar menu programaticamente
}

export function MobileMenu({ open, onOpenChange, title, children, sections, onCloseMenu }: MobileMenuProps) {
  // Expor função de fechar menu via contexto ou prop
  useEffect(() => {
    if (onCloseMenu) {
      // Armazenar função globalmente para ser acessada pelos botões
      (window as any).__closeMobileMenu = onCloseMenu;
      return () => {
        delete (window as any).__closeMobileMenu;
      };
    }
  }, [onCloseMenu]);
  // Overscroll Behavior: Prevenir scroll da página de fundo quando menu está aberto
  useEffect(() => {
    if (open) {
      // Salvar o valor original
      const originalOverscroll = document.body.style.overscrollBehaviorY;
      // Aplicar overscroll-behavior-y: none
      document.body.style.overscrollBehaviorY = 'none';
      
      return () => {
        // Restaurar o valor original quando menu fechar
        document.body.style.overscrollBehaviorY = originalOverscroll;
      };
    }
  }, [open]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[85vw] sm:w-[400px] flex flex-col">
        {title && (
          <SheetHeader>
            <SheetTitle>{title}</SheetTitle>
            <SheetDescription className="sr-only">
              Menu de navegação e configurações
            </SheetDescription>
          </SheetHeader>
        )}
        
        {/* Container flexível: título no topo, botões na parte inferior */}
        <div className="flex-1 flex flex-col mt-6 overflow-y-auto">
          {/* Seções organizadas (se fornecidas) */}
          {sections && sections.length > 0 ? (
            <div className="space-y-6 pb-4">
              {sections.map((section, index) => (
                <div key={index} className="space-y-2">
                  {section.label && (
                    <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-1">
                      {section.label}
                    </h3>
                  )}
                  <div className="space-y-2 flex flex-col [&>*]:w-full">
                    {section.items}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <>
              {/* Espaço flexível para empurrar botões para baixo */}
              <div className="flex-1" />
              
              {/* Botões na parte inferior para melhor alcance com polegar */}
              <div className="space-y-2 flex flex-col [&>*]:w-full pb-4">
                {children}
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
