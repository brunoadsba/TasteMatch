"""
Script para popular o banco de dados com dados de exemplo.
Inclui geração automática de embeddings para restaurantes.
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
    create_or_update_user_preferences
)
from app.models.user import UserCreate
from app.models.restaurant import RestaurantCreate
from app.models.order import OrderCreate
from app.core.embeddings import generate_restaurant_embedding
from app.core.security import get_password_hash


# Dados de exemplo
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
    {"name": "Fogo de Chão", "cuisine_type": "brasileira", "description": "Churrascaria rodízio premium", "rating": 4.8, "price_range": "high", "location": "Jardins"},
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


def seed_restaurants(db):
    """Cria restaurantes com embeddings."""
    print("🍽️  Criando restaurantes...")
    print("   ⏳ Carregando modelo de embeddings (pode demorar na primeira vez)...")
    
    # Pré-carregar o modelo antes do loop para evitar múltiplos carregamentos
    try:
        from app.core.embeddings import get_embedding_model
        model = get_embedding_model()
        print("   ✅ Modelo de embeddings carregado!")
    except Exception as e:
        print(f"   ⚠️  Aviso ao carregar modelo: {e}")
        model = None
    
    restaurants = []
    for i, rest_data in enumerate(RESTAURANTS_DATA, 1):
        restaurant = RestaurantCreate(**rest_data)
        
        # Gerar embedding para o restaurante
        try:
            print(f"   🔄 [{i}/{len(RESTAURANTS_DATA)}] Gerando embedding para {restaurant.name}...", end=" ", flush=True)
            embedding = generate_restaurant_embedding(restaurant)
            embedding_json = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
            print("✅")
        except Exception as e:
            print(f"⚠️  Erro: {e}")
            embedding_json = None
        
        try:
            db_restaurant = create_restaurant(db, restaurant, embedding=embedding_json)
            restaurants.append(db_restaurant)
        except Exception as e:
            print(f"   ❌ Erro ao criar restaurante {restaurant.name}: {e}")
    
    print(f"\n✅ {len(restaurants)} restaurantes criados com embeddings!\n")
    return restaurants


def seed_users(db):
    """Cria usuários de exemplo."""
    print("👥 Criando usuários...")
    
    users = []
    for user_data in USERS_DATA:
        user_create = UserCreate(**user_data)
        password_hash = get_password_hash(user_data["password"])
        db_user = create_user(db, user_create, password_hash)
        users.append(db_user)
        print(f"   ✅ {db_user.name} ({db_user.email})")
    
    print(f"\n✅ {len(users)} usuários criados!\n")
    return users


def seed_orders(db, users, restaurants):
    """Cria pedidos de exemplo para gerar histórico."""
    print("📦 Criando pedidos de exemplo...")
    
    orders = []
    items_examples = [
        [{"name": "Pizza Margherita", "quantity": 1, "price": 35.90}],
        [{"name": "Sushi Combo", "quantity": 1, "price": 45.90}],
        [{"name": "Whopper", "quantity": 1, "price": 25.90}, {"name": "Batata Frita", "quantity": 1, "price": 10.00}],
        [{"name": "Lasanha", "quantity": 1, "price": 42.50}],
        [{"name": "Temaki Salmão", "quantity": 2, "price": 18.90}],
    ]
    
    # Criar 50-100 pedidos distribuídos entre os usuários
    num_orders = random.randint(50, 100)
    
    for i in range(num_orders):
        user = random.choice(users)
        restaurant = random.choice(restaurants)
        
        # Data aleatória nos últimos 90 dias
        days_ago = random.randint(0, 90)
        order_date = datetime.now() - timedelta(days=days_ago)
        
        # Valor total aleatório
        total_amount = round(random.uniform(20.0, 80.0), 2)
        
        # Itens aleatórios
        items = random.choice(items_examples)
        
        # Rating aleatório (1-5)
        rating = random.randint(3, 5)
        
        order_create = OrderCreate(
            restaurant_id=restaurant.id,
            order_date=order_date,
            total_amount=total_amount,
            items=items,
            rating=rating
        )
        
        db_order = create_order(db, order_create, user.id)
        orders.append(db_order)
        
        if (i + 1) % 10 == 0:
            print(f"   ✅ {i + 1}/{num_orders} pedidos criados...")
    
    print(f"\n✅ {len(orders)} pedidos criados!\n")
    return orders


def main():
    """Função principal de seeding."""
    import time
    start_time = time.time()
    
    print("🌱 Iniciando seeding do banco de dados...\n")
    
    db = SessionLocal()
    
    try:
        # 1. Criar restaurantes com embeddings
        print("=" * 50)
        print("ETAPA 1/3: Restaurantes")
        print("=" * 50)
        restaurants = seed_restaurants(db)
        
        # 2. Criar usuários
        print("=" * 50)
        print("ETAPA 2/3: Usuários")
        print("=" * 50)
        users = seed_users(db)
        
        # 3. Criar pedidos
        print("=" * 50)
        print("ETAPA 3/3: Pedidos")
        print("=" * 50)
        orders = seed_orders(db, users, restaurants)
        
        elapsed_time = time.time() - start_time
        print("=" * 50)
        print("✅ Seeding concluído com sucesso!")
        print(f"   - {len(restaurants)} restaurantes")
        print(f"   - {len(users)} usuários")
        print(f"   - {len(orders)} pedidos")
        print(f"   - Tempo total: {elapsed_time:.2f} segundos")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Seeding interrompido pelo usuário (Ctrl+C)")
        db.rollback()
        return False
    except Exception as e:
        print(f"\n❌ Erro durante seeding: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

