import { useOrders } from '@/hooks/useOrders';
import { OrderTable } from '@/components/features/OrderTable';
import { OrderCard } from '@/components/features/OrderCard';
import { Button } from '@/components/ui/button';
import { RefreshCw, Table2, Grid, LogOut, User } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AppHeader } from '@/components/layout';

type ViewMode = 'table' | 'cards';

export function Orders() {
  const { user, logout } = useAuth();
  const { orders, total, loading, error, refresh } = useOrders({ limit: 50 });
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refresh();
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header com AppHeader */}
      <AppHeader
        title="TasteMatch"
        subtitle="Histórico de pedidos"
      >
        <Link to="/dashboard">
          <Button variant="outline" size="sm">
            Dashboard
          </Button>
        </Link>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <User className="w-4 h-4" />
          <span>{user?.name}</span>
        </div>
        <Button variant="outline" onClick={logout} size="sm">
          <LogOut className="w-4 h-4 mr-2" />
          Sair
        </Button>
      </AppHeader>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controls */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-xl md:text-2xl font-semibold text-gray-900">
              Meus Pedidos
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Total: {total} pedido{total !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex items-center gap-2 w-full md:w-auto">
            {/* Toggle table/cards: apenas desktop */}
            <div className="hidden md:flex items-center gap-1 border rounded-md">
              <Button
                variant={viewMode === 'table' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('table')}
              >
                <Table2 className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === 'cards' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('cards')}
              >
                <Grid className="w-4 h-4" />
              </Button>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing || loading}
              className="w-full md:w-auto"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
          </div>
        </div>

        {/* Content */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {loading && !orders.length ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Carregando pedidos...</p>
          </div>
        ) : (
          <>
            {/* Tabela: apenas desktop quando viewMode === 'table' */}
            {viewMode === 'table' && (
              <div className="hidden md:block">
                <OrderTable orders={orders} />
              </div>
            )}
            
            {/* Cards: sempre em mobile, em desktop quando viewMode === 'cards' */}
            <div className={viewMode === 'table' ? 'block md:hidden' : 'block'}>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {orders.map((order) => (
                  <OrderCard key={order.id} order={order} />
                ))}
              </div>
            </div>
          </>
        )}

        {!loading && orders.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">Você ainda não fez nenhum pedido.</p>
            <Link to="/dashboard">
              <Button variant="outline" className="mt-4">
                Ver recomendações
              </Button>
            </Link>
          </div>
        )}
      </main>
    </div>
  );
}

