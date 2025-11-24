"""
Script para inicializar o banco de dados.
Cria todas as tabelas definidas nos modelos SQLAlchemy.
"""

import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.base import Base, engine
from app.database.models import User, Restaurant, Order, Recommendation, UserPreferences
from app.config import settings


def init_db():
    """Cria todas as tabelas no banco de dados."""
    
    print(f"🔧 Inicializando banco de dados: {settings.DATABASE_URL}")
    
    # Importar todos os modelos para que Base tenha conhecimento deles
    # (já importados acima)
    
    try:
        # Criar todas as tabelas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tabelas criadas com sucesso!")
        print("\n📋 Tabelas criadas:")
        print("   - users")
        print("   - restaurants")
        print("   - orders")
        print("   - recommendations")
        print("   - user_preferences")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)

