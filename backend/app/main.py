"""
TasteMatch - Agente de Recomendação Inteligente
Main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.config import settings

# TODO: Importar routers quando criados
# from app.api.routes import auth, recommendations, restaurants, orders, users

app = FastAPI(
    title=settings.APP_NAME,
    description="Agente de Recomendação Inteligente para Delivery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Frontend em desenvolvimento
        "http://localhost:5173",  # Vite dev server
        # "https://tastematch.netlify.app",  # Frontend em produção (adicionar quando deployar)
    ],
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
            database_status = "connected"
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


# TODO: Incluir routers quando criados
# app.include_router(auth.router, prefix="/auth", tags=["authentication"])
# app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
# app.include_router(restaurants.router, prefix="/api", tags=["restaurants"])
# app.include_router(orders.router, prefix="/api", tags=["orders"])
# app.include_router(users.router, prefix="/api", tags=["users"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

