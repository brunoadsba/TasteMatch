import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { Recommendation } from '@/types';

interface UseRecommendationsReturn {
  recommendations: Recommendation[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useRecommendations(limit: number = 10): UseRecommendationsReturn {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = async (refreshCache: boolean = false) => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRecommendations({ limit, refresh: refreshCache });
      // Garantir que sempre seja um array
      setRecommendations(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar recomendações');
      setRecommendations([]);
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
    refresh: () => fetchRecommendations(true),
  };
}

