import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { validateLoginForm, validateRegisterForm, type ValidationError } from '@/lib/validation';

export function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const { login, register } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});
    
    // Validação no frontend
    const validationErrors = isLogin
      ? validateLoginForm(email, password)
      : validateRegisterForm(email, password, name);
    
    if (validationErrors.length > 0) {
      const errorsMap: Record<string, string> = {};
      validationErrors.forEach((err) => {
        errorsMap[err.field] = err.message;
      });
      setFieldErrors(errorsMap);
      return;
    }
    
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register({ email, password, name });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    if (fieldErrors.email) {
      setFieldErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.email;
        return newErrors;
      });
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    if (fieldErrors.password) {
      setFieldErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.password;
        return newErrors;
      });
    }
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
    if (fieldErrors.name) {
      setFieldErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.name;
        return newErrors;
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background text-foreground p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">TasteMatch</CardTitle>
          <CardDescription>
            {isLogin ? 'Faça login na sua conta' : 'Crie uma nova conta'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-1">
                  Nome
                </label>
                <Input
                  id="name"
                  type="text"
                  value={name}
                  onChange={handleNameChange}
                  placeholder="Seu nome completo"
                  required={!isLogin}
                  error={!!fieldErrors.name}
                  errorMessage={fieldErrors.name}
                  aria-label="Nome completo"
                  aria-required="true"
                />
              </div>
            )}
            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-1">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={handleEmailChange}
                placeholder="seu@email.com"
                required
                error={!!fieldErrors.email}
                errorMessage={fieldErrors.email}
                aria-label="Email"
                aria-required="true"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium mb-1">
                Senha
              </label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={handlePasswordChange}
                placeholder="••••••••"
                required
                error={!!fieldErrors.password}
                errorMessage={fieldErrors.password}
                aria-label="Senha"
                aria-required="true"
              />
            </div>
            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-3 rounded flex items-start gap-2">
                <span className="text-red-600">⚠️</span>
                <span>{error}</span>
              </div>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Processando...' : isLogin ? 'Entrar' : 'Criar conta'}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setFieldErrors({});
              }}
              className="text-sm text-blue-600 hover:underline"
              aria-label={isLogin ? 'Ir para criação de conta' : 'Ir para login'}
            >
              {isLogin
                ? 'Não tem conta? Criar conta'
                : 'Já tem conta? Fazer login'}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

