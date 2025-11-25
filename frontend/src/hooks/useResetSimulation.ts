import { useState } from 'react';
import { toast } from 'sonner';
import { api } from '@/lib/api';

interface UseResetSimulationReturn {
  resetSimulation: () => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

/**
 * Hook para resetar simulação de pedidos.
 * Remove todos os pedidos simulados do usuário autenticado.
 */
export function useResetSimulation(): UseResetSimulationReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resetSimulation = async (): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      // Chamar endpoint DELETE /api/orders/simulation
      const response = await api.resetSimulation();
      
      const deletedCount = response.deleted;
      
      toast.success('Simulação resetada', {
        description: `${deletedCount} pedido(s) simulado(s) removido(s).`,
      });
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao resetar simulação';
      setError(errorMessage);
      toast.error('Falha ao resetar simulação', {
        description: errorMessage,
      });
      return false;
    } finally {
      setLoading(false);
    }
  };

  return {
    resetSimulation,
    loading,
    error,
  };
}

