"""
Script para validar migração para Supabase
"""
from app.database.base import SessionLocal
from sqlalchemy import text

def validate_migration():
    """Valida migração completa para Supabase"""
    db = SessionLocal()
    try:
        # 1. Testar conexão
        db.execute(text("SELECT 1"))
        print("✅ Conexão com Supabase OK")
        
        # 2. Verificar extensão vector
        result = db.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        if result.fetchone():
            print("✅ Extensão vector instalada")
        else:
            print("❌ Extensão vector NÃO encontrada")
            return False
        
        # 3. Contar registros
        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        restaurants_count = db.execute(text("SELECT COUNT(*) FROM restaurants")).scalar()
        orders_count = db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        recommendations_count = db.execute(text("SELECT COUNT(*) FROM recommendations")).scalar()
        
        print(f"✅ Usuários: {users_count}")
        print(f"✅ Restaurantes: {restaurants_count}")
        print(f"✅ Pedidos: {orders_count}")
        print(f"✅ Recomendações: {recommendations_count}")
        
        # 4. Verificar embeddings
        embeddings_count = db.execute(
            text("SELECT COUNT(*) FROM restaurants WHERE embedding IS NOT NULL")
        ).scalar()
        print(f"✅ Restaurantes com embeddings: {embeddings_count}")
        
        # 5. Verificar base RAG
        try:
            rag_count = db.execute(
                text("SELECT COUNT(*) FROM langchain_pg_collection WHERE name = 'tastematch_knowledge'")
            ).scalar()
            if rag_count > 0:
                print("✅ Base RAG encontrada")
            else:
                print("⚠️ Base RAG não encontrada (pode ser normal se ainda não migrada)")
        except Exception as e:
            print(f"⚠️ Não foi possível verificar base RAG: {e}")
        
        print("\n✅ Validação completa!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na validação: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    validate_migration()

