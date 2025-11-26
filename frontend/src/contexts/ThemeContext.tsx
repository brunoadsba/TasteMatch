import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const THEME_STORAGE_KEY = 'tastematch-theme';

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyThemeClass(theme: Theme) {
  if (typeof document === 'undefined') return;
  const root = document.documentElement;
  const effective = theme === 'system' ? getSystemTheme() : theme;
  if (effective === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>('system');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(() =>
    typeof window === 'undefined' ? 'light' : getSystemTheme()
  );

  // Inicializar a partir do localStorage + sistema
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const stored = window.localStorage.getItem(THEME_STORAGE_KEY) as Theme | null;
    const initialTheme = stored ?? 'system';
    setThemeState(initialTheme);
    const effective = initialTheme === 'system' ? getSystemTheme() : initialTheme;
    setResolvedTheme(effective);
    applyThemeClass(initialTheme);
  }, []);

  // Reagir a mudanças do sistema quando em modo 'system'
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (theme === 'system') {
        const sys = getSystemTheme();
        setResolvedTheme(sys);
        applyThemeClass('system');
      }
    };
    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, [theme]);

  const setTheme = (next: Theme) => {
    setThemeState(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    }
    const effective = next === 'system' ? getSystemTheme() : next;
    setResolvedTheme(effective);
    applyThemeClass(next);
  };

  const value: ThemeContextValue = {
    theme,
    resolvedTheme,
    setTheme,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return ctx;
}


