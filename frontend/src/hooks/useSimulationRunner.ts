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
  onComplete?: () => void,
  onOrderCreated?: () => void // Callback quando um pedido é criado
): UseSimulationRunnerReturn {
  const { simulateOrder } = useSimulateOrder();
  const { refresh: refreshRecommendations } = useRecommendations(12);
  
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(0);
  const [error, setError] = useState<string | null>(null);

  /**
   * Normaliza tipos de culinária para corresponder ao formato do banco de dados.
   * Converte variações como "Japonês" -> "japonesa", "Italiana" -> "italiana"
   */
  const normalizeCuisineType = (cuisineType: string): string[] => {
    const normalized = cuisineType.toLowerCase().trim();
    const variations: string[] = [normalized];
    
    // Mapeamento de variações comuns (masculino -> feminino)
    const mappings: Record<string, string> = {
      'japonês': 'japonesa',
      'italiano': 'italiana',
      'francês': 'francesa',
      'brasileiro': 'brasileira',
      'chinês': 'chinesa',
      'mexicano': 'mexicana',
      'português': 'portuguesa',
    };
    
    // Adicionar variação feminina se existir no mapeamento
    if (mappings[normalized]) {
      variations.push(mappings[normalized]);
    }
    
    // Tentar todas as variações
    const allVariations: string[] = [];
    for (const variation of variations) {
      allVariations.push(variation); // Ex: "japonesa"
      allVariations.push(`comida ${variation}`); // Ex: "comida japonesa"
    }
    
    return [...new Set(allVariations)]; // Remove duplicatas
  };

  /**
   * Busca um restaurante por tipo de culinária.
   * Tenta múltiplas variações do tipo para encontrar correspondência.
   * Retorna o primeiro restaurante encontrado do tipo especificado.
   */
  const findRestaurantByCuisine = async (cuisineType: string): Promise<number | null> => {
    try {
      // Gerar variações do tipo de culinária
      const variations = normalizeCuisineType(cuisineType);
      
      // Tentar busca exata para cada variação
      for (const variation of variations) {
        const response = await api.getRestaurants({
          cuisine_type: variation,
          limit: 1,
          sort_by: 'rating_desc',
        });
        
        if (response.restaurants && response.restaurants.length > 0) {
          return response.restaurants[0].id;
        }
      }
      
      // Se não encontrou por busca exata, tentar busca textual (buscar mais resultados)
      const searchResponse = await api.getRestaurants({
        search: variations[0], // Usar a primeira variação para busca textual
        limit: 10, // Buscar mais para ter mais opções
        sort_by: 'rating_desc',
      });
      
      if (searchResponse.restaurants && searchResponse.restaurants.length > 0) {
        // Procurar o primeiro que tenha o tipo de culinária similar
        const found = searchResponse.restaurants.find(r => {
          const restaurantCuisine = (r.cuisine_type || '').toLowerCase();
          return variations.some(v => restaurantCuisine.includes(v) || v.includes(restaurantCuisine));
        });
        
        if (found) {
          return found.id;
        }
        
        // Se não encontrou similar, retorna o primeiro da busca (melhor avaliado)
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
        
        // NÃO notificar após cada pedido para evitar múltiplos toasts sobrepostos
        // A notificação acontecerá apenas no final da simulação completa
        
        // Atualizar progresso
        const newProgress = Math.round(((i + 1) / orders.length) * 100);
        setProgress(newProgress);
        
        if (onProgress) {
          onProgress(i + 1, orders.length);
        }
        
        // Delay entre pedidos aumentado para dar tempo de ler as mensagens do terminal (1500ms)
        if (i < orders.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 1500));
        }
      }
      
      // Atualizar recomendações após todos os pedidos (sem toast duplicado)
      await refreshRecommendations(false); // Não mostrar toast aqui, vamos mostrar um único resumo
      
      // Notificar que pedidos foram criados (uma única vez no final)
      if (onOrderCreated) {
        onOrderCreated();
      }
      
      toast.success('Simulação concluída!', {
        description: `${orders.length} pedido(s) criado(s). Recomendações atualizadas.`,
        duration: 3000, // Mostrar por 3 segundos
      });
      
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
        // Notificar que um pedido foi criado (para atualizar UI)
        if (onOrderCreated) {
          onOrderCreated();
        }
        
        // Atualizar recomendações sem toast (evitar spam de notificações)
        await refreshRecommendations(false);
        
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

