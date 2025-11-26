import { useRef, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useSimulationRunner } from '@/hooks/useSimulationRunner';
import { useAIReasoning } from '@/hooks/useAIReasoning';
import { AIReasoningLogComponent } from './AIReasoningLog';
import { SIMULATION_SCENARIOS, type SimulationScenario } from '@/data/simulationScenarios';
import { Loader2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';

interface OrderSimulatorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete?: () => void;
  onOrderCreated?: () => void; // Callback quando um pedido é criado
}

export function OrderSimulator({ open, onOpenChange, onComplete, onOrderCreated }: OrderSimulatorProps) {
  const [activeTab, setActiveTab] = useState<'quick' | 'manual'>('quick');
  const [currentScenarioId, setCurrentScenarioId] = useState<string>('fit');
  const currentScenarioIdRef = useRef<string>('fit');
  const { logs, clearLogs, simulateReasoning } = useAIReasoning();
  
  const { runScenario, runCustomOrder, isRunning, progress, currentStep, totalSteps } = useSimulationRunner(
    async (step, total) => {
      // Callback de progresso - gera logs do terminal
      await simulateReasoning(currentScenarioIdRef.current, step, total);
    },
    () => {
      // Callback de conclusão
      toast.success('Simulação concluída!', {
        description: 'Seus pedidos foram processados e o perfil foi atualizado.',
      });
      if (onComplete) {
        onComplete();
      }
      // Fechar modal após um delay
      setTimeout(() => {
        onOpenChange(false);
      }, 2000);
    },
    () => {
      // Callback quando um pedido é criado - atualizar painel dinamicamente
      toast.success('Pedido simulado criado!', {
        description: 'O sistema está atualizando suas recomendações...',
        duration: 2000,
      });
      if (onOrderCreated) {
        onOrderCreated();
      }
    }
  );

  // Formulário manual
  const [manualForm, setManualForm] = useState({
    restaurant_id: '',
    total_amount: '',
    rating: '5',
    items: '',
  });

  const handleQuickPersona = async (scenario: SimulationScenario) => {
    clearLogs(); // Limpar logs anteriores
    setCurrentScenarioId(scenario.id); // Salvar ID do cenário para logs (para UI)
    currentScenarioIdRef.current = scenario.id; // Garantir que logs usem o cenário correto
    await runScenario(scenario);
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const orderData = {
      restaurant_id: parseInt(manualForm.restaurant_id),
      order_date: new Date().toISOString(),
      total_amount: manualForm.total_amount ? parseFloat(manualForm.total_amount) : undefined,
      rating: parseInt(manualForm.rating) as 1 | 2 | 3 | 4 | 5,
      items: manualForm.items 
        ? manualForm.items.split(',').map(item => ({ name: item.trim() }))
        : [],
    };

    const success = await runCustomOrder(orderData);
    
    if (success) {
      toast.success('Pedido manual criado!', {
        description: 'O sistema está atualizando suas recomendações...',
        duration: 2000,
      });
      setManualForm({
        restaurant_id: '',
        total_amount: '',
        rating: '5',
        items: '',
      });
    } else {
      toast.error('Erro ao criar pedido', {
        description: 'Verifique os dados e tente novamente.',
      });
    }
  };

  const getColorClasses = (color: string) => {
    const colors: Record<string, string> = {
      green: 'bg-green-50 border-green-200 hover:bg-green-100 text-green-900',
      orange: 'bg-orange-50 border-orange-200 hover:bg-orange-100 text-orange-900',
      purple: 'bg-purple-50 border-purple-200 hover:bg-purple-100 text-purple-900',
    };
    return colors[color] || 'bg-gray-50 border-gray-200 hover:bg-gray-100';
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-500" />
            Simulador de Pedidos
          </DialogTitle>
          <DialogDescription>
            Crie pedidos simulados para testar o sistema de recomendações personalizadas
          </DialogDescription>
        </DialogHeader>

        {/* Tabs */}
        <div className="flex gap-2 border-b mb-6" role="tablist">
          <button
            onClick={() => setActiveTab('quick')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'quick'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            role="tab"
            aria-selected={activeTab === 'quick'}
            aria-controls="quick-personas-panel"
            id="quick-personas-tab"
          >
            Quick Personas
          </button>
          <button
            onClick={() => setActiveTab('manual')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'manual'
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            role="tab"
            aria-selected={activeTab === 'manual'}
            aria-controls="manual-options-panel"
            id="manual-options-tab"
          >
            Opções Avançadas
          </button>
        </div>

        {/* Conteúdo das Tabs */}
        {activeTab === 'quick' ? (
          <div className="space-y-4" role="tabpanel" id="quick-personas-panel" aria-labelledby="quick-personas-tab">
            <div>
              <p className="text-sm text-gray-600 mb-4">
                Escolha um perfil de usuário para simular múltiplos pedidos instantaneamente:
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4" role="group" aria-label="Perfis de usuário para simulação">
                {SIMULATION_SCENARIOS.map((scenario) => (
                  <Card
                    key={scenario.id}
                    className={`cursor-pointer transition-all hover:shadow-lg ${getColorClasses(scenario.color)}`}
                    onClick={() => !isRunning && handleQuickPersona(scenario)}
                    role="button"
                    tabIndex={isRunning ? -1 : 0}
                    aria-label={`Simular pedidos para perfil ${scenario.name}: ${scenario.description}`}
                    aria-disabled={isRunning}
                    onKeyDown={(e) => {
                      if ((e.key === 'Enter' || e.key === ' ') && !isRunning) {
                        e.preventDefault();
                        handleQuickPersona(scenario);
                      }
                    }}
                  >
                    <CardHeader>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-4xl" aria-hidden="true">{scenario.icon}</span>
                        {isRunning && currentScenarioId === scenario.id && (
                          <Loader2 className="w-5 h-5 animate-spin" aria-label="Processando simulação" />
                        )}
                      </div>
                      <CardTitle className="text-lg">{scenario.name}</CardTitle>
                      <CardDescription className="text-sm">
                        {scenario.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xs text-gray-600 space-y-1">
                        <p>• {scenario.orders.length} pedidos simulados</p>
                        <p>• Culinárias: {scenario.orders.map(o => o.cuisine_type).join(', ')}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* Terminal de AI Reasoning */}
            <AIReasoningLogComponent 
              logs={logs} 
              onClear={clearLogs}
              className="mt-4"
            />

            {/* Progresso da Simulação */}
            {isRunning && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-900">
                    Criando pedidos... {currentStep}/{totalSteps}
                  </span>
                  <span className="text-sm text-blue-600">{progress}%</span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <form onSubmit={handleManualSubmit} className="space-y-4" role="tabpanel" id="manual-options-panel" aria-labelledby="manual-options-tab">
            <div>
              <label htmlFor="restaurant_id" className="block text-sm font-medium text-gray-700 mb-1">
                ID do Restaurante *
              </label>
              <Input
                id="restaurant_id"
                type="number"
                value={manualForm.restaurant_id}
                onChange={(e) => setManualForm({ ...manualForm, restaurant_id: e.target.value })}
                placeholder="Ex: 1"
                required
                disabled={isRunning}
                aria-label="ID do restaurante"
                aria-required="true"
              />
            </div>

            <div>
              <label htmlFor="total_amount" className="block text-sm font-medium text-gray-700 mb-1">
                Valor Total (R$)
              </label>
              <Input
                id="total_amount"
                type="number"
                step="0.01"
                value={manualForm.total_amount}
                onChange={(e) => setManualForm({ ...manualForm, total_amount: e.target.value })}
                placeholder="Ex: 45.90"
                disabled={isRunning}
                aria-label="Valor total do pedido em reais"
              />
            </div>

            <div>
              <label htmlFor="rating" className="block text-sm font-medium text-gray-700 mb-1">
                Avaliação (1-5)
              </label>
              <Input
                id="rating"
                type="number"
                min="1"
                max="5"
                value={manualForm.rating}
                onChange={(e) => setManualForm({ ...manualForm, rating: e.target.value })}
                required
                disabled={isRunning}
                aria-label="Avaliação do pedido de 1 a 5"
                aria-required="true"
              />
            </div>

            <div>
              <label htmlFor="items" className="block text-sm font-medium text-gray-700 mb-1">
                Itens (separados por vírgula)
              </label>
              <Input
                id="items"
                type="text"
                value={manualForm.items}
                onChange={(e) => setManualForm({ ...manualForm, items: e.target.value })}
                placeholder="Ex: Pizza, Refrigerante, Batata"
                disabled={isRunning}
                aria-label="Itens do pedido separados por vírgula"
              />
            </div>

            <Button type="submit" disabled={isRunning} className="w-full">
              {isRunning ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Criando pedido...
                </>
              ) : (
                'Criar Pedido Simulado'
              )}
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

