"""
Endpoint de chat para Chef Virtual
"""

import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
import logging

from app.database.base import get_db
from app.api.deps import get_current_user
from app.database.models import User
from app.core.rag_service import get_rag_service
from app.core.chef_chat import get_chef_response, validate_question, detect_social_interaction
from app.core.audio_service import get_audio_service
from app.core.knowledge_base import update_knowledge_base
from app.core.rate_limiter import user_limiter
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/")
@user_limiter.limit("30/minute")  # Limite de 30 requisições por minuto (limite Groq API)
async def chat(
    request: Request,  # Necessário para rate limiting (deve vir primeiro)
    message: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint principal de chat do Chef Virtual
    
    Aceita mensagem de texto ou arquivo de áudio
    
    Rate Limit: 30 requisições por minuto por usuário (respeitando limite Groq API)
    """
    try:
        logger.info(f"Iniciando endpoint /api/chat/ para usuário {current_user.id}")
        request.state.current_user = current_user
    except Exception as e:
        logger.error(f"Erro ao inicializar endpoint /api/chat/: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Erro ao inicializar endpoint de chat"
        )
    
    
    # Validar que pelo menos um input foi fornecido
    if not message and not audio:
        raise HTTPException(
            status_code=400,
            detail="Forneça uma mensagem de texto ou arquivo de áudio"
        )
    
    # Processar áudio se fornecido
    user_question = message
    audio_url = None
    
    if audio:
        # Validar tipo de arquivo
        allowed_content_types = [
            "audio/webm",
            "audio/ogg",
            "audio/opus",
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/x-wav"
        ]
        
        if audio.content_type and audio.content_type not in allowed_content_types:
            # Verificar extensão do arquivo como fallback
            file_extension = Path(audio.filename or "").suffix.lower()
            allowed_extensions = [".webm", ".ogg", ".opus", ".mp3", ".wav", ".mpeg"]
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Formato de áudio não suportado: {audio.content_type}. Formatos aceitos: WebM, OGG, Opus, MP3, WAV"
                )
        
        # Validar tamanho do arquivo (máximo 25MB)
        content = await audio.read()
        if len(content) > 25 * 1024 * 1024:  # 25MB
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo de áudio muito grande: {len(content) / 1024 / 1024:.2f}MB (máximo: 25MB)"
            )
        
        audio_service = get_audio_service()
        
        # Salvar arquivo temporário
        import tempfile
        # Manter extensão original se possível
        file_extension = Path(audio.filename or "audio.webm").suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Converter áudio em texto usando Groq Whisper
            # Groq Whisper aceita WebM/Opus diretamente (sem conversão pesada)
            user_question = audio_service.speech_to_text(tmp_file_path)
            
            if not user_question or not user_question.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Não foi possível transcrever o áudio. Por favor, tente novamente ou envie uma mensagem de texto."
                )
        except HTTPException:
            raise
        except Exception as e:
            # Log detalhado do erro para debug
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(
                f"Erro ao processar áudio STT: {type(e).__name__}: {str(e)}\n{error_traceback}",
                exc_info=True
            )
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar áudio: {str(e)}"
            )
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(tmp_file_path)
            except Exception:
                pass  # Ignorar erros ao deletar
    
    if not user_question:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível processar a mensagem ou áudio"
        )
    
    # Detectar interações sociais (agradecimentos, saudações, despedidas)
    social_response = detect_social_interaction(user_question)
    if social_response:
        # Salvar no histórico
        from app.database import crud
        crud.create_chat_message(
            db=db,
            user_id=current_user.id,
            role="user",
            content=user_question
        )
        crud.create_chat_message(
            db=db,
            user_id=current_user.id,
            role="assistant",
            content=social_response
        )
        db.commit()
        
        return {
            "answer": social_response,
            "audio_url": None,
            "sources": [],
            "validation": {"confidence_score": 1.0, "is_social_interaction": True}
        }
    
    # Validar pergunta
    is_valid, error_message = validate_question(user_question)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)
    
    # Validar GROQ_API_KEY
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY não configurada. Configure no arquivo .env ou variáveis de ambiente."
        )
    
    # Obter RAG service
    # Usar eager=True para reutilizar instância global criada no startup (mais rápido)
    try:
        connection_string = settings.DATABASE_URL
        logger.debug(f"Obtendo RAG service (eager mode - reutiliza instância global se disponível)")
        rag_service = get_rag_service(db, connection_string, eager=True)
        logger.debug("RAG service obtido com sucesso")
    except ValueError as e:
        # Erros de validação (requisitos não atendidos) - mensagens mais claras
        error_msg = str(e)
        logger.error(f"Erro de validação ao inicializar RAG service: {error_msg}")
        
        # Retornar mensagem mais amigável ao usuário
        raise HTTPException(
            status_code=500,
            detail=f"Erro de configuração do banco de dados: {error_msg}. "
                   f"Verifique se a extensão pgvector está instalada e se o banco está configurado corretamente."
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(f"Erro ao inicializar RAG service: {str(e)}\n{error_traceback}", exc_info=True)
        
        # Determinar tipo de erro para mensagem mais específica
        error_msg = str(e)
        if "vector" in error_msg.lower() or "extension" in error_msg.lower():
            detail = (
                "Extensão pgvector não está instalada no banco de dados. "
                "Execute: CREATE EXTENSION IF NOT EXISTS vector;"
            )
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            detail = (
                "Erro de conexão ao banco de dados. "
                "Verifique se DATABASE_URL está correto e se o banco está acessível."
            )
        else:
            detail = f"Erro ao inicializar serviço RAG: {error_msg}"
        
        raise HTTPException(status_code=500, detail=detail)
    
    # Popular base de conhecimento se estiver vazia
    try:
        if not rag_service.has_documents():
            # Verificar se há restaurantes no banco antes de popular
            from app.database import crud
            restaurant_count = len(crud.get_restaurants(db, skip=0, limit=1))
            if restaurant_count > 0:
                # Popular base com restaurantes e conhecimento estático
                update_knowledge_base(db, rag_service, user_id=current_user.id)
            else:
                # Apenas conhecimento estático se não houver restaurantes
                update_knowledge_base(db, rag_service, user_id=current_user.id)
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.warning(f"Erro ao popular base de conhecimento: {str(e)}\n{error_traceback}")
        # Não falhar se não conseguir popular, apenas continuar
    
    # Obter resposta do Chef
    try:
        response = get_chef_response(
            question=user_question,
            rag_service=rag_service,
            user_id=current_user.id,
            db=db,
            audio_url=audio_url  # Passar audio_url se houver
        )
    except HTTPException:
        # Re-raise HTTP exceptions (já formatadas corretamente)
        raise
    except Exception as e:
        # CORREÇÃO: Em vez de retornar erro 500, retornar resposta fallback útil
        # Log completo do erro para debug
        import traceback
        error_traceback = traceback.format_exc()
        
        # Log detalhado do erro com contexto
        logger.error("=" * 60)
        logger.error("❌ ERRO AO GERAR RESPOSTA DO CHEF")
        logger.error("=" * 60)
        logger.error(f"Pergunta do usuário: {user_question}")
        logger.error(f"Tipo de erro: {type(e).__name__}")
        logger.error(f"Mensagem de erro: {str(e)}")
        logger.error(f"Traceback completo:\n{error_traceback}")
        logger.error("=" * 60)
        
        # MELHORIA: Resposta fallback mais inteligente baseada na pergunta
        # Tentar extrair intenção da pergunta para dar resposta mais útil
        question_lower = user_question.lower()
        
        # Detectar tipo de pergunta
        if any(word in question_lower for word in ['churrasco', 'picanha', 'rodízio', 'rodizio']):
            fallback_answer = (
                "Entendi que você está procurando churrasco! 🥩\n\n"
                "Infelizmente não encontrei restaurantes específicos no momento, mas posso te ajudar:\n\n"
                "• Churrascarias geralmente oferecem rodízio com variedade de carnes\n"
                "• Procure por restaurantes brasileiros especializados em carnes grelhadas\n"
                "• Algumas opções comuns incluem picanha, costela, linguiça e frango\n\n"
                "Quer que eu busque outras opções ou você tem alguma preferência específica?"
            )
        elif any(word in question_lower for word in ['pizza', 'massa', 'italiana']):
            fallback_answer = (
                "Entendi que você está procurando pizza! 🍕\n\n"
                "Infelizmente não encontrei restaurantes específicos no momento, mas posso te ajudar:\n\n"
                "• Pizzarias oferecem variedade de sabores e tamanhos\n"
                "• Você pode pedir pizza tradicional, artesanal ou até mesmo doce\n\n"
                "Quer que eu busque outras opções ou você tem alguma preferência específica?"
            )
        elif any(word in question_lower for word in ['sushi', 'japonesa', 'sashimi']):
            fallback_answer = (
                "Entendi que você está procurando comida japonesa! 🍣\n\n"
                "Infelizmente não encontrei restaurantes específicos no momento, mas posso te ajudar:\n\n"
                "• Restaurantes japoneses oferecem sushi, sashimi, temaki e muito mais\n"
                "• Você pode escolher entre opções tradicionais ou contemporâneas\n\n"
                "Quer que eu busque outras opções ou você tem alguma preferência específica?"
            )
        else:
            # Resposta genérica mas mais útil
            fallback_answer = (
                "Entendi sua pergunta! Infelizmente não encontrei informações específicas no momento.\n\n"
                "Posso te ajudar com:\n"
                "• Recomendações de restaurantes por tipo de culinária\n"
                "• Sugestões de pratos e cardápios\n"
                "• Informações sobre preços e localizações\n\n"
                "Que tal reformular sua pergunta? Por exemplo:\n"
                "• 'Quero churrasco'\n"
                "• 'Recomende uma pizzaria'\n"
                "• 'Onde tem comida japonesa?'"
            )
        
        # Salvar mensagens no histórico
        from app.database import crud
        crud.create_chat_message(
            db=db,
            user_id=current_user.id,
            role="user",
            content=user_question
        )
        crud.create_chat_message(
            db=db,
            user_id=current_user.id,
            role="assistant",
            content=fallback_answer
        )
        db.commit()
        
        return {
            "answer": fallback_answer,
            "audio_url": None,
            "sources": [],
            "validation": {
                "confidence_score": 0.0,
                "error": True,
                "error_message": str(e)
            }
        }
    
    # Gerar áudio da resposta (opcional) - após salvar no histórico
    # Se o usuário enviou áudio, gerar áudio da resposta automaticamente
    if audio is not None:
        audio_service = get_audio_service()
        try:
            logger.info(f"Gerando áudio para resposta do usuário {current_user.id}")
            
            # Gerar áudio da resposta usando Edge-TTS (versão assíncrona)
            # Usar versão async diretamente pois estamos em endpoint async
            audio_path = await audio_service.text_to_speech_async(response["answer"])
            
            logger.info(f"Áudio gerado com sucesso: {audio_path}")
            
            # Em produção, fazer upload para storage (S3, Cloudflare R2, etc.) e retornar URL pública
            # Por enquanto, retornar caminho relativo que será servido pelo endpoint /api/chat/audio/{filename}
            audio_filename = Path(audio_path).name
            audio_url = f"/api/chat/audio/{audio_filename}"
            
            logger.info(f"Audio URL gerada: {audio_url}")
            
            # Atualizar última mensagem do assistente com audio_url
            from app.database import crud
            recent_messages = crud.get_user_chat_messages_recent(db, current_user.id, limit=1)
            if recent_messages and recent_messages[0].role == "assistant":
                recent_messages[0].audio_url = audio_url
                db.commit()
                logger.info(f"Audio URL salva no banco de dados para mensagem do assistente")
            else:
                logger.warning("Não foi possível encontrar mensagem do assistente para salvar audio_url")
                
        except ImportError as e:
            # Edge-TTS não está instalado
            logger.error(f"Edge-TTS não está instalado: {str(e)}", exc_info=True)
            audio_url = None
        except Exception as e:
            # Não falhar se TTS falhar, apenas não incluir áudio
            # Log detalhado do erro para debug
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(
                f"Erro ao gerar áudio da resposta: {type(e).__name__}: {str(e)}\n{error_traceback}",
                exc_info=True
            )
            audio_url = None  # Garantir que audio_url seja None em caso de erro
    
    return {
        "answer": response["answer"],
        "audio_url": audio_url,
        "sources": response.get("source_documents", []),
        "validation": response.get("validation", {})  # Incluir validação e score de confiança
    }


@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """
    Retorna histórico de conversas do usuário
    
    Args:
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        skip: Offset para paginação
        limit: Limite de resultados (máximo 100)
    """
    from app.database import crud
    
    # Limitar máximo de resultados
    limit = min(limit, 100)
    
    # Buscar mensagens do banco
    messages = crud.get_user_chat_messages(db, current_user.id, skip=skip, limit=limit)
    
    # Converter para formato de resposta
    return {
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "audio_url": msg.audio_url,
                "created_at": msg.created_at.isoformat() if msg.created_at else None
            }
            for msg in messages
        ],
        "total": len(messages),
        "skip": skip,
        "limit": limit
    }


@router.get("/audio/{filename}")
async def get_audio_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    Serve arquivos de áudio gerados pelo TTS
    
    Args:
        filename: Nome do arquivo de áudio
        current_user: Usuário autenticado (validação de acesso)
    
    Returns:
        Arquivo de áudio
    """
    from fastapi.responses import FileResponse
    from app.core.audio_service import get_audio_service
    
    audio_service = get_audio_service()
    audio_path = audio_service.temp_dir / filename
    
    # Validar que o arquivo existe e está no diretório temporário
    if not audio_path.exists() or not str(audio_path).startswith(str(audio_service.temp_dir)):
        raise HTTPException(status_code=404, detail="Arquivo de áudio não encontrado")
    
    # Retornar arquivo com headers apropriados
    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=filename
    )

