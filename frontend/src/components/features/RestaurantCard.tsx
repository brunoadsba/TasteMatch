import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { RestaurantWithScore } from '@/types';
import { Star } from 'lucide-react';

interface RestaurantCardProps {
  restaurant: RestaurantWithScore;
  onViewInsight?: () => void;
}

export function RestaurantCard({ restaurant, onViewInsight }: RestaurantCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const formatPriceRange = (range?: string) => {
    if (!range) return 'N/A';
    const ranges: Record<string, string> = {
      low: 'R$ 15-30',
      medium: 'R$ 30-50',
      high: 'R$ 50+',
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
            <>
              <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                <p className="text-blue-900 line-clamp-2 mb-2">
                  {restaurant.insight}
                </p>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="text-blue-600 hover:text-blue-800 text-xs font-medium underline w-full text-left"
                >
                  Ver recomendação completa
                </button>
              </div>
              
              <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle className="text-2xl">
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
                      <div className="flex items-center gap-1 text-yellow-500">
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
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <h3 className="font-semibold text-blue-900 mb-3">
                        Por que recomendamos?
                      </h3>
                      <p className="text-blue-900 leading-relaxed">
                        {restaurant.insight}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4 pt-2">
                      <div>
                        <span className="text-sm text-muted-foreground">Faixa de preço:</span>
                        <p className="font-medium">{formatPriceRange(restaurant.price_range)}</p>
                      </div>
                      <div>
                        <span className="text-sm text-muted-foreground">Relevância:</span>
                        <p className="font-medium text-blue-600">
                          {(restaurant.similarity_score * 100).toFixed(0)}%
                        </p>
                      </div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </>
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

