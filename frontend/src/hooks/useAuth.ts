import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { User, UserCreate } from '@/types';

interface UseAuthReturn {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: UserCreate) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.getCurrentUser()
        .then((userData) => {
          setUser(userData);
        })
        .catch(() => {
          localStorage.removeItem('token');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const { token, user } = await api.login(email, password);
      localStorage.setItem('token', token);
      setUser(user);
      toast.success('Login realizado com sucesso!', {
        description: `Bem-vindo, ${user.name}!`,
      });
      navigate('/dashboard');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao fazer login';
      toast.error('Falha no login', {
        description: message.includes('Email ou senha') 
          ? 'Email ou senha incorretos. Verifique suas credenciais.'
          : 'Não foi possível fazer login. Tente novamente.',
      });
      throw error;
    }
  };

  const register = async (data: UserCreate) => {
    try {
      const { token, user } = await api.register(data);
      localStorage.setItem('token', token);
      setUser(user);
      toast.success('Conta criada com sucesso!', {
        description: `Bem-vindo ao TasteMatch, ${user.name}!`,
      });
      // Redirecionar para onboarding após cadastro
      navigate('/onboarding');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Erro ao criar conta';
      toast.error('Falha ao criar conta', {
        description: message.includes('já cadastrado') || message.includes('Email')
          ? 'Este email já está cadastrado. Tente fazer login.'
          : 'Não foi possível criar sua conta. Verifique os dados e tente novamente.',
      });
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    toast.info('Logout realizado', {
      description: 'Você foi desconectado com sucesso.',
    });
    navigate('/login');
  };

  return {
    user,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user,
  };
}

