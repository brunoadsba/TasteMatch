import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { Recommendation } from '@/types';

interface UseRecommendationsReturn {
  recommendations: Recommendation[];
  loading: boolean;
  error: string | null;
  refresh: (showToast?: boolean) => Promise<void>;
}

export function useRecommendations(limit: number = 10): UseRecommendationsReturn {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = async (refreshCache: boolean = false, showToast: boolean = true) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRecommendations({ limit, refresh: refreshCache });
      // Garantir que sempre seja um array
      const recommendationsArray = Array.isArray(data) ? data : [];
      setRecommendations(recommendationsArray);
      
      if (refreshCache && recommendationsArray.length > 0 && showToast) {
        toast.success('Recomendações atualizadas!', {
          description: `${recommendationsArray.length} restaurante(s) encontrado(s).`,
        });
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao carregar recomendações';
      setError(errorMessage);
      setRecommendations([]);
      
      // Não mostrar toast de erro no carregamento inicial ou atualizações automáticas
      if (refreshCache && showToast) {
        toast.error('Falha ao atualizar recomendações', {
          description: 'Tente novamente em alguns instantes.',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [limit]);

  return {
    recommendations,
    loading,
    error,
    refresh: (showToast: boolean = true) => fetchRecommendations(true, showToast),
  };
}

