import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, Sparkles } from 'lucide-react';
import { useOrders } from '@/hooks/useOrders';
import { useRecommendations } from '@/hooks/useRecommendations';

interface LLMInsightPanelProps {
  className?: string;
}

export function LLMInsightPanel({ className }: LLMInsightPanelProps) {
  const { orders, total: totalOrders } = useOrders({ limit: 100, autoFetch: true });
  const { recommendations } = useRecommendations(1); // Pega apenas a primeira recomendação para análise

  // Filtrar apenas pedidos simulados
  const simulatedOrders = orders.filter(order => order.is_simulation);
  const simulatedCount = simulatedOrders.length;
  const realOrdersCount = totalOrders - simulatedCount;

  // Análise básica de preferências (pode ser melhorada com dados reais do backend)
  const analyzePreferences = () => {
    if (simulatedCount === 0 && realOrdersCount === 0) {
      return {
        stage: 'cold_start',
        message: 'Seu perfil está em construção. As recomendações atuais são baseadas na popularidade geral e sazonalidade.',
        details: [],
      };
    }

    if (simulatedCount < 5) {
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

    // Análise avançada (simulada)
    const topRecommendation = recommendations[0];
    const avgRating = simulatedOrders
      .filter(o => o.rating)
      .reduce((sum, o) => sum + (o.rating || 0), 0) / simulatedOrders.filter(o => o.rating).length;

    return {
      stage: 'personalized',
      message: `Com base em seus ${simulatedCount} pedidos simulados, identificamos um perfil personalizado.`,
      details: [
        topRecommendation
          ? `• Preferência forte: ${topRecommendation.restaurant.cuisine_type}`
          : '• Perfil em análise',
        `• Avaliação média: ${avgRating ? avgRating.toFixed(1) : 'N/A'}`,
        '• Sistema confiante nas recomendações',
        topRecommendation
          ? `• Recomendação principal: ${topRecommendation.restaurant.name}`
          : '• Gerando recomendações personalizadas',
      ],
    };
  };

  const insight = analyzePreferences();

  return (
    <Card className={className}>
      <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 border-b">
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
            <div className="flex items-center gap-2">
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
            </div>
          )}

          {/* Mensagem Principal */}
          <p className="text-sm text-gray-700 leading-relaxed">{insight.message}</p>

          {/* Detalhes */}
          {insight.details.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
              <h4 className="text-xs font-semibold text-blue-900 uppercase tracking-wide">
                Detalhes da Análise
              </h4>
              <ul className="space-y-1 text-sm text-blue-800">
                {insight.details.map((detail, index) => (
                  <li key={index}>{detail}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Informação Adicional */}
          {insight.stage === 'cold_start' && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800">
              💡 <strong>Dica:</strong> Ative o Modo Demo e simule alguns pedidos para ver o sistema aprender suas preferências em tempo real!
            </div>
          )}

          {insight.stage === 'learning' && simulatedCount > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-800">
              📊 Faltam <strong>{5 - simulatedCount}</strong> pedido(s) simulado(s) para personalização completa.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

