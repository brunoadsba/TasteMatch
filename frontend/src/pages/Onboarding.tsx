import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { ChefHat, ArrowRight, ArrowLeft, Check } from 'lucide-react';
import type { OnboardingRequest } from '@/types';

// Opções de culinárias disponíveis
// Nota: Apenas culinárias que existem no banco de dados
const CUISINE_OPTIONS = [
  { id: 'italiana', label: 'Italiana', emoji: '🍝', description: 'Pizza, Massas, Risotto' },
  { id: 'japonesa', label: 'Japonesa', emoji: '🍣', description: 'Sushi, Sashimi, Ramen' },
  { id: 'brasileira', label: 'Brasileira', emoji: '🥘', description: 'Feijoada, Churrasco, Moqueca' },
  { id: 'mexicana', label: 'Mexicana', emoji: '🌮', description: 'Tacos, Burritos, Quesadillas' },
  { id: 'chinesa', label: 'Chinesa', emoji: '🥡', description: 'Yakisoba, Dim Sum, Pato' },
  { id: 'vegetariana', label: 'Vegetariana', emoji: '🥗', description: 'Saladas, Quinoa, Legumes' },
  { id: 'hamburgueria', label: 'Hamburgueria', emoji: '🍔', description: 'Burgers, Batatas, Milkshakes' },
  { id: 'americana', label: 'Americana', emoji: '🍗', description: 'BBQ, Wings, Comfort Food' },
  { id: 'cafeteria', label: 'Cafeteria', emoji: '☕', description: 'Cafés, Doces, Lanches' },
  { id: 'árabe', label: 'Árabe', emoji: '🥙', description: 'Shawarma, Kebab, Hummus' },
];

// Opções de preço
const PRICE_OPTIONS = [
  { id: 'low', label: 'Econômico', emoji: '💰', description: 'R$ 15-30 por pessoa' },
  { id: 'medium', label: 'Moderado', emoji: '💵', description: 'R$ 30-50 por pessoa' },
  { id: 'high', label: 'Gourmet', emoji: '💎', description: 'R$ 50+ por pessoa' },
];

// Opções de restrições
const DIETARY_OPTIONS = [
  { id: 'vegan', label: 'Vegano', emoji: '🌱' },
  { id: 'vegetarian', label: 'Vegetariano', emoji: '🥬' },
  { id: 'gluten-free', label: 'Sem Glúten', emoji: '🌾' },
  { id: 'lactose-free', label: 'Sem Lactose', emoji: '🥛' },
  { id: 'keto', label: 'Keto', emoji: '🥑' },
];

type OnboardingStep = 'cuisines' | 'price' | 'restrictions';

export function Onboarding() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('cuisines');
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);
  const [pricePreference, setPricePreference] = useState<string | null>(null);
  const [dietaryRestrictions, setDietaryRestrictions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleCuisineToggle = (cuisineId: string) => {
    setSelectedCuisines((prev) => {
      if (prev.includes(cuisineId)) {
        return prev.filter((id) => id !== cuisineId);
      } else if (prev.length < 5) {
        return [...prev, cuisineId];
      }
      return prev;
    });
  };

  const handlePriceSelect = (priceId: string) => {
    setPricePreference(priceId);
  };

  const handleRestrictionToggle = (restrictionId: string) => {
    setDietaryRestrictions((prev) => {
      if (prev.includes(restrictionId)) {
        return prev.filter((id) => id !== restrictionId);
      }
      return [...prev, restrictionId];
    });
  };

  const handleNext = () => {
    if (currentStep === 'cuisines') {
      if (selectedCuisines.length === 0) {
        toast.error('Selecione pelo menos uma culinária');
        return;
      }
      setCurrentStep('price');
    } else if (currentStep === 'price') {
      if (!pricePreference) {
        toast.error('Selecione uma faixa de preço');
        return;
      }
      setCurrentStep('restrictions');
    }
  };

  const handleBack = () => {
    if (currentStep === 'price') {
      setCurrentStep('cuisines');
    } else if (currentStep === 'restrictions') {
      setCurrentStep('price');
    }
  };

  const handleComplete = async () => {
    if (selectedCuisines.length === 0) {
      toast.error('Selecione pelo menos uma culinária');
      return;
    }

    setLoading(true);
    try {
      const request: OnboardingRequest = {
        selected_cuisines: selectedCuisines,
        price_preference: pricePreference as 'low' | 'medium' | 'high' | undefined,
        dietary_restrictions: dietaryRestrictions.length > 0 ? dietaryRestrictions : undefined,
      };

      const response = await api.completeOnboarding(request);

      if (response.success) {
        toast.success('Perfil de sabor criado!', {
          description: 'Agora você pode receber recomendações personalizadas.',
        });
        // Forçar refresh das recomendações após onboarding
        navigate('/dashboard', { state: { refreshRecommendations: true } });
      } else {
        toast.warning('Onboarding concluído', {
          description: response.message,
        });
        navigate('/dashboard', { state: { refreshRecommendations: true } });
      }
    } catch (error: any) {
      toast.error('Erro ao criar perfil', {
        description: error.response?.data?.detail || 'Tente novamente em instantes.',
      });
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    if (currentStep === 'cuisines') return selectedCuisines.length > 0;
    if (currentStep === 'price') return pricePreference !== null;
    return true; // restrictions é opcional
  };

  const getStepTitle = () => {
    switch (currentStep) {
      case 'cuisines':
        return 'O que te dá água na boca?';
      case 'price':
        return 'Qual a sua vibe hoje?';
      case 'restrictions':
        return 'Alguma restrição alimentar?';
      default:
        return '';
    }
  };

  const getStepDescription = () => {
    switch (currentStep) {
      case 'cuisines':
        return 'Selecione até 5 tipos de culinária que você mais gosta';
      case 'price':
        return 'Escolha a faixa de preço que você prefere';
      case 'restrictions':
        return 'Selecione suas restrições alimentares (opcional)';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-4">
      <Card className="w-full max-w-3xl">
        <CardHeader className="text-center pb-6">
          <div className="flex items-center justify-center gap-2 mb-4">
            <ChefHat className="w-8 h-8 fill-amber-600" />
            <CardTitle className="text-3xl">Crie seu Perfil de Sabor</CardTitle>
          </div>
          <CardDescription className="text-base">
            {getStepTitle()}
          </CardDescription>
          <p className="text-sm text-muted-foreground mt-2">{getStepDescription()}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Indicador de Progresso */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {(['cuisines', 'price', 'restrictions'] as OnboardingStep[]).map((step, index) => (
              <div key={step} className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                    currentStep === step
                      ? 'bg-amber-600 text-white'
                      : ['cuisines', 'price', 'restrictions'].indexOf(currentStep) > index
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                  }`}
                >
                  {['cuisines', 'price', 'restrictions'].indexOf(currentStep) > index ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < 2 && (
                  <div
                    className={`w-12 h-1 mx-1 transition-colors ${
                      ['cuisines', 'price', 'restrictions'].indexOf(currentStep) > index
                        ? 'bg-green-500'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          {/* Conteúdo da Etapa */}
          {currentStep === 'cuisines' && (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {CUISINE_OPTIONS.map((cuisine) => {
                const isSelected = selectedCuisines.includes(cuisine.id);
                const isDisabled = !isSelected && selectedCuisines.length >= 5;
                return (
                  <button
                    key={cuisine.id}
                    onClick={() => handleCuisineToggle(cuisine.id)}
                    disabled={isDisabled}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      isSelected
                        ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/20 shadow-md'
                        : isDisabled
                        ? 'border-gray-200 bg-gray-50 dark:bg-gray-800 opacity-50 cursor-not-allowed'
                        : 'border-gray-200 bg-white dark:bg-gray-800 hover:border-amber-300 hover:shadow-sm'
                    }`}
                    aria-label={`Selecionar ${cuisine.label}`}
                    aria-pressed={isSelected}
                  >
                    <div className="text-3xl mb-2">{cuisine.emoji}</div>
                    <div className="font-semibold text-sm mb-1">{cuisine.label}</div>
                    <div className="text-xs text-muted-foreground">{cuisine.description}</div>
                    {isSelected && (
                      <div className="mt-2 flex items-center gap-1 text-amber-600 text-xs font-medium">
                        <Check className="w-3 h-3" />
                        Selecionado
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {currentStep === 'price' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {PRICE_OPTIONS.map((price) => {
                const isSelected = pricePreference === price.id;
                return (
                  <button
                    key={price.id}
                    onClick={() => handlePriceSelect(price.id)}
                    className={`p-6 rounded-lg border-2 transition-all text-center ${
                      isSelected
                        ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/20 shadow-md'
                        : 'border-gray-200 bg-white dark:bg-gray-800 hover:border-amber-300 hover:shadow-sm'
                    }`}
                    aria-label={`Selecionar ${price.label}`}
                    aria-pressed={isSelected}
                  >
                    <div className="text-4xl mb-3">{price.emoji}</div>
                    <div className="font-semibold text-lg mb-2">{price.label}</div>
                    <div className="text-sm text-muted-foreground">{price.description}</div>
                    {isSelected && (
                      <div className="mt-3 flex items-center justify-center gap-1 text-amber-600 text-sm font-medium">
                        <Check className="w-4 h-4" />
                        Selecionado
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {currentStep === 'restrictions' && (
            <div>
              <p className="text-sm text-muted-foreground mb-4 text-center">
                Selecione suas restrições alimentares (opcional)
              </p>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {DIETARY_OPTIONS.map((restriction) => {
                  const isSelected = dietaryRestrictions.includes(restriction.id);
                  return (
                    <button
                      key={restriction.id}
                      onClick={() => handleRestrictionToggle(restriction.id)}
                      className={`p-4 rounded-lg border-2 transition-all text-center ${
                        isSelected
                          ? 'border-amber-500 bg-amber-50 dark:bg-amber-900/20 shadow-md'
                          : 'border-gray-200 bg-white dark:bg-gray-800 hover:border-amber-300 hover:shadow-sm'
                      }`}
                      aria-label={`Selecionar ${restriction.label}`}
                      aria-pressed={isSelected}
                    >
                      <div className="text-2xl mb-2">{restriction.emoji}</div>
                      <div className="font-medium text-xs">{restriction.label}</div>
                      {isSelected && (
                        <div className="mt-1 flex items-center justify-center gap-1 text-amber-600">
                          <Check className="w-3 h-3" />
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Botões de Navegação */}
          <div className="flex items-center justify-between pt-6 border-t">
            <div className="flex items-center gap-2">
              {currentStep !== 'cuisines' && (
                <Button
                  variant="outline"
                  onClick={handleBack}
                  disabled={loading}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Voltar
                </Button>
              )}
              {currentStep === 'cuisines' && (
                <Button
                  variant="ghost"
                  onClick={() => navigate('/dashboard')}
                  disabled={loading}
                  className="text-muted-foreground"
                >
                  Pular por enquanto
                </Button>
              )}
            </div>

            {currentStep === 'restrictions' ? (
              <Button
                onClick={handleComplete}
                disabled={loading || selectedCuisines.length === 0}
                className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700"
              >
                {loading ? 'Criando perfil...' : 'Finalizar'}
                {!loading && <ArrowRight className="w-4 h-4" />}
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                disabled={!canProceed() || loading}
                className="flex items-center gap-2 bg-amber-600 hover:bg-amber-700"
              >
                Próximo
                <ArrowRight className="w-4 h-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

