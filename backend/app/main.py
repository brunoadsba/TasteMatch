"""
TasteMatch - Agente de Recomendação Inteligente
Main application entry point.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
import os
from app.config import settings
from app.core.logging_config import setup_logging, get_logger

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
from app.api.routes import auth, users, restaurants, orders, recommendations, onboarding

app = FastAPI(
    title=settings.APP_NAME,
    description="Agente de Recomendação Inteligente para Delivery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logar todas as requisições HTTP."""
    start_time = time.time()
    
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
    
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code}",
        extra=extra
    )
    
    return response

logger.info("Aplicação FastAPI inicializada", extra={"app_name": settings.APP_NAME, "environment": settings.ENVIRONMENT})

# Configuração CORS
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


@app.get("/health")
async def health_check():
    """
    Health check endpoint para monitoramento da aplicação.
    
    Returns:
        dict: Status da aplicação e banco de dados
    """
    from app.database.base import engine
    
    # Verificar conexão com banco de dados
    try:
        with engine.connect() as conn:
            # Verificar se há tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            database_status = f"connected ({len(tables)} tables)"
    except Exception as e:
        database_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy",
        "database": database_status,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

