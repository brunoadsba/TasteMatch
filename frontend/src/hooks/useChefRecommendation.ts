import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import type { ChefRecommendation } from '@/types';
import { toast } from 'sonner';

interface UseChefRecommendationOptions {
  autoFetch?: boolean;
  refreshTrigger?: number;
}

interface UseChefRecommendationReturn {
  chefRecommendation: ChefRecommendation | null;
  loading: boolean;
  error: string | null;
  refresh: (showToast?: boolean) => Promise<void>;
}

/**
 * Hook para buscar e gerenciar a recomendação única do Chef.
 */
export function useChefRecommendation(
  options: UseChefRecommendationOptions = {}
): UseChefRecommendationReturn {
  const { autoFetch = true, refreshTrigger } = options;
  
  const [chefRecommendation, setChefRecommendation] = useState<ChefRecommendation | null>(null);
  const [loading, setLoading] = useState<boolean>(autoFetch);
  const [error, setError] = useState<string | null>(null);

  const fetchChefRecommendation = useCallback(
    async (refresh: boolean = false, showToast: boolean = true) => {
      setLoading(true);
      setError(null);

      try {
        const data = await api.getChefRecommendation({ refresh });
        setChefRecommendation(data);
        
        if (refresh && showToast && data) {
          toast.success('Recomendação do Chef atualizada!', {
            description: `${data.restaurant.name} foi escolhido especialmente para você.`,
          });
        }
      } catch (err: any) {
        const errorMessage =
          err.response?.data?.detail || err.message || 'Erro ao buscar recomendação do Chef';
        setError(errorMessage);
        
        // Se for erro 404, não mostrar toast (usuário pode não ter pedidos ainda)
        if (err.response?.status !== 404) {
          if (showToast) {
            toast.error('Erro ao buscar recomendação do Chef', {
              description: errorMessage,
            });
          }
        }
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Buscar recomendação automaticamente ao montar (se autoFetch = true)
  useEffect(() => {
    if (autoFetch) {
      fetchChefRecommendation(false, false); // Primeira busca silenciosa
    }
  }, [autoFetch, fetchChefRecommendation]);

  // Atualizar quando refreshTrigger mudar
  useEffect(() => {
    if (refreshTrigger !== undefined && refreshTrigger > 0) {
      fetchChefRecommendation(true, false); // Atualização silenciosa quando trigger muda
    }
  }, [refreshTrigger, fetchChefRecommendation]);

  const refresh = useCallback(
    async (showToast: boolean = true) => {
      await fetchChefRecommendation(true, showToast);
    },
    [fetchChefRecommendation]
  );

  return {
    chefRecommendation,
    loading,
    error,
    refresh,
  };
}

