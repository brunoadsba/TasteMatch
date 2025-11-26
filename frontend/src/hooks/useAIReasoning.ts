/**
 * Hook para gerenciar logs de raciocínio da IA.
 * Agora usa Context API para compartilhar estado globalmente.
 * 
 * Este arquivo mantém compatibilidade com imports existentes,
 * mas delega a implementação para o Context.
 */
export { useAIReasoning, type AIReasoningLog } from '@/contexts/AIReasoningContext';

