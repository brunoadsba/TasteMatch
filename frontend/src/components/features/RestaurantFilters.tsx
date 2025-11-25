import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Search, X } from 'lucide-react';

export interface RestaurantFilters {
  cuisine_type?: string;
  min_rating?: number;
  price_range?: string;
  search?: string;
  sort_by?: string;
}

interface RestaurantFiltersProps {
  filters: RestaurantFilters;
  onFiltersChange: (filters: RestaurantFilters) => void;
  onReset: () => void;
}

const CUISINE_TYPES = [
  'Italiana',
  'Japonesa',
  'Brasileira',
  'Chinesa',
  'Mexicana',
  'Indiana',
  'Francesa',
  'Árabe',
  'Americana',
  'Vegetariana',
];

const PRICE_RANGES = [
  { value: 'low', label: 'Baixo (R$)' },
  { value: 'medium', label: 'Médio (R$ R$)' },
  { value: 'high', label: 'Alto (R$ R$ R$)' },
];

const SORT_OPTIONS = [
  { value: 'rating_desc', label: 'Rating (maior)' },
  { value: 'rating_asc', label: 'Rating (menor)' },
  { value: 'name_asc', label: 'Nome (A-Z)' },
  { value: 'name_desc', label: 'Nome (Z-A)' },
];

export function RestaurantFiltersComponent({
  filters,
  onFiltersChange,
  onReset,
}: RestaurantFiltersProps) {
  const updateFilter = (key: keyof RestaurantFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value || undefined });
  };

  const hasActiveFilters =
    filters.cuisine_type ||
    filters.min_rating ||
    filters.price_range ||
    filters.search ||
    filters.sort_by;

  return (
    <Card>
      <CardContent className="p-4">
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              type="text"
              placeholder="Buscar restaurantes..."
              value={filters.search || ''}
              onChange={(e) => updateFilter('search', e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Cuisine Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Culinária
              </label>
              <select
                value={filters.cuisine_type || ''}
                onChange={(e) => updateFilter('cuisine_type', e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos</option>
                {CUISINE_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Min Rating */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rating Mínimo
              </label>
              <select
                value={filters.min_rating?.toString() || ''}
                onChange={(e) =>
                  updateFilter('min_rating', e.target.value ? parseFloat(e.target.value) : undefined)
                }
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos</option>
                <option value="3.0">3.0+</option>
                <option value="3.5">3.5+</option>
                <option value="4.0">4.0+</option>
                <option value="4.5">4.5+</option>
              </select>
            </div>

            {/* Price Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Faixa de Preço
              </label>
              <select
                value={filters.price_range || ''}
                onChange={(e) => updateFilter('price_range', e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Todos</option>
                {PRICE_RANGES.map((range) => (
                  <option key={range.value} value={range.value}>
                    {range.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ordenar Por
              </label>
              <select
                value={filters.sort_by || 'rating_desc'}
                onChange={(e) => updateFilter('sort_by', e.target.value)}
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Reset Button */}
          {hasActiveFilters && (
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={onReset}>
                <X className="w-4 h-4 mr-2" />
                Limpar Filtros
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

