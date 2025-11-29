import { useState, useRef, useEffect } from 'react';
import { useChefChat } from '@/hooks/useChefChat';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { api } from '@/lib/api';
import { 
  Send, 
  Mic, 
  MicOff, 
  Loader2, 
  Volume2, 
  VolumeX,
  X,
  MessageSquare,
  Headphones,
  Brain,
  MessageCircle,
  User
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChefChatProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ChefChat({ open, onOpenChange }: ChefChatProps) {
  const {
    messages,
    loading,
    error,
    sending,
    processingAudio,
    sendMessage,
    sendAudio,
    loadHistory,
    clearError,
  } = useChefChat();

  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [audioStatus, setAudioStatus] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [playingAudioId, setPlayingAudioId] = useState<number | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Carregar histórico ao abrir
  useEffect(() => {
    if (open) {
      loadHistory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // Scroll para última mensagem
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Atualizar status de áudio baseado no estado
  useEffect(() => {
    if (processingAudio) {
      setAudioStatus('listening');
    } else if (sending && !processingAudio) {
      setAudioStatus('thinking');
    } else {
      setAudioStatus('idle');
    }
  }, [processingAudio, sending]);

  const handleSendText = async () => {
    if (!inputText.trim() || sending) return;
    
    const text = inputText.trim();
    setInputText('');
    await sendMessage(text);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Configurar MediaRecorder para WebM/Opus (otimizado)
      const options: MediaRecorderOptions = {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 128000, // 128 kbps - qualidade suficiente
      };

      // Fallback para navegadores que não suportam WebM/Opus
      let mediaRecorder: MediaRecorder;
      try {
        mediaRecorder = new MediaRecorder(stream, options);
      } catch (e) {
        // Fallback para formato padrão
        mediaRecorder = new MediaRecorder(stream);
      }

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Parar stream
        stream.getTracks().forEach(track => track.stop());
        
        // Enviar áudio
        await sendAudio(audioBlob);
        setIsRecording(false);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setAudioStatus('listening');
    } catch (err) {
      console.error('Erro ao iniciar gravação:', err);
      alert('Erro ao acessar microfone. Verifique as permissões.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handlePlayAudio = (audioUrl: string, messageId: number) => {
    if (playingAudioId === messageId) {
      // Pausar se já está tocando
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      setPlayingAudioId(null);
      setAudioStatus('idle');
      return;
    }

    // Parar áudio anterior se houver
    if (audioRef.current) {
      audioRef.current.pause();
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;
    
    audio.onplay = () => {
      setPlayingAudioId(messageId);
      setAudioStatus('speaking');
    };

    audio.onended = () => {
      setPlayingAudioId(null);
      setAudioStatus('idle');
      audioRef.current = null;
    };

    audio.onerror = () => {
      setPlayingAudioId(null);
      setAudioStatus('idle');
      audioRef.current = null;
    };

    audio.play().catch((err) => {
      console.error('Erro ao reproduzir áudio:', err);
      setPlayingAudioId(null);
      setAudioStatus('idle');
    });
  };

  const getAudioStatusText = () => {
    switch (audioStatus) {
      case 'listening':
        return 'O Chef está ouvindo...';
      case 'thinking':
        return 'O Chef está pensando...';
      case 'speaking':
        return 'O Chef está falando...';
      default:
        return '';
    }
  };

  // Função para renderizar markdown básico (converter **texto** para negrito)
  const renderMarkdown = (text: string) => {
    // Regex para encontrar **texto** (negrito) - suporta múltiplas ocorrências
    const boldRegex = /\*\*([^*]+)\*\*/g;
    const parts: Array<{ type: 'text' | 'bold'; content: string }> = [];
    let lastIndex = 0;
    let match;

    // Encontrar todas as ocorrências de **texto**
    while ((match = boldRegex.exec(text)) !== null) {
      // Adicionar texto antes do match
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index),
        });
      }
      
      // Adicionar texto em negrito
      parts.push({
        type: 'bold',
        content: match[1], // Conteúdo sem os asteriscos
      });
      
      lastIndex = match.index + match[0].length;
    }
    
    // Adicionar texto restante após o último match
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex),
      });
    }
    
    // Se não houver matches, retornar texto original
    if (parts.length === 0) {
      return <span>{text}</span>;
    }
    
    // Renderizar partes
    return (
      <>
        {parts.map((part, index) => {
          if (part.type === 'bold') {
            return (
              <strong key={index} className="font-semibold">
                {part.content}
              </strong>
            );
          }
          return <span key={index}>{part.content}</span>;
        })}
      </>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl h-[80vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5" />
            Chef Virtual
          </DialogTitle>
          <DialogDescription>
            Converse com o Chef Virtual sobre restaurantes e comida
          </DialogDescription>
        </DialogHeader>

        {/* Área de mensagens */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {loading && messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <MessageCircle className="w-12 h-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">Nenhuma mensagem ainda</p>
              <p className="text-sm mt-2">
                Comece uma conversa enviando uma mensagem ou gravando um áudio
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  'flex gap-3',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="w-4 h-4 text-primary" />
                  </div>
                )}
                
                <div
                  className={cn(
                    'rounded-lg px-4 py-2 max-w-[80%]',
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  )}
                >
                  <div className="text-sm whitespace-pre-wrap break-words">
                    {renderMarkdown(message.content)}
                  </div>
                  
                  {message.role === 'assistant' && message.audio_url && (
                    <div className="mt-2 flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (!message.audio_url) return;
                          const audioUrl = message.audio_url.startsWith('http')
                            ? message.audio_url
                            : api.getAudioUrl(message.audio_url.split('/').pop() || '');
                          handlePlayAudio(audioUrl, message.id);
                        }}
                        className="h-8 px-2"
                      >
                        {playingAudioId === message.id ? (
                          <>
                            <VolumeX className="w-3 h-3 mr-1" />
                            Pausar
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3 h-3 mr-1" />
                            Ouvir
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-primary-foreground" />
                  </div>
                )}
              </div>
            ))
          )}

          {/* Status de áudio */}
          {(audioStatus !== 'idle' || sending) && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground px-4 py-2 bg-muted/50 rounded-lg">
              {audioStatus === 'listening' && <Headphones className="w-4 h-4 animate-pulse" />}
              {audioStatus === 'thinking' && <Brain className="w-4 h-4 animate-pulse" />}
              {audioStatus === 'speaking' && <Volume2 className="w-4 h-4 animate-pulse" />}
              {sending && audioStatus === 'idle' && <Loader2 className="w-4 h-4 animate-spin" />}
              <span>{getAudioStatusText() || 'Processando...'}</span>
            </div>
          )}

          {error && (
            <div className="bg-destructive/10 text-destructive text-sm px-4 py-2 rounded-lg">
              {error}
              <Button
                variant="ghost"
                size="sm"
                onClick={clearError}
                className="ml-2 h-auto p-0 text-destructive"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Rodapé fixo */}
        <div className="border-t px-6 py-3 bg-muted/30">
          <p className="text-xs text-muted-foreground text-center">
            ⚠️ Alguns restaurantes mencionados podem não estar disponíveis no momento. 
            Por favor, verifique a disponibilidade no site do TasteMatch.
          </p>
        </div>

        {/* Input area */}
        <div className="border-t px-6 py-4 space-y-2">
          <div className="flex gap-2">
            <Input
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendText();
                }
              }}
              placeholder="Digite sua mensagem..."
              disabled={sending || processingAudio}
              className="flex-1"
            />
            
            <Button
              variant={isRecording ? 'destructive' : 'outline'}
              size="icon"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={sending || processingAudio}
              className={cn(
                isRecording && 'animate-pulse'
              )}
            >
              {isRecording ? (
                <MicOff className="w-4 h-4" />
              ) : (
                <Mic className="w-4 h-4" />
              )}
            </Button>

            <Button
              onClick={handleSendText}
              disabled={!inputText.trim() || sending || processingAudio}
              size="icon"
            >
              {sending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

