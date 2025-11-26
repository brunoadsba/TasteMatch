import { useEffect } from 'react';
import type { ReactNode } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';

interface MobileMenuProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  children: ReactNode;
}

export function MobileMenu({ open, onOpenChange, title, children }: MobileMenuProps) {
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
          </SheetHeader>
        )}
        
        {/* Container flexível: título no topo, botões na parte inferior */}
        <div className="flex-1 flex flex-col mt-6">
          {/* Espaço flexível para empurrar botões para baixo */}
          <div className="flex-1" />
          
          {/* Botões na parte inferior para melhor alcance com polegar */}
          <div className="space-y-2 flex flex-col [&>*]:w-full pb-4">
            {children}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
