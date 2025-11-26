import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type {
  User,
  UserCreate,
  UserPreferences,
  Restaurant,
  Order,
  OrderCreate,
  Recommendation,
  ChefRecommendation,
  AuthResponse,
  ApiError,
  OnboardingRequest,
  OnboardingResponse,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? 'https://tastematch-api.fly.dev' : 'http://localhost:8000');

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor para adicionar token JWT
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Interceptor para tratamento de erros
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Token inválido ou expirado
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Autenticação
  async register(data: UserCreate): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/register', data);
    return response.data;
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  // Usuário
  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/api/users/me');
    return response.data;
  }

  async getUserPreferences(): Promise<UserPreferences> {
    const response = await this.client.get<UserPreferences>('/api/users/me/preferences');
    return response.data;
  }

  // Restaurantes
  async getRestaurants(params?: {
    cuisine_type?: string;
    min_rating?: number;
    price_range?: string;
    search?: string;
    sort_by?: string;
    page?: number;
    limit?: number;
  }): Promise<{ restaurants: Restaurant[]; total: number; page: number; limit: number }> {
    const response = await this.client.get('/api/restaurants', { params });
    return response.data;
  }

  async getRestaurant(id: number): Promise<Restaurant> {
    const response = await this.client.get<Restaurant>(`/api/restaurants/${id}`);
    return response.data;
  }

  // Pedidos
  async getOrders(params?: {
    limit?: number;
    offset?: number;
  }): Promise<{ orders: Order[]; total: number; count: number }> {
    const response = await this.client.get<{ orders: Order[]; total: number; count: number }>('/api/orders', {
      params,
    });
    return response.data;
  }

  async createOrder(data: OrderCreate): Promise<Order> {
    const response = await this.client.post<Order>('/api/orders', data);
    return response.data;
  }

  // Recomendações
  async getRecommendations(params?: {
    limit?: number;
    refresh?: boolean;
  }): Promise<Recommendation[]> {
    const response = await this.client.get<{ recommendations: Recommendation[]; count: number; generated_at: string }>('/api/recommendations', {
      params,
    });
    return response.data.recommendations;
  }

  async getRestaurantInsight(restaurantId: number): Promise<{ insight: string }> {
    const response = await this.client.get<{ insight: string }>(
      `/api/recommendations/${restaurantId}/insight`
    );
    return response.data;
  }

  async getChefRecommendation(params?: {
    refresh?: boolean;
  }): Promise<ChefRecommendation> {
    const response = await this.client.get<ChefRecommendation>('/api/recommendations/chef-choice', {
      params,
    });
    return response.data;
  }

  // Simulação
  async resetSimulation(): Promise<{ deleted: number; message: string }> {
    const response = await this.client.delete<{ deleted: number; message: string }>('/api/orders/simulation');
    return response.data;
  }

  async completeOnboarding(data: OnboardingRequest): Promise<OnboardingResponse> {
    const response = await this.client.post<OnboardingResponse>('/api/onboarding/complete', data);
    return response.data;
  }
}

export const api = new ApiClient();
export default api;

