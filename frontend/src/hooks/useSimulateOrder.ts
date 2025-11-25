import { useState } from 'react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { OrderCreate } from '@/types';

interface UseSimulateOrderReturn {
  simulateOrder: (orderData: OrderCreate) => Promise<boolean>;
  loading: boolean;
  error: string | null;
}

/**
 * Hook para criar pedidos simulados.
 * Faz POST para /api/orders com is_simulation: true
 */
export function useSimulateOrder(): UseSimulateOrderReturn {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const simulateOrder = async (orderData: OrderCreate): Promise<boolean> => {
    try {
      setLoading(true);
      setError(null);

      // Adicionar flag is_simulation: true
      const simulatedOrderData: OrderCreate & { is_simulation?: boolean } = {
        ...orderData,
        is_simulation: true,
      };

      await api.createOrder(simulatedOrderData);
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao criar pedido simulado';
      setError(errorMessage);
      toast.error('Falha ao criar pedido simulado', {
        description: errorMessage,
      });
      return false;
    } finally {
      setLoading(false);
    }
  };

  return {
    simulateOrder,
    loading,
    error,
  };
}

