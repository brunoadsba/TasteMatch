import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Brain } from 'lucide-react';
import { useChefRecommendation } from '@/hooks/useChefRecommendation';

interface ChefReasoningModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ChefReasoningModal({ open, onOpenChange }: ChefReasoningModalProps) {
  const { chefRecommendation, loading, error } = useChefRecommendation({
    autoFetch: open,
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Raciocínio do Chef
          </DialogTitle>
          <DialogDescription>
            Veja, em linguagem simples, por que este restaurante foi escolhido para você.
          </DialogDescription>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto mt-4 space-y-4">
          {loading && !chefRecommendation && (
            <p className="text-sm text-muted-foreground">Gerando raciocínio do Chef...</p>
          )}

          {error && !chefRecommendation && (
            <p className="text-sm text-red-600">
              Não foi possível carregar o raciocínio do Chef no momento. Tente novamente mais tarde.
            </p>
          )}

          {chefRecommendation && (
            <>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold">
                  Por que o Chef escolheu {chefRecommendation.restaurant.name} para você
                </h3>
                <p className="text-sm text-muted-foreground">
                  Esta explicação é baseada no seu histórico de pedidos, nas suas preferências e nas
                  características deste restaurante.
                </p>
              </div>

              {/* Explicação completa, sem truncar */}
              <div className="bg-muted/60 border border-border rounded-lg p-4">
                <p className="text-sm leading-relaxed">
                  {chefRecommendation.explanation}
                </p>
              </div>

              {/* Razões detalhadas em linguagem simples */}
              {chefRecommendation.reasoning && chefRecommendation.reasoning.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold">Principais motivos desta escolha</h4>
                  <ul className="space-y-1 text-sm">
                    {chefRecommendation.reasoning.map((reason, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="mt-0.5 text-amber-600">✓</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Selo de confiança em linguagem leiga, sem números de similaridade */}
              <div className="flex items-center gap-2 pt-2 text-xs text-muted-foreground">
                <span className="inline-flex items-center rounded-full border border-border px-3 py-1">
                  Confiança alta na combinação com seu perfil
                </span>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

