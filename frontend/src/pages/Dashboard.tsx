import { useAuth } from '@/hooks/useAuth';
import { useRecommendations } from '@/hooks/useRecommendations';
import { RestaurantCard } from '@/components/features/RestaurantCard';
import { RecommendationSkeletonGrid } from '@/components/features/RecommendationSkeleton';
import { OrderSimulator } from '@/components/features/OrderSimulator';
import { LLMInsightPanel } from '@/components/features/LLMInsightPanel';
import { ChefRecommendationCard } from '@/components/features/ChefRecommendationCard';
import { ChefReasoningModal } from '@/components/features/ChefReasoningModal';
import { useResetSimulation } from '@/hooks/useResetSimulation';
import { Button } from '@/components/ui/button';
import { RefreshCw, LogOut, User, AlertCircle, History, Play, X, RotateCcw } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { toast } from 'sonner';
import { AppHeader } from '@/components/layout';

export function Dashboard() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const { recommendations, loading, error, refresh } = useRecommendations(12);
  const [refreshing, setRefreshing] = useState(false);
  
  // Forçar refresh das recomendações se vier do onboarding
  useEffect(() => {
    if (location.state?.refreshRecommendations) {
      refresh(false); // Refresh sem toast (já tem toast do onboarding)
      // Limpar state para evitar refresh em navegações futuras
      window.history.replaceState({}, document.title);
    }
  }, [location.state, refresh]);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [simulatorOpen, setSimulatorOpen] = useState(false);
  const [ordersRefreshTrigger, setOrdersRefreshTrigger] = useState(0); // Trigger para atualizar pedidos
  const [reasoningModalOpen, setReasoningModalOpen] = useState(false); // Modal de raciocínio
  const { resetSimulation, loading: resetting } = useResetSimulation();

  const handleResetSimulation = async () => {
    if (confirm('Deseja resetar toda a simulação? Isso removerá todos os pedidos simulados.')) {
      const success = await resetSimulation();
      if (success) {
        toast.success('Histórico de simulações resetado', {
          description: 'Todas as simulações foram removidas. Você pode começar novamente.',
        });
        await refresh();
        // Atualizar trigger para atualizar o painel de pedidos
        setOrdersRefreshTrigger(prev => prev + 1);
      } else {
        toast.error('Erro ao resetar simulações', {
          description: 'Tente novamente em instantes.',
        });
      }
    }
  };

  // Função para scroll até o grid de recomendações
  const handleScrollToRecommendations = () => {
    const recommendationsSection = document.querySelector('[data-recommendations-section]');
    if (recommendationsSection) {
      recommendationsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Callback para atualizar pedidos quando um novo pedido é criado
  const handleOrderCreated = () => {
    setOrdersRefreshTrigger(prev => prev + 1);
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
    <div className="min-h-screen bg-background text-foreground">
      {/* Header com AppHeader */}
      <AppHeader
        title="TasteMatch"
        subtitle="Recomendações personalizadas para você"
        isDemoMode={isDemoMode}
        demoModeBar={
          isDemoMode ? (
            <span>Modo Demo Ativo</span>
          ) : undefined
        }
        mobileMenuSections={[
          // Seção 1: Modo Demo
          {
            label: isDemoMode ? 'Modo Demo' : undefined,
            items: (
              <>
                <Button
                  variant={isDemoMode ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    if (isDemoMode) {
                      localStorage.removeItem('demo-banner-dismissed');
                      toast.success('Modo demo encerrado', {
                        description: 'Faça login para continuar usando o TasteMatch.',
                        duration: 3000,
                      });
                    } else {
                      toast.info('Modo demo ativado', {
                        description: 'Explore o TasteMatch. Dados simulados não serão salvos.',
                        duration: 4000,
                      });
                    }
                    setIsDemoMode(!isDemoMode);
                  }}
                  className={isDemoMode ? "bg-blue-600 hover:bg-blue-700 text-white" : "w-full"}
                >
                  {isDemoMode ? (
                    <>
                      <X className="w-4 h-4 mr-2" />
                      Sair do Modo Demo
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Ativar Modo Demo
                    </>
                  )}
                </Button>
                {isDemoMode && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleResetSimulation}
                    disabled={resetting}
                    className="text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-700 dark:hover:bg-red-950"
                  >
                    <RotateCcw className={`w-4 h-4 mr-2 ${resetting ? 'animate-spin' : ''}`} />
                    Resetar Simulação
                  </Button>
                )}
              </>
            ),
          },
          // Seção 2: Navegação
          {
            label: 'Navegação',
            items: (
              <Link to="/orders" className="w-full">
                <Button variant="outline" size="sm" className="w-full">
                  <History className="w-4 h-4 mr-2" />
                  Histórico de Pedidos
                </Button>
              </Link>
            ),
          },
          // Seção 3: Conta
          {
            label: 'Conta',
            items: (
              <>
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 px-3 py-2">
                  <User className="w-4 h-4" />
                  <span>{user?.name}</span>
                </div>
                <Button variant="outline" onClick={logout} size="sm" className="w-full">
                  <LogOut className="w-4 h-4 mr-2" />
                  Sair
                </Button>
              </>
            ),
          },
        ]}
      >
        {/* Toggle Tema Claro/Escuro */}
        <ThemeToggle />

        {/* Toggle Modo Demo - Sem Tooltip (melhor para mobile) */}
        <Button
          variant={isDemoMode ? "default" : "outline"}
          size="sm"
          onClick={() => {
            if (isDemoMode) {
              // Resetar banner dismissed ao sair do modo demo
              localStorage.removeItem('demo-banner-dismissed');
              toast.success('Modo demo encerrado', {
                description: 'Faça login para continuar usando o TasteMatch.',
                duration: 3000,
              });
            } else {
              toast.info('Modo demo ativado', {
                description: 'Explore o TasteMatch. Dados simulados não serão salvos.',
                duration: 4000,
              });
            }
            setIsDemoMode(!isDemoMode);
          }}
          className={isDemoMode ? "bg-blue-600 hover:bg-blue-700" : ""}
          aria-label={isDemoMode ? "Sair do modo demo" : "Ativar modo demo"}
        >
          {isDemoMode ? (
            <>
              <X className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Sair do Modo Demo</span>
              <span className="sm:hidden">Sair Demo</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Modo Demo</span>
              <span className="sm:hidden">Demo</span>
            </>
          )}
        </Button>
        
        {/* Botão Reset Simulação */}
        {isDemoMode && (
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
      </AppHeader>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Layout para Modo Demo: Layout Vertical com Chef em Destaque */}
        {isDemoMode && (
          <div className="space-y-6 mb-6">
            {/* Chef Recomenda em destaque (Hero) */}
            <div className="max-w-4xl mx-auto w-full">
              <ChefRecommendationCard
                refreshTrigger={ordersRefreshTrigger}
                onViewReasoning={() => setReasoningModalOpen(true)}
                onScrollToRecommendations={handleScrollToRecommendations}
                className="w-full"
              />
            </div>

            {/* Análise de Perfil abaixo como contexto */}
            <div className="max-w-4xl mx-auto w-full">
              <LLMInsightPanel refreshTrigger={ordersRefreshTrigger} />
            </div>
          </div>
        )}

        {/* Painel LLM Insight (fora do modo demo - oculto ou menor) */}
        {!isDemoMode && (
          <div className="mb-6">
            <LLMInsightPanel refreshTrigger={ordersRefreshTrigger} />
          </div>
        )}

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
          <h2 className="text-xl md:text-2xl font-semibold">
            Restaurantes Recomendados
          </h2>
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {isDemoMode && (
              <Button
                onClick={() => setSimulatorOpen(true)}
                disabled={refreshing || loading}
                variant="default"
                className="bg-blue-600 hover:bg-blue-700 w-full md:w-auto"
              >
                <Play className="w-4 h-4 mr-2" />
                Simular Pedido
              </Button>
            )}
            <Button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              variant="outline"
              className="w-full md:w-auto"
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
          <div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            data-recommendations-section
          >
            {/* Filtrar duplicatas no frontend: primeiro por ID, depois por nome (normalizado) */}
            {Array.from(
              new Map(
                recommendations.map(rec => [
                  `${rec.restaurant.id}-${rec.restaurant.name.toLowerCase().trim()}`,
                  rec
                ])
              ).values()
            ).map((rec) => (
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
          // Atualizar trigger para atualizar o painel de pedidos
          setOrdersRefreshTrigger(prev => prev + 1);
        }}
        onOrderCreated={handleOrderCreated}
      />

      {/* Modal de Raciocínio do Chef (opcional) */}
      {isDemoMode && (
        <ChefReasoningModal
          open={reasoningModalOpen}
          onOpenChange={setReasoningModalOpen}
        />
      )}
    </div>
  );
}

