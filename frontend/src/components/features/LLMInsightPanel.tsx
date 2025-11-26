import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Brain, Sparkles } from 'lucide-react';
import { useOrders } from '@/hooks/useOrders';
import { useRecommendations } from '@/hooks/useRecommendations';
import { useEffect, useRef } from 'react';

interface LLMInsightPanelProps {
  className?: string;
  refreshTrigger?: number; // Prop para forçar refresh quando mudar
}

export function LLMInsightPanel({ className, refreshTrigger }: LLMInsightPanelProps) {
  const { orders, refresh: refreshOrders, loading: ordersLoading } = useOrders({ limit: 100, autoFetch: true });
  const { recommendations, refresh: refreshRecommendations, loading: recommendationsLoading } = useRecommendations(1); // Pega apenas a primeira recomendação para análise
  const previousRefreshTrigger = useRef(refreshTrigger);
  
  const isLoading = ordersLoading || recommendationsLoading;

  // Atualizar pedidos quando refreshTrigger mudar
  useEffect(() => {
    if (refreshTrigger !== undefined && refreshTrigger !== previousRefreshTrigger.current) {
      previousRefreshTrigger.current = refreshTrigger;
      // Atualizar pedidos e recomendações silenciosamente (sem toast) para evitar spam
      refreshOrders();
      refreshRecommendations(false); // Não mostrar toast em atualizações automáticas
    }
  }, [refreshTrigger, refreshOrders, refreshRecommendations]);

  // Filtrar pedidos simulados e reais separadamente
  // Tratar is_simulation como boolean (pode ser undefined, null, false, ou true)
  const simulatedOrders = orders.filter(order => order.is_simulation === true);
  const realOrders = orders.filter(order => order.is_simulation !== true);
  const simulatedCount = simulatedOrders.length;
  const realOrdersCount = realOrders.length;
  const totalOrdersCount = simulatedCount + realOrdersCount;

  // Análise básica de preferências (pode ser melhorada com dados reais do backend)
  const analyzePreferences = () => {
    // IMPORTANTE: Se não há pedidos simulados, sempre mostrar cold_start
    // Não importa se há pedidos reais ou não - sem simulados = cold_start
    if (simulatedCount === 0) {
      return {
        stage: 'cold_start',
        message: 'Seu perfil está em construção. As recomendações atuais são baseadas na popularidade geral e sazonalidade.',
        details: [],
      };
    }

    // Apenas mostrar learning/personalized se houver pedidos simulados (verificação explícita)
    if (simulatedCount > 0 && simulatedCount < 5) {
      return {
        stage: 'learning',
        message: `Em evolução - ${simulatedCount} pedido(s) simulado(s) processado(s). Continue simulando pedidos para personalização completa.`,
        details: [
          `• ${simulatedCount} pedido(s) simulado(s) analisado(s)`,
          '• Sistema aprendendo suas preferências',
          '• Recomendações melhorando progressivamente',
        ],
      };
    }

    // Análise avançada (simulada) - só chega aqui se simulatedCount >= 5
    const avgRating = simulatedOrders
      .filter(o => o.rating)
      .reduce((sum, o) => sum + (o.rating || 0), 0) / simulatedOrders.filter(o => o.rating).length;

    const topRecommendation = recommendations[0];

    return {
      stage: 'personalized',
      message: `Com base em seus ${simulatedCount} pedidos simulados, identificamos um perfil personalizado.`,
      details: [
        topRecommendation
          ? `• Preferência forte: ${topRecommendation.restaurant.cuisine_type}`
          : '• Perfil em análise',
        `• Avaliação média dos seus pedidos: ${avgRating ? avgRating.toFixed(1) : 'N/A'}`,
        '• Status: Otimizando personalização',
        '• Nível de confiança do modelo: Alto',
      ],
    };
  };

  const insight = analyzePreferences();

  // Loading state com Skeleton
  if (isLoading && orders.length === 0) {
    return (
      <Card className={className}>
        <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-slate-900 dark:to-indigo-900 border-b border-border">
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-24 w-full rounded-lg" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-slate-900 dark:to-indigo-900 border-b border-border">
        <CardTitle className="flex items-center gap-2 text-lg">
          <div className="relative">
            <Brain className="w-5 h-5 text-blue-600" />
            <Sparkles className="w-3 h-3 text-purple-500 absolute -top-1 -right-1" />
          </div>
          <span>Análise de Perfil e Sugestão</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Status Badge - apenas para learning e personalized */}
          {(insight.stage === 'learning' || insight.stage === 'personalized') && (
            <div className="flex items-center gap-2 flex-wrap">
              {insight.stage === 'learning' && (
                <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full animate-pulse">
                  🔄 Aprendendo...
                </span>
              )}
              {insight.stage === 'personalized' && (
                <span className="px-3 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                  ✨ Personalizado
                </span>
              )}
              {totalOrdersCount > 0 && (
                <span className="text-xs text-gray-500">
                  {totalOrdersCount} pedido{totalOrdersCount !== 1 ? 's' : ''} total
                </span>
              )}
            </div>
          )}

          {/* Mensagem Principal */}
          <p className="text-sm text-foreground leading-relaxed">{insight.message}</p>

          {/* Detalhes */}
          {insight.details.length > 0 && (
            <div className="bg-blue-50 dark:bg-slate-900/60 border border-blue-200 dark:border-slate-700 rounded-lg p-4 space-y-2">
              <h4 className="text-xs font-semibold text-blue-900 dark:text-blue-100 uppercase tracking-wide">
                Detalhes da Análise
              </h4>
              <ul className="space-y-1 text-sm text-blue-800 dark:text-blue-100">
                {insight.details.map((detail, index) => (
                  <li key={index}>{detail}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Informação Adicional */}
          {insight.stage === 'cold_start' && (
            <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-xs text-amber-800 dark:text-amber-200">
              💡 <strong>Dica:</strong> Ative o Modo Demo e simule alguns pedidos para ver o sistema aprender suas preferências em tempo real!
            </div>
          )}

          {insight.stage === 'learning' && simulatedCount > 0 && (
            <div className="space-y-3">
              {/* Barra de Progresso Visual */}
              <div className="bg-blue-50 dark:bg-slate-900/60 border border-blue-200 dark:border-slate-700 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-blue-900 dark:text-blue-100">Progresso de Personalização</span>
                  <span className="text-xs text-blue-700 dark:text-blue-200 font-semibold">{simulatedCount}/5</span>
                </div>
                <div className="w-full bg-blue-200 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 dark:from-blue-400 dark:to-blue-500 h-2.5 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${Math.min((simulatedCount / 5) * 100, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-blue-800 dark:text-blue-100 mt-2">
                  📊 Faltam <strong>{5 - simulatedCount}</strong> pedido(s) simulado(s) para personalização completa.
                </p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

