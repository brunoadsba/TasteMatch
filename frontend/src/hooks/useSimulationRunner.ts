import { useState } from 'react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import { useSimulateOrder } from './useSimulateOrder';
import { useRecommendations } from './useRecommendations';
import type { SimulationScenario, OrderSimulationData } from '@/data/simulationScenarios';
import type { OrderCreate } from '@/types';

interface UseSimulationRunnerReturn {
  runScenario: (scenario: SimulationScenario) => Promise<void>;
  runCustomOrder: (orderData: OrderCreate) => Promise<boolean>;
  isRunning: boolean;
  progress: number; // 0-100
  currentStep: number;
  totalSteps: number;
  error: string | null;
}

/**
 * Hook para orquestrar simulação de pedidos.
 * Gerencia criação sequencial de múltiplos pedidos e atualização de recomendações.
 */
export function useSimulationRunner(
  onProgress?: (step: number, total: number) => void,
  onComplete?: () => void
): UseSimulationRunnerReturn {
  const { simulateOrder } = useSimulateOrder();
  const { refresh: refreshRecommendations } = useRecommendations(12);
  
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [error, setError] = useState<string | null>(null);

  /**
   * Busca um restaurante por tipo de culinária.
   * Retorna o primeiro restaurante encontrado do tipo especificado.
   */
  const findRestaurantByCuisine = async (cuisineType: string): Promise<number | null> => {
    try {
      const response = await api.getRestaurants({
        cuisine_type: cuisineType,
        limit: 1,
        sort_by: 'rating_desc', // Pega o melhor avaliado
      });
      
      if (response.restaurants && response.restaurants.length > 0) {
        return response.restaurants[0].id;
      }
      
      // Se não encontrou pelo tipo exato, tenta busca textual
      const searchResponse = await api.getRestaurants({
        search: cuisineType,
        limit: 1,
        sort_by: 'rating_desc',
      });
      
      if (searchResponse.restaurants && searchResponse.restaurants.length > 0) {
        return searchResponse.restaurants[0].id;
      }
      
      return null;
    } catch (err) {
      console.error('Erro ao buscar restaurante:', err);
      return null;
    }
  };

  /**
   * Cria um pedido simulado com base nos dados do cenário.
   */
  const createSimulatedOrder = async (orderData: OrderSimulationData, restaurantId: number): Promise<boolean> => {
    const orderCreate: OrderCreate = {
      restaurant_id: restaurantId,
      order_date: new Date().toISOString(),
      total_amount: orderData.total_amount,
      rating: orderData.rating as 1 | 2 | 3 | 4 | 5,
      items: orderData.items?.map(item => ({ name: item })) || [],
      is_simulation: true,
    };
    
    return await simulateOrder(orderCreate);
  };

  /**
   * Executa um cenário completo (múltiplos pedidos).
   */
  const runScenario = async (scenario: SimulationScenario): Promise<void> => {
    setIsRunning(true);
    setError(null);
    setCurrentStep(0);
    setTotalSteps(scenario.orders.length);
    setProgress(0);

    try {
      const orders = scenario.orders;
      
      // Processar cada pedido em sequência com delay
      for (let i = 0; i < orders.length; i++) {
        const orderData = orders[i];
        setCurrentStep(i + 1);
        
        // Buscar restaurante
        const restaurantId = await findRestaurantByCuisine(orderData.cuisine_type);
        
        if (!restaurantId) {
          toast.warning('Restaurante não encontrado', {
            description: `Não foi possível encontrar restaurante do tipo "${orderData.cuisine_type}"`,
          });
          continue; // Pula este pedido e continua
        }
        
        // Criar pedido simulado
        const success = await createSimulatedOrder(orderData, restaurantId);
        
        if (!success) {
          toast.error('Erro ao criar pedido', {
            description: `Falha ao criar pedido ${i + 1}/${orders.length}`,
          });
          continue; // Continua mesmo com erro
        }
        
        // Atualizar progresso
        const newProgress = Math.round(((i + 1) / orders.length) * 100);
        setProgress(newProgress);
        
        if (onProgress) {
          onProgress(i + 1, orders.length);
        }
        
        // Delay entre pedidos para criar suspense (500ms)
        if (i < orders.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
      
      // Atualizar recomendações após todos os pedidos
      toast.success('Simulação concluída!', {
        description: `${orders.length} pedido(s) criado(s). Atualizando recomendações...`,
      });
      
      await refreshRecommendations();
      
      if (onComplete) {
        onComplete();
      }
      
      // Reset progresso após um delay
      setTimeout(() => {
        setProgress(0);
        setCurrentStep(0);
        setTotalSteps(0);
      }, 1000);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao executar simulação';
      setError(errorMessage);
      toast.error('Falha na simulação', {
        description: errorMessage,
      });
    } finally {
      setIsRunning(false);
    }
  };

  /**
   * Cria um pedido único (usado pelo formulário manual).
   */
  const runCustomOrder = async (orderData: OrderCreate): Promise<boolean> => {
    setIsRunning(true);
    setError(null);
    
    try {
      const success = await simulateOrder({
        ...orderData,
        is_simulation: true,
      });
      
      if (success) {
        // Atualizar recomendações
        await refreshRecommendations();
        
        if (onComplete) {
          onComplete();
        }
      }
      
      return success;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao criar pedido';
      setError(errorMessage);
      return false;
    } finally {
      setIsRunning(false);
    }
  };

  return {
    runScenario,
    runCustomOrder,
    isRunning,
    progress,
    currentStep,
    totalSteps,
    error,
  };
}

