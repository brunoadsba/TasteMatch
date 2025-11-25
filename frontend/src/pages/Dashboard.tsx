import { useAuth } from '@/hooks/useAuth';
import { useRecommendations } from '@/hooks/useRecommendations';
import { RestaurantCard } from '@/components/features/RestaurantCard';
import { RecommendationSkeletonGrid } from '@/components/features/RecommendationSkeleton';
import { OrderSimulator } from '@/components/features/OrderSimulator';
import { LLMInsightPanel } from '@/components/features/LLMInsightPanel';
import { AIReasoningLogComponent } from '@/components/features/AIReasoningLog';
import { useAIReasoning } from '@/hooks/useAIReasoning';
import { useResetSimulation } from '@/hooks/useResetSimulation';
import { Button } from '@/components/ui/button';
import { RefreshCw, LogOut, User, AlertCircle, History, Play, X, RotateCcw } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

export function Dashboard() {
  const { user, logout } = useAuth();
  const { recommendations, loading, error, refresh } = useRecommendations(12);
  const [refreshing, setRefreshing] = useState(false);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [simulatorOpen, setSimulatorOpen] = useState(false);
  const { logs, clearLogs } = useAIReasoning();
  const { resetSimulation, loading: resetting } = useResetSimulation();

  const handleResetSimulation = async () => {
    if (confirm('Deseja resetar toda a simulação? Isso removerá todos os pedidos simulados.')) {
      clearLogs();
      const success = await resetSimulation();
      if (success) {
        await refresh();
      }
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refresh();
    } catch (err) {
      // Erro já tratado no hook com toast
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        {/* Barra de Demo Mode */}
        {isDemoMode && (
          <div className="bg-blue-600 text-white px-4 py-2 text-center text-sm font-medium">
            🎯 Modo Demonstração Ativo - Dados simulados não serão salvos permanentemente
          </div>
        )}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">TasteMatch</h1>
              <p className="text-sm text-gray-500">Recomendações personalizadas para você</p>
            </div>
            <div className="flex items-center gap-4">
              {/* Toggle Modo Demo */}
              <Button
                variant={isDemoMode ? "default" : "outline"}
                size="sm"
                onClick={() => setIsDemoMode(!isDemoMode)}
                className={isDemoMode ? "bg-blue-600 hover:bg-blue-700" : ""}
              >
                {isDemoMode ? (
                  <>
                    <X className="w-4 h-4 mr-2" />
                    Sair do Modo Demo
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Modo Demo
                  </>
                )}
              </Button>
              
              {/* Botão Reset Simulação */}
              {isDemoMode && (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleResetSimulation}
                    disabled={resetting}
                    className="text-red-600 border-red-300 hover:bg-red-50"
                  >
                    <RotateCcw className={`w-4 h-4 mr-2 ${resetting ? 'animate-spin' : ''}`} />
                    Resetar
                  </Button>
                </>
              )}
              
              <Link to="/orders">
                <Button variant="outline" size="sm">
                  <History className="w-4 h-4 mr-2" />
                  Histórico
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
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Layout para Modo Demo: Sidebar com Terminal */}
        {isDemoMode && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
            {/* Painel LLM Insight */}
            <div className="lg:col-span-3">
              <LLMInsightPanel />
            </div>
            {/* Terminal de AI Reasoning */}
            <div className="lg:col-span-1">
              <AIReasoningLogComponent logs={logs} onClear={clearLogs} />
            </div>
          </div>
        )}

        {/* Painel LLM Insight (fora do modo demo - oculto ou menor) */}
        {!isDemoMode && (
          <div className="mb-6">
            <LLMInsightPanel />
          </div>
        )}

        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">
            Restaurantes Recomendados
          </h2>
          <div className="flex items-center gap-3">
            {isDemoMode && (
              <Button
                onClick={() => setSimulatorOpen(true)}
                disabled={refreshing || loading}
                variant="default"
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Play className="w-4 h-4 mr-2" />
                Simular Pedido
              </Button>
            )}
            <Button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              variant="outline"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing || loading ? 'animate-spin' : ''}`} />
              {refreshing ? 'Atualizando...' : 'Atualizar'}
            </Button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 font-medium text-sm">Erro ao carregar recomendações</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-3"
                onClick={handleRefresh}
                disabled={loading || refreshing}
              >
                Tentar novamente
              </Button>
            </div>
          </div>
        )}

        {loading && !refreshing ? (
          <>
            <div className="mb-4">
              <p className="text-gray-500 text-sm">Carregando suas recomendações personalizadas...</p>
            </div>
            <RecommendationSkeletonGrid count={6} />
          </>
        ) : !Array.isArray(recommendations) || recommendations.length === 0 ? (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Nenhuma recomendação disponível
              </h3>
              <p className="text-gray-500 mb-1">
                Ainda não temos dados suficientes para gerar recomendações personalizadas.
              </p>
              <p className="text-sm text-gray-400">
                Faça alguns pedidos para receber recomendações personalizadas baseadas no seu gosto!
              </p>
            </div>
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

      {/* Order Simulator Modal */}
      <OrderSimulator
        open={simulatorOpen}
        onOpenChange={setSimulatorOpen}
        onComplete={() => {
          // Atualizar recomendações após simulação
          handleRefresh();
        }}
      />
    </div>
  );
}

