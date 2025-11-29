"""
Serviço de áudio para Chef Virtual
STT (Speech-to-Text) usando Groq Whisper
TTS (Text-to-Speech) usando Edge-TTS
"""

import os
import tempfile
from typing import Optional
from pathlib import Path
import groq
from edge_tts import Communicate
import asyncio

from app.config import settings


class AudioService:
    """Serviço para processamento de áudio"""
    
    def __init__(self):
        """Inicializa o serviço de áudio"""
        self.groq_client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.temp_dir = Path(tempfile.gettempdir()) / "tastematch_audio"
        self.temp_dir.mkdir(exist_ok=True)
    
    def speech_to_text(
        self, 
        audio_file_path: str,
        language: Optional[str] = "pt"
    ) -> str:
        """
        Converte áudio em texto usando Groq Whisper API
        
        Otimização: Groq Whisper aceita WebM/Opus diretamente (sem conversão pesada)
        
        Args:
            audio_file_path: Caminho para o arquivo de áudio
            language: Idioma do áudio (padrão: português)
        
        Returns:
            Texto transcrito
        
        Raises:
            Exception: Se houver erro ao transcrever
        """
        # Validar que o arquivo existe
        if not os.path.exists(audio_file_path):
            raise Exception(f"Arquivo de áudio não encontrado: {audio_file_path}")
        
        # Validar tamanho do arquivo (máximo 25MB para Groq Whisper)
        file_size = os.path.getsize(audio_file_path)
        max_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_size:
            raise Exception(f"Arquivo de áudio muito grande: {file_size / 1024 / 1024:.2f}MB (máximo: 25MB)")
        
        try:
            with open(audio_file_path, "rb") as audio_file:
                # Groq Whisper aceita WebM/Opus diretamente (sem conversão)
                # Isso reduz latência significativamente
                transcription = self.groq_client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3",
                    language=language,
                    response_format="text"
                )
                return transcription.strip()
        except Exception as e:
            # Groq pode lançar diferentes tipos de exceções
            error_msg = str(e)
            if "groq" in error_msg.lower() or "api" in error_msg.lower():
                raise Exception(f"Erro na API Groq ao transcrever áudio: {error_msg}")
            raise Exception(f"Erro ao transcrever áudio: {error_msg}")
    
    async def text_to_speech_async(
        self,
        text: str,
        voice: str = "pt-BR-FranciscaNeural",
        output_path: Optional[str] = None
    ) -> str:
        """
        Converte texto em áudio usando Edge-TTS (assíncrono)
        
        Nota: Edge-TTS é uma API não oficial da Microsoft.
        Monitorar mudanças na API e considerar fallback alternativo.
        
        Args:
            text: Texto para converter (máximo 5000 caracteres)
            voice: Voz a usar (padrão: Francisca - português brasileiro)
            output_path: Caminho de saída (opcional, gera automaticamente se None)
        
        Returns:
            Caminho do arquivo de áudio gerado
        
        Raises:
            Exception: Se houver erro ao gerar áudio
        """
        # Validar tamanho do texto (Edge-TTS tem limite)
        if len(text) > 5000:
            raise Exception(f"Texto muito longo para TTS: {len(text)} caracteres (máximo: 5000)")
        
        if output_path is None:
            # Usar hash do texto para nome do arquivo (evita duplicatas)
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            output_path = str(self.temp_dir / f"tts_{text_hash}.mp3")
        
        try:
            communicate = Communicate(text, voice)
            await communicate.save(output_path)
            
            # Validar que o arquivo foi criado
            if not os.path.exists(output_path):
                raise Exception("Arquivo de áudio não foi criado")
            
            return output_path
        except Exception as e:
            raise Exception(f"Erro ao gerar áudio com Edge-TTS: {str(e)}")
    
    def text_to_speech(
        self,
        text: str,
        voice: str = "pt-BR-FranciscaNeural",
        output_path: Optional[str] = None
    ) -> str:
        """
        Converte texto em áudio usando Edge-TTS (síncrono)
        
        Args:
            text: Texto para converter
            voice: Voz a usar
            output_path: Caminho de saída (opcional)
        
        Returns:
            Caminho do arquivo de áudio gerado
        """
        return asyncio.run(
            self.text_to_speech_async(text, voice, output_path)
        )
    
    def cleanup_temp_files(self, max_age_hours: int = 24):
        """
        Limpa arquivos temporários antigos
        
        Args:
            max_age_hours: Idade máxima dos arquivos em horas (padrão: 24h)
        
        Returns:
            Número de arquivos deletados
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0
        
        for file_path in self.temp_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception:
                        pass  # Ignorar erros ao deletar
        
        return deleted_count


def get_audio_service() -> AudioService:
    """
    Factory function para criar instância do AudioService
    
    Returns:
        Instância do AudioService
    """
    return AudioService()

