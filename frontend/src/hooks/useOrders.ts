import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import type { Order } from '@/types';

interface UseOrdersOptions {
  limit?: number;
  autoFetch?: boolean;
}

interface UseOrdersReturn {
  orders: Order[];
  total: number;
  loading: boolean;
  error: string | null;
  fetchOrders: (offset?: number) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useOrders(options: UseOrdersOptions = {}): UseOrdersReturn {
  const { limit = 20, autoFetch = true } = options;
  
  const [orders, setOrders] = useState<Order[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = async (offset: number = 0) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.getOrders({ limit, offset });
      setOrders(response.orders);
      setTotal(response.total);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Erro ao carregar pedidos';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    await fetchOrders(0);
    toast.success('Histórico atualizado');
  };

  useEffect(() => {
    if (autoFetch) {
      fetchOrders();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoFetch, limit]);

  return {
    orders,
    total,
    loading,
    error,
    fetchOrders,
    refresh,
  };
}

