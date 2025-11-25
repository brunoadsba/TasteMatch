/**
 * Cenários pré-configurados para simulação de pedidos.
 * Cada cenário representa um perfil de usuário diferente.
 */

export interface OrderSimulationData {
  cuisine_type: string; // Tipo de culinária para buscar restaurante
  total_amount: number; // Valor do pedido
  rating: number; // Avaliação (1-5)
  items?: string[]; // Itens do pedido (opcional)
}

export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  orders: OrderSimulationData[];
  color: string; // Cor para identificação visual
}

/**
 * Cenário: Vida Saudável (FIT)
 * Usuário que prefere opções saudáveis, nutritivas e leves
 */
export const FIT_SCENARIO: SimulationScenario = {
  id: 'fit',
  name: 'Vida Saudável',
  description: 'Simula 3 pedidos de opções saudáveis e nutritivas',
  icon: '🥗',
  color: 'green',
  orders: [
    {
      cuisine_type: 'Salada',
      total_amount: 35.90,
      rating: 5,
      items: ['Salada Caesar', 'Suco Verde']
    },
    {
      cuisine_type: 'Japonês',
      total_amount: 42.50,
      rating: 4,
      items: ['Poke Bowl Salmão', 'Chá Verde']
    },
    {
      cuisine_type: 'Saudável',
      total_amount: 28.90,
      rating: 5,
      items: ['Smoothie Bowl', 'Granola']
    }
  ]
};

/**
 * Cenário: Comfort Food (JUNK)
 * Usuário que prefere fast food, pizzas e comidas indulgentes
 */
export const COMFORT_SCENARIO: SimulationScenario = {
  id: 'comfort',
  name: 'Comfort Food',
  description: 'Simula 3 pedidos de fast food e comidas indulgentes',
  icon: '🍔',
  color: 'orange',
  orders: [
    {
      cuisine_type: 'Pizza',
      total_amount: 58.90,
      rating: 5,
      items: ['Pizza Grande Calabresa', 'Coca-Cola 2L']
    },
    {
      cuisine_type: 'Hamburgueria',
      total_amount: 45.90,
      rating: 4,
      items: ['X-Burger Completo', 'Batata Frita', 'Refrigerante']
    },
    {
      cuisine_type: 'Lanches',
      total_amount: 32.90,
      rating: 5,
      items: ['Porção de Nuggets', 'Açaí com Leite Condensado']
    }
  ]
};

/**
 * Cenário: Gourmet (PREMIUM)
 * Usuário que valoriza alta gastronomia e experiência gastronômica
 */
export const PREMIUM_SCENARIO: SimulationScenario = {
  id: 'premium',
  name: 'Gourmet',
  description: 'Simula 3 pedidos de alta gastronomia e experiências premium',
  icon: '🍷',
  color: 'purple',
  orders: [
    {
      cuisine_type: 'Francesa',
      total_amount: 125.00,
      rating: 5,
      items: ['Coq au Vin', 'Vinho Tinto', 'Crème Brûlée']
    },
    {
      cuisine_type: 'Japonês',
      total_amount: 98.90,
      rating: 5,
      items: ['Sashimi Premium', 'Temaki Especial', 'Sake']
    },
    {
      cuisine_type: 'Italiana',
      total_amount: 89.90,
      rating: 4,
      items: ['Risotto de Camarão', 'Tiramisù', 'Vinho Branco']
    }
  ]
};

/**
 * Lista de todos os cenários disponíveis
 */
export const SIMULATION_SCENARIOS: SimulationScenario[] = [
  FIT_SCENARIO,
  COMFORT_SCENARIO,
  PREMIUM_SCENARIO
];

/**
 * Busca um cenário por ID
 */
export function getScenarioById(id: string): SimulationScenario | undefined {
  return SIMULATION_SCENARIOS.find(scenario => scenario.id === id);
}

