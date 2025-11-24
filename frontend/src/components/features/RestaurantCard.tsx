import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { RestaurantWithScore } from '@/types';
import { Star } from 'lucide-react';

interface RestaurantCardProps {
  restaurant: RestaurantWithScore;
  onViewInsight?: () => void;
}

export function RestaurantCard({ restaurant, onViewInsight }: RestaurantCardProps) {
  const formatPriceRange = (range?: string) => {
    if (!range) return 'N/A';
    const ranges: Record<string, string> = {
      low: 'R$',
      medium: 'R$ R$',
      high: 'R$ R$ R$',
    };
    return ranges[range] || range;
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl mb-1">{restaurant.name}</CardTitle>
            <CardDescription className="flex items-center gap-2">
              <span className="capitalize">{restaurant.cuisine_type}</span>
              {restaurant.location && (
                <>
                  <span>•</span>
                  <span>{restaurant.location}</span>
                </>
              )}
            </CardDescription>
          </div>
          <div className="flex items-center gap-1 text-yellow-500">
            <Star className="w-4 h-4 fill-current" />
            <span className="text-sm font-medium">{restaurant.rating.toFixed(1)}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col">
        {restaurant.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-2">
            {restaurant.description}
          </p>
        )}
        <div className="mt-auto space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Faixa de preço:</span>
            <span className="font-medium">{formatPriceRange(restaurant.price_range)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Relevância:</span>
            <span className="font-medium text-blue-600">
              {(restaurant.similarity_score * 100).toFixed(0)}%
            </span>
          </div>
          {restaurant.insight && (
            <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
              <p className="text-blue-900">{restaurant.insight}</p>
            </div>
          )}
          {onViewInsight && (
            <Button variant="outline" onClick={onViewInsight} className="w-full">
              Ver detalhes
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

