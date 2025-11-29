import { useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { api } from '@/lib/api';
import type { ChatMessage, ChatResponse } from '@/types';

export interface UseChefChatReturn {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  sending: boolean;
  processingAudio: boolean;
  sendMessage: (text: string) => Promise<void>;
  sendAudio: (audioBlob: Blob) => Promise<void>;
  loadHistory: () => Promise<void>;
  clearError: () => void;
}

export function useChefChat(): UseChefChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [processingAudio, setProcessingAudio] = useState(false);
  const historyLoadedRef = useRef(false);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || sending) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      created_at: new Date().toISOString(),
    };

    // Estado otimista: adicionar mensagem do usuário imediatamente
    setMessages((prev) => [...prev, userMessage]);
    setSending(true);
    setError(null);

    try {
      const response: ChatResponse = await api.sendChatMessage(text.trim());
      
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        audio_url: response.audio_url || null,
        created_at: new Date().toISOString(),
      };

      // Substituir mensagem otimista pela resposta real
      setMessages((prev) => {
        const withoutOptimistic = prev.filter((m) => m.id !== userMessage.id);
        return [...withoutOptimistic, userMessage, assistantMessage];
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao enviar mensagem';
      setError(errorMessage);
      
      // Remover mensagem otimista em caso de erro
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      
      toast.error('Erro ao enviar mensagem', {
        description: errorMessage,
      });
    } finally {
      setSending(false);
    }
  }, [sending]);

  const sendAudio = useCallback(async (audioBlob: Blob) => {
    if (sending || processingAudio) return;

    setProcessingAudio(true);
    setSending(true);
    setError(null);

    try {
      const response: ChatResponse = await api.sendChatAudio(audioBlob);
      
      // Adicionar mensagens (usuário e assistente) após processamento
      const userMessage: ChatMessage = {
        id: Date.now(),
        role: 'user',
        content: '[Áudio enviado]', // Placeholder, poderia transcrever se necessário
        created_at: new Date().toISOString(),
      };

      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        audio_url: response.audio_url || null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao processar áudio';
      setError(errorMessage);
      
      toast.error('Erro ao processar áudio', {
        description: errorMessage,
      });
    } finally {
      setSending(false);
      setProcessingAudio(false);
    }
  }, [sending, processingAudio]);

  const loadHistory = useCallback(async () => {
    if (historyLoadedRef.current) return;

    setLoading(true);
    setError(null);
    historyLoadedRef.current = true; // Marcar como carregado antes para evitar chamadas duplicadas

    try {
      const data = await api.getChatHistory({ limit: 50 });
      setMessages(data.messages);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao carregar histórico';
      setError(errorMessage);
      historyLoadedRef.current = false; // Resetar em caso de erro para permitir retry
      
      // Não mostrar toast no carregamento inicial
      console.error('Erro ao carregar histórico:', errorMessage);
    } finally {
      setLoading(false);
    }
  }, []); // Sem dependências para evitar loops

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    loading,
    error,
    sending,
    processingAudio,
    sendMessage,
    sendAudio,
    loadHistory,
    clearError,
  };
}

