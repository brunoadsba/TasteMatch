"""
Script de teste para o pipeline de áudio do Chef Virtual
Testa STT (Speech-to-Text) e TTS (Text-to-Speech)
"""

import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.audio_service import get_audio_service
from app.config import settings


def test_text_to_speech():
    """Testa Text-to-Speech (TTS)"""
    print("🎤 Testando Text-to-Speech (TTS)...")
    
    audio_service = get_audio_service()
    test_text = "Olá! Eu sou o Chef Virtual do TasteMatch. Como posso ajudá-lo hoje?"
    
    try:
        audio_path = audio_service.text_to_speech(test_text)
        print(f"✅ Áudio gerado com sucesso: {audio_path}")
        
        # Verificar se o arquivo existe
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"   Tamanho do arquivo: {file_size / 1024:.2f} KB")
            return True
        else:
            print("❌ Arquivo de áudio não foi criado")
            return False
    except Exception as e:
        print(f"❌ Erro ao gerar áudio: {str(e)}")
        return False


def test_speech_to_text():
    """Testa Speech-to-Text (STT) - requer arquivo de áudio"""
    print("\n🎧 Testando Speech-to-Text (STT)...")
    print("   Nota: Este teste requer um arquivo de áudio.")
    print("   Para testar completamente, use o endpoint /api/chat com um arquivo de áudio.")
    
    # Verificar se há arquivos de áudio de teste
    audio_service = get_audio_service()
    temp_dir = audio_service.temp_dir
    
    # Procurar arquivos de áudio no diretório temporário
    audio_files = list(temp_dir.glob("*.mp3")) + list(temp_dir.glob("*.webm"))
    
    if not audio_files:
        print("   ⚠️  Nenhum arquivo de áudio encontrado para teste")
        print("   Para testar STT, envie um arquivo de áudio via endpoint /api/chat")
        return None
    
    # Testar com o primeiro arquivo encontrado
    test_file = audio_files[0]
    print(f"   Testando com arquivo: {test_file.name}")
    
    try:
        transcription = audio_service.speech_to_text(str(test_file))
        print(f"✅ Transcrição bem-sucedida:")
        print(f"   Texto: {transcription[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Erro ao transcrever áudio: {str(e)}")
        return False


def test_cleanup():
    """Testa limpeza de arquivos temporários"""
    print("\n🧹 Testando limpeza de arquivos temporários...")
    
    audio_service = get_audio_service()
    
    try:
        deleted_count = audio_service.cleanup_temp_files(max_age_hours=0)  # Deletar todos
        print(f"✅ Limpeza concluída: {deleted_count} arquivos deletados")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar arquivos: {str(e)}")
        return False


def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("TESTE DO PIPELINE DE ÁUDIO - CHEF VIRTUAL")
    print("=" * 60)
    print(f"Groq API Key: {'✅ Configurada' if settings.GROQ_API_KEY else '❌ Não configurada'}")
    print()
    
    results = []
    
    # Teste 1: TTS
    results.append(("TTS", test_text_to_speech()))
    
    # Teste 2: STT (opcional, requer arquivo)
    stt_result = test_speech_to_text()
    if stt_result is not None:
        results.append(("STT", stt_result))
    
    # Teste 3: Cleanup
    results.append(("Cleanup", test_cleanup()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results if result is not None)
    
    if all_passed:
        print("\n✅ Todos os testes passaram!")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os logs acima.")


if __name__ == "__main__":
    main()

