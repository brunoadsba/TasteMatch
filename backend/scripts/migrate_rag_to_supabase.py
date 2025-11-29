"""
Script para migrar base de conhecimento RAG para Supabase
"""
from app.database.base import SessionLocal
from app.core.rag_service import RAGService
from app.core.knowledge_base import update_knowledge_base
from app.config import settings

def migrate_rag():
    """Migra base de conhecimento RAG para Supabase"""
    db = SessionLocal()
    try:
        print("🔄 Inicializando RAG service...")
        rag = RAGService(db, settings.DATABASE_URL)
        rag.initialize_vector_store("tastematch_knowledge")
        
        print("🔄 Recriando base de conhecimento...")
        update_knowledge_base(db, rag, user_id=None)
        
        print("✅ Base de conhecimento RAG migrada com sucesso")
    except Exception as e:
        print(f"❌ Erro ao migrar RAG: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_rag()

