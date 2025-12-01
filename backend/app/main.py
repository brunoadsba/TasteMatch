"""
TasteMatch - Agente de Recomendação Inteligente
Main application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time
import os
import traceback
from app.config import settings
from app.core.logging_config import setup_logging, get_logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limiter import limiter

# Configurar logging primeiro
setup_logging()
logger = get_logger(__name__)

# Validar configurações de produção ao iniciar
if settings.is_production:
    try:
        settings.validate_production_settings()
        logger.info("Configurações de produção validadas com sucesso")
    except ValueError as e:
        logger.error(f"Erro na validação de configurações de produção: {e}")
        raise

# Importar routers
from app.api.routes import auth, users, restaurants, orders, recommendations, onboarding, chat, metrics

app = FastAPI(
    title=settings.APP_NAME,
    description="Agente de Recomendação Inteligente para Delivery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuração CORS - DEVE SER ADICIONADO PRIMEIRO
# Configurar CORS baseado no ambiente
cors_origins = [
    "http://localhost:3000",  # Frontend em desenvolvimento
    "http://localhost:5173",  # Vite dev server (porta padrão)
    "http://localhost:5174",  # Vite dev server (porta alternativa)
    "http://127.0.0.1:5173",  # Vite dev server (IP localhost)
    "http://127.0.0.1:5174",  # Vite dev server (IP localhost, porta alternativa)
    "http://127.0.0.1:8000",  # Backend local (caso necessário)
    "https://tastematch.netlify.app",  # Frontend em produção (Netlify)
]

# Adicionar origem de produção se configurada via variável de ambiente
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url and frontend_url not in cors_origins:
    cors_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Handler global para capturar exceções não tratadas
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para capturar todas as exceções não tratadas."""
    import traceback
    error_traceback = traceback.format_exc()
    
    # Log completo do erro
    logger.error(
        f"Erro não tratado: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "endpoint": str(request.url.path),
            "method": request.method,
            "traceback": error_traceback
        }
    )
    
    # Determinar origem da requisição para CORS
    # IMPORTANTE: Não podemos usar "*" com allow_credentials=True
    origin = request.headers.get("origin")
    headers = {}
    
    if origin:
        # Verificar se a origem está na lista permitida
        if origin in cors_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        else:
            # Se origem não está permitida, usar a primeira origem permitida como fallback
            # Isso garante que o header CORS esteja presente
            if cors_origins:
                headers["Access-Control-Allow-Origin"] = cors_origins[0]
    else:
        # Se não há origem na requisição, usar primeira origem permitida
        if cors_origins:
            headers["Access-Control-Allow-Origin"] = cors_origins[0]
    
    # Sempre adicionar headers CORS básicos
    headers["Access-Control-Allow-Methods"] = "*"
    headers["Access-Control-Allow-Headers"] = "*"
    
    # Retornar erro 500 com detalhes (em desenvolvimento) ou mensagem genérica (em produção)
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"{type(exc).__name__}: {str(exc)}",
                "traceback": error_traceback.split('\n') if settings.DEBUG else None
            },
            headers=headers
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"},
            headers=headers
        )

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logar todas as requisições HTTP."""
    start_time = time.time()
    
    try:
        # Executar requisição
        response = await call_next(request)
        
        # Calcular duração
        duration_ms = (time.time() - start_time) * 1000
        
        # Log da requisição
        extra = {
            "endpoint": str(request.url.path),
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
        
        # Log de erro se status >= 500
        if response.status_code >= 500:
            logger.error(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra=extra
            )
        else:
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra=extra
            )
        
        return response
    except Exception as e:
        # Capturar exceções não tratadas pelo handler global
        import traceback
        error_traceback = traceback.format_exc()
        duration_ms = (time.time() - start_time) * 1000
        
        logger.error(
            f"Exceção não tratada no middleware: {type(e).__name__}: {str(e)}",
            exc_info=True,
            extra={
                "endpoint": str(request.url.path),
                "method": request.method,
                "duration_ms": round(duration_ms, 2),
                "traceback": error_traceback
            }
        )
        raise  # Re-raise para o handler global capturar


# Middleware para adicionar headers HTTP Cache-Control
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    """
    Middleware para adicionar headers de cache HTTP.
    
    OTIMIZAÇÃO: Reduz requisições ao backend permitindo que clientes/CDN façam cache.
    - Restaurantes: cache público de 5 minutos (dados mais estáticos)
    - Recomendações: cache privado de 10 minutos (dados personalizados)
    """
    response = await call_next(request)
    
    # Aplicar cache apenas para requisições GET bem-sucedidas
    if request.method == "GET" and response.status_code == 200:
        path = str(request.url.path)
        
        if "/api/restaurants" in path:
            # Restaurantes: dados mais estáticos, cache público
            response.headers["Cache-Control"] = "public, max-age=300"  # 5 minutos
        elif "/api/recommendations" in path:
            # Recomendações: dados personalizados, cache privado
            response.headers["Cache-Control"] = "private, max-age=600"  # 10 minutos
    
    return response

logger.info("Aplicação FastAPI inicializada", extra={"app_name": settings.APP_NAME, "environment": settings.ENVIRONMENT})


@app.get("/health")
async def health_check():
    """
    Health check endpoint para monitoramento da aplicação.
    
    Returns:
        dict: Status da aplicação e todos os bancos de dados
    """
    from app.database.base import engine, SessionLocal
    from sqlalchemy import inspect, text
    
    health_status = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "databases": {}
    }
    
    # Verificar conexão PostgreSQL principal
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            # Detectar tipo de banco
            is_supabase = os.getenv("DB_PROVIDER", "").lower() == "supabase" or "supabase" in settings.DATABASE_URL.lower()
            db_type = "Supabase" if is_supabase else "PostgreSQL Local"
            
            # Verificar versão
            version_result = conn.execute(text("SELECT version()"))
            version = version_result.fetchone()[0][:50]  # Primeiros 50 caracteres
            
            health_status["databases"]["postgresql"] = {
                "status": "connected",
                "type": db_type,
                "tables": len(tables),
                "version": version
            }
    except Exception as e:
        health_status["databases"]["postgresql"] = {
            "status": "disconnected",
            "error": str(e)[:100]  # Primeiros 100 caracteres
        }
        health_status["status"] = "degraded"
    
    # Verificar extensão pgvector
    try:
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
            extension = result.fetchone()
            
            if extension:
                health_status["databases"]["pgvector"] = {
                    "status": "installed",
                    "extension": "vector"
                }
            else:
                health_status["databases"]["pgvector"] = {
                    "status": "not_installed",
                    "error": "Extensão pgvector não encontrada"
                }
                health_status["status"] = "degraded"
        finally:
            db.close()
    except Exception as e:
        health_status["databases"]["pgvector"] = {
            "status": "error",
            "error": str(e)[:100]
        }
        health_status["status"] = "degraded"
    
    # Verificar RAG Service (lazy - apenas verificar se pode inicializar)
    try:
        from app.core.rag_service import validate_database_requirements
        db = SessionLocal()
        try:
            connection_string = settings.DATABASE_URL
            if connection_string.startswith("postgres://"):
                connection_string = connection_string.replace("postgres://", "postgresql://", 1)
            
            validation = validate_database_requirements(connection_string, db)
            
            if validation["valid"]:
                health_status["databases"]["rag"] = {
                    "status": "ready",
                    "warnings": validation.get("warnings", [])
                }
            else:
                health_status["databases"]["rag"] = {
                    "status": "not_ready",
                    "errors": validation.get("errors", [])
                }
                health_status["status"] = "degraded"
        finally:
            db.close()
    except Exception as e:
        health_status["databases"]["rag"] = {
            "status": "error",
            "error": str(e)[:100]
        }
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/")
async def root():
    """
    Endpoint raiz da API.
    """
    return {
        "message": "TasteMatch API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Incluir routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(restaurants.router)
app.include_router(orders.router)
app.include_router(recommendations.router)
app.include_router(onboarding.router)
app.include_router(chat.router)
app.include_router(metrics.router, prefix="/api", tags=["metrics"])


@app.on_event("startup")
async def startup_event():
    """
    Eventos executados ao iniciar a aplicação
    """
    # Limpar arquivos temporários de áudio antigos
    try:
        from app.core.audio_service import get_audio_service
        audio_service = get_audio_service()
        deleted_count = audio_service.cleanup_temp_files(max_age_hours=24)
        if deleted_count > 0:
            logger.info(f"Limpeza de arquivos temporários: {deleted_count} arquivos deletados")
    except Exception as e:
        logger.warning(f"Erro ao limpar arquivos temporários no startup: {str(e)}")
    
    # Inicializar bancos de dados automaticamente
    try:
        from app.core.database_startup import initialize_databases
        db_init_results = await initialize_databases()
        
        # Log resumo final
        if db_init_results.get("overall_success"):
            logger.info("✅ Todos os bancos de dados inicializados com sucesso")
        else:
            logger.warning("⚠️  Alguns bancos de dados podem não estar totalmente configurados")
            logger.warning("   A aplicação continuará, mas algumas funcionalidades podem não funcionar")
    except Exception as e:
        logger.error(f"Erro crítico ao inicializar bancos de dados: {str(e)}", exc_info=True)
        logger.error("⚠️  Aplicação iniciada, mas bancos de dados podem não estar disponíveis")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

