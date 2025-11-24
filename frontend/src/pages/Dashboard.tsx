import { useAuth } from '@/hooks/useAuth';
import { useRecommendations } from '@/hooks/useRecommendations';
import { RestaurantCard } from '@/components/features/RestaurantCard';
import { Button } from '@/components/ui/button';
import { RefreshCw, LogOut, User } from 'lucide-react';
import { useState } from 'react';

export function Dashboard() {
  const { user, logout } = useAuth();
  const { recommendations, loading, error, refresh } = useRecommendations(12);
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    await refresh();
    setRefreshing(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">TasteMatch</h1>
              <p className="text-sm text-gray-500">Recomendações personalizadas para você</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <User className="w-4 h-4" />
                <span>{user?.name}</span>
              </div>
              <Button variant="outline" onClick={logout} size="sm">
                <LogOut className="w-4 h-4 mr-2" />
                Sair
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">
            Restaurantes Recomendados
          </h2>
          <Button
            onClick={handleRefresh}
            disabled={refreshing || loading}
            variant="outline"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing || loading ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {loading && !refreshing ? (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Carregando recomendações...</p>
          </div>
        ) : !Array.isArray(recommendations) || recommendations.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Nenhuma recomendação disponível.</p>
            <p className="text-sm text-gray-400 mt-2">
              Faça alguns pedidos para receber recomendações personalizadas!
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((rec) => (
              <RestaurantCard
                key={rec.restaurant.id}
                restaurant={{
                  ...rec.restaurant,
                  similarity_score: rec.similarity_score,
                  insight: rec.insight,
                }}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

