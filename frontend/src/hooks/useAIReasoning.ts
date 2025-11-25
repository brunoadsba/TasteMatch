import { useState, useCallback, useRef } from 'react';

export interface AIReasoningLog {
  id: string;
  timestamp: Date;
  type: 'info' | 'success' | 'warning' | 'error' | 'processing';
  message: string;
}

interface UseAIReasoningReturn {
  logs: AIReasoningLog[];
  addLog: (message: string, type?: AIReasoningLog['type']) => void;
  clearLogs: () => void;
  simulateReasoning: (scenario: string, step: number, total: number) => Promise<void>;
}

/**
 * Hook para gerenciar logs de raciocínio da IA.
 * Simula o processo de análise e inferência do sistema de recomendação.
 */
export function useAIReasoning(): UseAIReasoningReturn {
  const [logs, setLogs] = useState<AIReasoningLog[]>([]);
  const logIdCounter = useRef(0);

  const addLog = useCallback((message: string, type: AIReasoningLog['type'] = 'info') => {
    const log: AIReasoningLog = {
      id: `log-${logIdCounter.current++}`,
      timestamp: new Date(),
      type,
      message,
    };
    
    setLogs(prev => [...prev, log]);
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
    logIdCounter.current = 0;
  }, []);

  /**
   * Simula o processo de raciocínio baseado no cenário e progresso.
   */
  const simulateReasoning = useCallback(async (
    scenario: string,
    step: number,
    total: number
  ): Promise<void> => {
    // Logs baseados no cenário
    const scenarioLogs: Record<string, string[]> = {
      'fit': [
        'Detectando padrão: preferências por comida saudável',
        'Analisando termos semânticos: "Salada", "Detox", "Proteico"',
        'Identificando cluster: SAÚDE_BEM_ESTAR',
        'Reduzindo score de Fast Food (-45%)',
        'Aumentando score de Natural/Saudável (+60%)',
      ],
      'comfort': [
        'Detectando padrão: preferências por comfort food',
        'Analisando termos semânticos: "Pizza", "Hamburguer", "Doces"',
        'Identificando cluster: FAST_FOOD_INDULGENCE',
        'Reduzindo score de Saudável (-30%)',
        'Aumentando score de Fast Food (+50%)',
      ],
      'premium': [
        'Detectando padrão: preferências por alta gastronomia',
        'Analisando termos semânticos: "Premium", "Gourmet", "Experiência"',
        'Identificando cluster: FINE_DINING',
        'Reduzindo score de Fast Food (-60%)',
        'Aumentando score de Alta Gastronomia (+70%)',
      ],
    };

    const defaultLogs = [
      'Processando dados do pedido...',
      'Extraindo características semânticas',
      'Atualizando perfil do usuário',
      'Recalculando scores de similaridade',
    ];

    const messages = scenarioLogs[scenario] || defaultLogs;
    const messagesToShow = messages.slice(0, step);

    // Limpar logs anteriores se for o primeiro passo
    if (step === 1) {
      clearLogs();
      addLog('[INGESTÃO DE DADOS] Processando lote de novos pedidos...', 'info');
      await new Promise(resolve => setTimeout(resolve, 300));
    }

    // Adicionar logs progressivamente
    for (let i = 0; i < messagesToShow.length; i++) {
      const message = messagesToShow[i];
      
      // Determinar tipo de log baseado no conteúdo
      let type: AIReasoningLog['type'] = 'info';
      if (message.includes('score') || message.includes('Cluster')) {
        type = 'processing';
      } else if (message.includes('Reduzindo') || message.includes('Aumentando')) {
        type = 'success';
      }

      addLog(`[INFERÊNCIA] ${message}`, type);
      await new Promise(resolve => setTimeout(resolve, 400)); // Delay entre logs
    }

    // Log final quando completar
    if (step === total) {
      await new Promise(resolve => setTimeout(resolve, 300));
      addLog(`[SUCESSO] Perfil atualizado com confiança de ${85 + step * 3}%`, 'success');
      addLog('Recomendações sendo recalculadas...', 'info');
    }
  }, [addLog, clearLogs]);

  return {
    logs,
    addLog,
    clearLogs,
    simulateReasoning,
  };
}

