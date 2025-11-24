"""
TasteMatch - Agente de Recomendação Inteligente
Main application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.config import settings

# Importar routers
from app.api.routes import auth, users, restaurants, orders, recommendations

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
        "http://localhost:5173",  # Vite dev server (porta padrão)
        "http://localhost:5174",  # Vite dev server (porta alternativa)
        "http://127.0.0.1:5173",  # Vite dev server (IP localhost)
        "http://127.0.0.1:5174",  # Vite dev server (IP localhost, porta alternativa)
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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

