import { Button } from '@/components/ui/button';
import { useTheme } from '@/contexts/ThemeContext';
import { Moon, Sun, Monitor } from 'lucide-react';

export function ThemeToggle() {
  const { theme, resolvedTheme, setTheme } = useTheme();

  const isDark = resolvedTheme === 'dark';

  const handleClick = () => {
    // Alterna entre claro e escuro; o modo 'system' pode ser selecionado via menu futuro
    setTheme(isDark ? 'light' : 'dark');
  };

  const icon =
    theme === 'system' ? <Monitor className="w-4 h-4" /> : isDark ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />;

  const label =
    theme === 'system'
      ? 'Sistema'
      : isDark
      ? 'Escuro'
      : 'Claro';

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={handleClick}
      className="flex items-center gap-2"
      title={`Tema atual: ${label} (clique para alternar entre Claro/Escuro)`}
    >
      {icon}
      <span className="hidden sm:inline text-xs">{label}</span>
    </Button>
  );
}


