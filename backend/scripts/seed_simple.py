"""
Script para popular banco de dados em produção SEM embeddings.
Versão leve que não carrega modelo de ML - evita crash de memória.
Embeddings podem ser gerados depois com outro script.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# Adicionar o diretório raiz ao path para imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.base import SessionLocal
from app.database.crud import (
    create_user, create_restaurant, create_order,
    get_user_by_email, get_restaurants
)
from app.models.user import UserCreate
from app.models.restaurant import RestaurantCreate
from app.models.order import OrderCreate
from app.core.security import get_password_hash
from app.core.logging_config import setup_logging, get_logger

# Configurar logging
setup_logging()
logger = get_logger(__name__)

# Dados de exemplo (25 restaurantes)
RESTAURANTS_DATA = [
    {"name": "Sushi House", "cuisine_type": "japonesa", "description": "Sushi fresco e autêntico", "rating": 4.8, "price_range": "high", "location": "Jardins"},
    {"name": "Pizzaria Bella", "cuisine_type": "italiana", "description": "Pizzas artesanais com ingredientes frescos", "rating": 4.5, "price_range": "medium", "location": "Centro"},
    {"name": "Burger King", "cuisine_type": "hamburgueria", "description": "Hambúrgueres clássicos e deliciosos", "rating": 4.2, "price_range": "low", "location": "Shopping"},
    {"name": "Cantina Italiana", "cuisine_type": "italiana", "description": "Massas caseiras e vinhos selecionados", "rating": 4.6, "price_range": "medium", "location": "Vila Madalena"},
    {"name": "Temaki Express", "cuisine_type": "japonesa", "description": "Temakis e comida japonesa rápida", "rating": 4.3, "price_range": "medium", "location": "Pinheiros"},
    {"name": "McDonald's", "cuisine_type": "hamburgueria", "description": "Fast food clássico", "rating": 4.0, "price_range": "low", "location": "Centro"},
    {"name": "Outback Steakhouse", "cuisine_type": "americana", "description": "Carnes grelhadas e ambiente descontraído", "rating": 4.7, "price_range": "high", "location": "Jardins"},
    {"name": "Domino's Pizza", "cuisine_type": "italiana", "description": "Pizzas delivery rápidas", "rating": 4.1, "price_range": "low", "location": "Vila Olímpia"},
    {"name": "KFC", "cuisine_type": "americana", "description": "Frango frito crocante", "rating": 4.2, "price_range": "low", "location": "Shopping"},
    {"name": "Subway", "cuisine_type": "sanduíches", "description": "Sanduíches personalizados", "rating": 4.0, "price_range": "low", "location": "Centro"},
    {"name": "Giraffas", "cuisine_type": "brasileira", "description": "Comida brasileira rápida", "rating": 4.3, "price_range": "medium", "location": "Vila Madalena"},
    {"name": "Habib's", "cuisine_type": "árabe", "description": "Comida árabe e esfihas", "rating": 4.4, "price_range": "low", "location": "Centro"},
    {"name": "Spoleto", "cuisine_type": "italiana", "description": "Massas personalizadas", "rating": 4.2, "price_range": "medium", "location": "Shopping"},
    {"name": "Viena", "cuisine_type": "brasileira", "description": "Comida brasileira tradicional", "rating": 4.5, "price_range": "medium", "location": "Jardins"},
    {"name": "China in Box", "cuisine_type": "chinesa", "description": "Comida chinesa delivery", "rating": 4.1, "price_range": "medium", "location": "Pinheiros"},
    {"name": "Taco Bell", "cuisine_type": "mexicana", "description": "Comida mexicana rápida", "rating": 4.0, "price_range": "low", "location": "Shopping"},
    {"name": "Papa John's", "cuisine_type": "italiana", "description": "Pizzas artesanais", "rating": 4.3, "price_range": "medium", "location": "Vila Olímpia"},
    {"name": "Bob's", "cuisine_type": "hamburgueria", "description": "Hambúrgueres e milkshakes", "rating": 4.2, "price_range": "low", "location": "Centro"},
    {"name": "Coco Bambu", "cuisine_type": "brasileira", "description": "Frutos do mar e comida brasileira", "rating": 4.6, "price_range": "high", "location": "Jardins"},
    {"name": "Fogo de Chão", "cuisine_type": "brasileira", "description": "Churrascaria rodízio premium com picanha na brasa e cortes nobres", "rating": 4.8, "price_range": "high", "location": "Jardins"},
    {"name": "Barbacoa", "cuisine_type": "brasileira", "description": "Churrascaria com rodízio de carnes grelhadas e buffet completo", "rating": 4.7, "price_range": "high", "location": "Vila Olímpia"},
    {"name": "Churrascaria Gaúcha", "cuisine_type": "brasileira", "description": "Rodízio de churrasco gaúcho com picanha, costela e linguiça", "rating": 4.6, "price_range": "medium", "location": "Centro"},
    {"name": "Bovinus", "cuisine_type": "brasileira", "description": "Churrascaria premium com carnes selecionadas e ambiente sofisticado", "rating": 4.9, "price_range": "high", "location": "Jardins"},
    {"name": "Rodeio Grill", "cuisine_type": "brasileira", "description": "Rodízio de churrasco com variedade de carnes e acompanhamentos", "rating": 4.5, "price_range": "medium", "location": "Pinheiros"},
    {"name": "Mamãe Terra", "cuisine_type": "vegetariana", "description": "Comida vegetariana saudável", "rating": 4.4, "price_range": "medium", "location": "Pinheiros"},
    {"name": "Popeyes", "cuisine_type": "americana", "description": "Frango frito estilo Louisiana", "rating": 4.3, "price_range": "low", "location": "Shopping"},
    {"name": "Starbucks", "cuisine_type": "cafeteria", "description": "Cafés e lanches", "rating": 4.5, "price_range": "medium", "location": "Vila Madalena"},
    {"name": "Casa do Pão de Queijo", "cuisine_type": "brasileira", "description": "Pães de queijo e café mineiro", "rating": 4.6, "price_range": "low", "location": "Centro"},
    {"name": "Açaí do Bem", "cuisine_type": "brasileira", "description": "Açaí e bowls saudáveis", "rating": 4.4, "price_range": "medium", "location": "Pinheiros"},
]

USERS_DATA = [
    {"email": "joao@example.com", "name": "João Silva", "password": "123456"},
    {"email": "maria@example.com", "name": "Maria Santos", "password": "123456"},
    {"email": "pedro@example.com", "name": "Pedro Oliveira", "password": "123456"},
    {"email": "ana@example.com", "name": "Ana Costa", "password": "123456"},
    {"email": "carlos@example.com", "name": "Carlos Ferreira", "password": "123456"},
]


def seed_restaurants(db, skip_existing=True):
    """Cria restaurantes SEM embeddings (leve, não carrega modelo)."""
    logger.info("🍽️  Criando restaurantes (SEM embeddings - versão leve)...")
    
    existing_restaurants = get_restaurants(db, limit=100)
    existing_names = {r.name for r in existing_restaurants}
    
    restaurants = []
    created = 0
    skipped = 0
    
    for i, rest_data in enumerate(RESTAURANTS_DATA, 1):
        if skip_existing and rest_data["name"] in existing_names:
            skipped += 1
            logger.info(f"   ⏭️  {i}/{len(RESTAURANTS_DATA)} - {rest_data['name']} (já existe, pulando)")
            continue
        
        restaurant = RestaurantCreate(**rest_data)
        
        try:
            # Criar restaurante SEM embedding (None)
            db_restaurant = create_restaurant(db, restaurant, embedding=None)
            restaurants.append(db_restaurant)
            created += 1
            logger.info(f"   ✅ {i}/{len(RESTAURANTS_DATA)} - {db_restaurant.name}")
        except Exception as e:
            logger.error(f"   ❌ Erro ao criar restaurante {restaurant.name}: {e}")
    
    logger.info(f"\n✅ {created} restaurantes criados, {skipped} já existiam!\n")
    return restaurants


def seed_users(db, skip_existing=True):
    """Cria usuários de exemplo."""
    logger.info("👥 Criando usuários...")
    
    users = []
    created = 0
    skipped = 0
    
    for user_data in USERS_DATA:
        if skip_existing:
            existing_user = get_user_by_email(db, email=user_data["email"])
            if existing_user:
                users.append(existing_user)
                skipped += 1
                logger.info(f"   ⏭️  {user_data['name']} ({user_data['email']}) (já existe, pulando)")
                continue
        
        try:
            user_create = UserCreate(**user_data)
            password_hash = get_password_hash(user_data["password"])
            db_user = create_user(db, user_create, password_hash)
            users.append(db_user)
            created += 1
            logger.info(f"   ✅ {db_user.name} ({db_user.email})")
        except Exception as e:
            logger.error(f"   ❌ Erro ao criar usuário {user_data['email']}: {e}")
    
    logger.info(f"\n✅ {created} usuários criados, {skipped} já existiam!\n")
    return users


def seed_orders(db, users, restaurants, num_orders=50):
    """Cria pedidos de exemplo."""
    if not users or not restaurants:
        logger.warning("⚠️  Sem usuários ou restaurantes, pulando criação de pedidos")
        return []
    
    logger.info(f"📦 Criando {num_orders} pedidos de exemplo...")
    
    items_examples = [
        [{"name": "Pizza Margherita", "quantity": 1, "price": 35.90}],
        [{"name": "Sushi Combo", "quantity": 1, "price": 45.90}],
        [{"name": "Whopper", "quantity": 1, "price": 25.90}, {"name": "Batata Frita", "quantity": 1, "price": 10.00}],
        [{"name": "Lasanha", "quantity": 1, "price": 42.50}],
        [{"name": "Temaki Salmão", "quantity": 2, "price": 18.90}],
    ]
    
    orders = []
    created = 0
    
    for i in range(num_orders):
        user = random.choice(users)
        restaurant = random.choice(restaurants)
        
        days_ago = random.randint(0, 90)
        order_date = datetime.now() - timedelta(days=days_ago)
        total_amount = round(random.uniform(20.0, 80.0), 2)
        items = random.choice(items_examples)
        rating = random.randint(3, 5)
        
        try:
            order_create = OrderCreate(
                restaurant_id=restaurant.id,
                order_date=order_date,
                total_amount=total_amount,
                items=items,
                rating=rating
            )
            
            db_order = create_order(db, order_create, user.id)
            orders.append(db_order)
            created += 1
            
            if (i + 1) % 10 == 0:
                logger.info(f"   ✅ {i + 1}/{num_orders} pedidos criados...")
        except Exception as e:
            logger.error(f"   ❌ Erro ao criar pedido {i+1}: {e}")
    
    logger.info(f"\n✅ {created} pedidos criados!\n")
    return orders


def main():
    """Função principal de seeding (SEM embeddings)."""
    logger.info("=" * 60)
    logger.info("🌱 Iniciando seeding do banco de dados (versão leve)...")
    logger.info("📝 NOTA: Restaurantes serão criados SEM embeddings")
    logger.info("📝 Embeddings podem ser gerados depois com outro script")
    logger.info("=" * 60)
    logger.info("")
    
    db = SessionLocal()
    
    try:
        # 1. Criar restaurantes SEM embeddings
        restaurants = seed_restaurants(db, skip_existing=True)
        
        # Buscar todos os restaurantes
        all_restaurants = get_restaurants(db, limit=100)
        
        # 2. Criar usuários
        users = seed_users(db, skip_existing=True)
        
        # 3. Criar pedidos
        if users and all_restaurants:
            orders = seed_orders(db, users, all_restaurants, num_orders=50)
        else:
            orders = []
            logger.warning("⚠️  Pulando criação de pedidos (sem usuários ou restaurantes suficientes)")
        
        logger.info("=" * 60)
        logger.info("✅ Seeding concluído com sucesso!")
        logger.info(f"   - {len(all_restaurants)} restaurantes (total)")
        logger.info(f"   - {len(users)} usuários (total)")
        logger.info(f"   - {len(orders)} pedidos criados")
        logger.info("")
        logger.info("📝 PRÓXIMO PASSO:")
        logger.info("   Execute generate_embeddings.py para gerar embeddings dos restaurantes")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Erro durante seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

