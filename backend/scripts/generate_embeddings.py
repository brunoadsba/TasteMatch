"""
Script para gerar embeddings dos restaurantes que ainda não têm.
Processa 1 restaurante por vez para evitar crash de memória.
"""

import sys
import json
import gc
from pathlib import Path

# Adicionar o diretório raiz ao path para imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.base import SessionLocal
from app.database.crud import get_restaurants, update_restaurant_embedding
from app.core.embeddings import generate_restaurant_embedding, get_embedding_model, unload_model
from app.core.logging_config import setup_logging, get_logger
from sqlalchemy.orm import Session

# Configurar logging
setup_logging()
logger = get_logger(__name__)


def get_restaurants_without_embeddings(db: Session):
    """Retorna restaurantes que ainda não têm embeddings."""
    all_restaurants = get_restaurants(db, limit=1000)
    restaurants_without = [
        r for r in all_restaurants
        if r.embedding is None or r.embedding == ""
    ]
    return restaurants_without


def generate_embedding_for_restaurant(db: Session, restaurant):
    """Gera embedding para um restaurante e atualiza no banco."""
    try:
        logger.info(f"   🔄 Gerando embedding para: {restaurant.name}...")
        
        # Criar objeto RestaurantCreate para o embedding
        from app.models.restaurant import RestaurantCreate
        restaurant_data = RestaurantCreate(
            name=restaurant.name,
            cuisine_type=restaurant.cuisine_type,
            description=restaurant.description,
            rating=restaurant.rating,
            price_range=restaurant.price_range,
            location=restaurant.location
        )
        
        # Gerar embedding
        embedding = generate_restaurant_embedding(restaurant_data)
        embedding_json = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
        
        # Atualizar no banco
        update_restaurant_embedding(db, restaurant.id, embedding_json)
        
        logger.info(f"   ✅ Embedding gerado e salvo para: {restaurant.name}")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Erro ao gerar embedding para {restaurant.name}: {e}")
        return False


def main():
    """Função principal para gerar embeddings."""
    logger.info("=" * 60)
    logger.info("🔄 Iniciando geração de embeddings...")
    logger.info("📦 Processando 1 restaurante por vez (otimização de memória)")
    logger.info("=" * 60)
    logger.info("")
    
    db = SessionLocal()
    
    try:
        # 1. Buscar restaurantes sem embeddings
        restaurants_without = get_restaurants_without_embeddings(db)
        
        if not restaurants_without:
            logger.info("✅ Todos os restaurantes já têm embeddings!")
            return True
        
        logger.info(f"📊 Encontrados {len(restaurants_without)} restaurantes sem embeddings")
        logger.info("")
        
        # 2. Carregar modelo uma vez (ficará em cache)
        logger.info("⏳ Carregando modelo de embeddings...")
        model = get_embedding_model()
        logger.info("✅ Modelo carregado!")
        logger.info("")
        
        # 3. Processar 1 restaurante por vez
        generated = 0
        failed = 0
        
        for i, restaurant in enumerate(restaurants_without, 1):
            logger.info(f"[{i}/{len(restaurants_without)}] Processando {restaurant.name}...")
            
            success = generate_embedding_for_restaurant(db, restaurant)
            
            if success:
                generated += 1
                # Commit após cada restaurante
                db.commit()
            else:
                failed += 1
                db.rollback()
            
            # Limpeza agressiva de memória após cada restaurante
            gc.collect()
            
            logger.info("")  # Linha em branco para separar
            
            # Pausa pequena para dar tempo ao garbage collector
            import time
            time.sleep(0.5)
        
        logger.info("=" * 60)
        logger.info("✅ Geração de embeddings concluída!")
        logger.info(f"   - {generated} embeddings gerados com sucesso")
        if failed > 0:
            logger.info(f"   - {failed} falhas")
        logger.info("=" * 60)
        
        # Descarregar modelo após terminar
        logger.info("\n🧹 Liberando memória...")
        try:
            unload_model()
            logger.info("✅ Memória liberada")
        except Exception as e:
            logger.warning(f"⚠️  Aviso ao liberar memória: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante geração de embeddings: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

