import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ChefChat } from './ChefChat';
import { ChefHat } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChefChatButtonProps {
  className?: string;
}

export function ChefChatButton({ className }: ChefChatButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="fixed bottom-6 right-6 z-50">
        {/* Anel de pulso animado para chamar atenção */}
        <div 
          className="absolute inset-0 rounded-full bg-orange-400/30 animate-ping opacity-75" 
          style={{ animationDuration: '2s' }} 
        />
        
        <Button
          onClick={() => setOpen(true)}
          className={cn(
            'relative rounded-full shadow-2xl group overflow-hidden',
            'bg-gradient-to-br from-orange-500 via-orange-600 to-orange-700',
            'hover:from-orange-600 hover:via-orange-700 hover:to-orange-800',
            'text-white border-2 border-white/30 hover:border-white/50',
            'hover:scale-105 active:scale-100 transition-all duration-200',
            'ring-2 ring-orange-400/30 hover:ring-orange-400/50',
            'px-5 py-3.5 flex items-center gap-3',
            'min-w-[160px] backdrop-blur-sm',
            className
          )}
          aria-label="Abrir chat com Chef Virtual"
        >
          {/* Efeito de brilho no fundo */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          
          {/* Ícone Chef Hat com animação */}
          <div className="relative z-10">
            <ChefHat 
              className="w-7 h-7 group-hover:rotate-[-8deg] group-hover:scale-110 transition-all duration-200 drop-shadow-lg" 
              strokeWidth={2.5}
            />
            {/* Brilho sutil no ícone */}
            <div className="absolute inset-0 bg-white/30 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
          </div>
          
          {/* Texto "Chef Virtual" */}
          <span className="font-bold text-sm whitespace-nowrap relative z-10 drop-shadow-md">
            Chef Virtual
          </span>
        </Button>
      </div>

      <ChefChat open={open} onOpenChange={setOpen} />
    </>
  );
}

