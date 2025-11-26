import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { useChefRecommendation } from '@/hooks/useChefRecommendation';
import { Star, ChefHat, Sparkles, RefreshCw, ArrowDown, Brain, AlertCircle } from 'lucide-react';

interface ChefRecommendationCardProps {
  className?: string;
  refreshTrigger?: number;
  onViewReasoning?: () => void;
  onScrollToRecommendations?: () => void;
}

export function ChefRecommendationCard({
  className,
  refreshTrigger,
  onViewReasoning,
  onScrollToRecommendations,
}: ChefRecommendationCardProps) {
  const { chefRecommendation, loading, error, refresh } = useChefRecommendation({
    autoFetch: true,
    refreshTrigger,
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const formatPriceRange = (range?: string) => {
    if (!range) return 'N/A';
    const ranges: Record<string, string> = {
      low: 'R$ 15-30',
      medium: 'R$ 30-50',
      high: 'R$ 50+',
    };
    return ranges[range] || range;
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refresh(true);
    setIsRefreshing(false);
  };

  const handleScrollToRecommendations = () => {
    if (onScrollToRecommendations) {
      onScrollToRecommendations();
    } else {
      // Fallback: scroll para grid de recomendações
      const recommendationsSection = document.querySelector('[data-recommendations-section]');
      if (recommendationsSection) {
        recommendationsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  };

  // Loading state com Skeleton melhorado
  if (loading && !chefRecommendation) {
    return (
      <Card className={`border-2 border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900 dark:via-amber-950 dark:to-amber-900 ${className}`}>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between mb-2">
            <Skeleton className="h-7 w-40" />
            <Skeleton className="h-6 w-24" />
          </div>
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent className="space-y-5">
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <div className="flex items-center gap-3">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-4 rounded-full" />
              <Skeleton className="h-4 w-12" />
            </div>
          </div>
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-10 w-full" />
        </CardContent>
      </Card>
    );
  }

  // Error state (404 = sem recomendações disponíveis, mostrar mensagem amigável)
  if (error && !chefRecommendation) {
    const isNotFound = error.includes('404') || error.toLowerCase().includes('não encontrei');
    
    if (isNotFound) {
      return (
        <Card className={`border-2 border-amber-200 bg-gradient-to-br from-amber-50 to-orange-50 ${className}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-900">
              <ChefHat className="w-5 h-5" />
              Chef Recomenda
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-6">
              <p className="text-sm text-amber-800 mb-4">
                Ainda estou aprendendo seus gostos! Faça alguns pedidos para receber recomendações personalizadas.
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="border-amber-300 text-amber-900 hover:bg-amber-100"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Atualizar
              </Button>
            </div>
          </CardContent>
        </Card>
      );
    }
    
    // Outros erros
    return (
      <Card className={`border-2 border-red-200 bg-red-50 ${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-900">
            <ChefHat className="w-5 h-5" />
            Chef Recomenda
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-6">
            <p className="text-sm text-red-800 mb-4">
              Não encontrei recomendações no momento. Tente novamente em instantes.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={isRefreshing}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              Atualizar
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Sem recomendação (não deveria acontecer, mas tratar)
  if (!chefRecommendation) {
    return null;
  }

  const { restaurant, explanation, reasoning, confidence, similarity_score, has_insight = true } = chefRecommendation;

  return (
    <>
      <Card className={`border-2 border-amber-400 shadow-xl bg-gradient-to-br from-amber-100 via-orange-50 to-amber-100 dark:from-amber-900 dark:via-amber-950 dark:to-amber-900 ${className}`}>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between mb-2">
            <CardTitle className="flex items-center gap-2 text-amber-900 dark:text-amber-100 text-xl">
              <ChefHat className="w-6 h-6 fill-amber-600" />
              Chef Recomenda
            </CardTitle>
            <span className="px-2 py-1 bg-amber-100 text-amber-900 border border-amber-300 rounded-md text-xs font-semibold">
              {Math.round(confidence * 100)}% confiança
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-600" />
            <span className="text-xs text-amber-800 dark:text-amber-100 font-medium">Escolha personalizada</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Nome e Info do Restaurante */}
          <div>
            <h3 className="font-bold text-2xl text-gray-900 dark:text-gray-50 mb-2">{restaurant.name}</h3>
            <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-200 mb-3">
              <span className="capitalize font-medium">{restaurant.cuisine_type}</span>
              <span>•</span>
              <div className="flex items-center gap-1 text-yellow-600">
                <Star className="w-4 h-4 fill-current" />
                <span className="font-medium">{restaurant.rating.toFixed(1)}</span>
              </div>
              {restaurant.price_range && (
                <>
                  <span>•</span>
                  <span>{formatPriceRange(restaurant.price_range)}</span>
                </>
              )}
            </div>
          </div>

          {/* Explicação do Chef - destaque com menos truncamento */}
          <div className="bg-white/80 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-700 rounded-lg p-4 shadow-md">
            {!has_insight && (
              <div className="flex items-start gap-2 mb-3 p-2 bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded text-xs text-amber-800 dark:text-amber-200">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>Recomendação baseada em similaridade. Insight do Chef temporariamente indisponível.</span>
              </div>
            )}
            <p className="text-base text-gray-800 dark:text-amber-50 leading-relaxed line-clamp-5">
              {explanation}
            </p>
          </div>

          {/* Razões */}
          {reasoning && reasoning.length > 0 && (
            <div className="space-y-1">
              {reasoning.slice(0, 2).map((reason, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-gray-600">
                  <span className="text-amber-600 mt-0.5">✓</span>
                  <span>{reason}</span>
                </div>
              ))}
            </div>
          )}

          {/* Scores */}
          <div className="flex items-center justify-between pt-2 border-t border-amber-200">
            <span className="text-xs text-gray-500">Similaridade:</span>
            <span className="text-sm font-semibold text-amber-900">
              {Math.round(similarity_score * 100)}%
            </span>
          </div>

          {/* Botões */}
          <div className="space-y-2 pt-2">
            <Button
              onClick={() => setIsModalOpen(true)}
              className="w-full bg-amber-600 hover:bg-amber-700 text-white"
              size="sm"
              aria-label="Ver detalhes completos da recomendação do Chef"
            >
              Ver Recomendação Completa
            </Button>
            
            <div className="grid grid-cols-2 gap-2">
              {onScrollToRecommendations && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleScrollToRecommendations}
                  className="text-xs"
                  aria-label="Ver outras opções de restaurantes recomendados"
                >
                  <ArrowDown className="w-3 h-3 mr-1" aria-hidden="true" />
                  Outras Opções
                </Button>
              )}
              
              {onViewReasoning && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onViewReasoning}
                  className="text-xs"
                  disabled={!has_insight}
                  title={!has_insight ? "Raciocínio do Chef temporariamente indisponível" : "Ver raciocínio completo"}
                  aria-label={!has_insight ? "Raciocínio do Chef temporariamente indisponível" : "Ver raciocínio completo do Chef"}
                  aria-disabled={!has_insight}
                >
                  <Brain className="w-3 h-3 mr-1" aria-hidden="true" />
                  Raciocínio
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Modal com detalhes completos */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-2xl flex items-center gap-2">
              <ChefHat className="w-6 h-6 fill-amber-600" />
              {restaurant.name}
            </DialogTitle>
            <DialogDescription className="flex items-center gap-3 pt-2">
              <span className="capitalize text-base">{restaurant.cuisine_type}</span>
              {restaurant.location && (
                <>
                  <span>•</span>
                  <span>{restaurant.location}</span>
                </>
              )}
              <span>•</span>
              <div className="flex items-center gap-1 text-yellow-600">
                <Star className="w-4 h-4 fill-current" />
                <span className="text-base font-medium">{restaurant.rating.toFixed(1)}</span>
              </div>
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            {restaurant.description && (
              <div>
                <h3 className="font-semibold mb-2">Sobre o restaurante</h3>
                <p className="text-muted-foreground">{restaurant.description}</p>
              </div>
            )}
            
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <h3 className="font-semibold text-amber-900 mb-3 flex items-center gap-2">
                <ChefHat className="w-5 h-5 fill-amber-600" />
                Recomendação do Chef
              </h3>
              <p className="text-amber-900 leading-relaxed mb-4">{explanation}</p>
              
              {reasoning && reasoning.length > 0 && (
                <div className="mt-4 pt-4 border-t border-amber-200">
                  <h4 className="font-medium text-amber-900 mb-2 text-sm">Por que escolhi este restaurante:</h4>
                  <ul className="space-y-1">
                    {reasoning.map((reason, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-amber-800">
                        <span className="text-amber-600 mt-0.5">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <span className="text-sm text-muted-foreground">Faixa de preço:</span>
                <p className="font-medium">{formatPriceRange(restaurant.price_range)}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Similaridade:</span>
                <p className="font-medium text-amber-600">
                  {Math.round(similarity_score * 100)}%
                </p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Confiança:</span>
                <p className="font-medium text-amber-600">
                  {Math.round(confidence * 100)}%
                </p>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

