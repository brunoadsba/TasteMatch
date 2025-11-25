import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Trash2, ChevronDown, ChevronUp, Terminal } from 'lucide-react';
import type { AIReasoningLog } from '@/hooks/useAIReasoning';
import { cn } from '@/lib/utils';

interface AIReasoningLogProps {
  logs: AIReasoningLog[];
  onClear: () => void;
  className?: string;
}

export function AIReasoningLogComponent({ logs, onClear, className }: AIReasoningLogProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll para última linha
  useEffect(() => {
    if (isExpanded && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [logs, isExpanded]);

  const getLogColor = (type: AIReasoningLog['type']) => {
    const colors: Record<AIReasoningLog['type'], string> = {
      info: 'text-blue-400',
      success: 'text-green-400',
      warning: 'text-yellow-400',
      error: 'text-red-400',
      processing: 'text-cyan-400',
    };
    return colors[type] || 'text-gray-400';
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <Card className={cn('bg-gray-900 border-gray-700', className)}>
      <CardHeader className="bg-gray-800 border-b border-gray-700 p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-green-400" />
            <CardTitle className="text-sm font-mono text-green-400">
              Terminal de Raciocínio da IA
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="h-7 w-7 p-0 text-gray-400 hover:text-gray-300"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronUp className="w-4 h-4" />
              )}
            </Button>
            {logs.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClear}
                className="h-7 w-7 p-0 text-red-400 hover:text-red-300"
                title="Limpar logs"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent className="p-0">
          <div
            ref={containerRef}
            className="h-[200px] overflow-y-auto bg-black p-4 font-mono text-xs"
            style={{
              scrollbarWidth: 'thin',
              scrollbarColor: '#4B5563 #1F2937',
            }}
          >
            {logs.length === 0 ? (
              <div className="text-gray-500 italic">
                {'>'} Aguardando processamento...
              </div>
            ) : (
              logs.map((log) => (
                <div
                  key={log.id}
                  className={cn('mb-1 flex items-start gap-2', getLogColor(log.type))}
                >
                  <span className="text-gray-500 shrink-0">
                    [{formatTime(log.timestamp)}]
                  </span>
                  <span className="flex-1 break-words">{log.message}</span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        </CardContent>
      )}
    </Card>
  );
}

