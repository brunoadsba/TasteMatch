// Tipos TypeScript correspondentes aos modelos Python do backend

export interface User {
  id: number;
  email: string;
  name: string;
  created_at: string;
}

export interface UserCreate {
  email: string;
  name: string;
  password: string;
}

export interface UserPreferences {
  favorite_cuisines: string[];
  total_orders: number;
  average_order_value: number;
}

export interface Restaurant {
  id: number;
  name: string;
  cuisine_type: string;
  description?: string;
  rating: number;
  price_range?: string;
  location?: string;
  created_at: string;
}

export interface RestaurantWithScore extends Restaurant {
  similarity_score: number;
  insight?: string;
}

export interface Order {
  id: number;
  user_id: number;
  restaurant_id: number;
  restaurant_name?: string;
  order_date: string;
  total_amount?: number;
  items?: Array<Record<string, any>>;
  rating?: number;
  is_simulation?: boolean;
  created_at: string;
}

export interface OrderCreate {
  restaurant_id: number;
  order_date: string;
  total_amount?: number;
  items?: Array<Record<string, any>>;
  rating?: number;
  is_simulation?: boolean;
}

export interface Recommendation {
  restaurant: Restaurant;
  similarity_score: number;
  insight?: string;
  generated_at: string;
}

export interface RecommendationsResponse {
  recommendations: Recommendation[];
  count: number;
  generated_at: string;
}

export interface ChefRecommendation {
  restaurant: Restaurant;
  similarity_score: number;
  explanation: string;
  reasoning: string[];
  confidence: number;
  has_insight?: boolean; // Indica se a explicação foi gerada por LLM (true) ou é fallback (false)
  generated_at: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface ApiError {
  detail: string;
}

export interface OnboardingRequest {
  selected_cuisines: string[];
  price_preference?: 'low' | 'medium' | 'high';
  dietary_restrictions?: string[];
}

export interface OnboardingResponse {
  success: boolean;
  message: string;
  has_synthetic_vector: boolean;
}

