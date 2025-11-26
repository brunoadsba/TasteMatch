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
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[85vw] sm:w-[400px]">
        {title && (
          <SheetHeader>
            <SheetTitle>{title}</SheetTitle>
          </SheetHeader>
        )}
        <div className="mt-6 space-y-2 flex flex-col [&>*]:w-full">
          {children}
        </div>
      </SheetContent>
    </Sheet>
  );
}
