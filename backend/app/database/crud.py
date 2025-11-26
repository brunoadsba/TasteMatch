"""
Operações CRUD (Create, Read, Update, Delete) para o TasteMatch.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from typing import Optional, List
from app.database.models import User, Restaurant, Order, Recommendation, UserPreferences
from app.models.user import UserCreate
from app.models.restaurant import RestaurantCreate
from app.models.order import OrderCreate


# ==================== USERS ====================

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Busca um usuário por ID."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Busca um usuário por email."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, user: UserCreate, password_hash: str) -> User:
    """Cria um novo usuário."""
    db_user = User(
        email=user.email,
        name=user.name,
        password_hash=password_hash
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ==================== RESTAURANTS ====================

def get_restaurant(db: Session, restaurant_id: int) -> Optional[Restaurant]:
    """Busca um restaurante por ID."""
    return db.get(Restaurant, restaurant_id)


def get_restaurants(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    cuisine_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    price_range: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None
) -> List[Restaurant]:
    """Lista restaurantes com filtros opcionais e ordenação."""
    stmt = select(Restaurant)
    
    # Filtros
    if cuisine_type:
        stmt = stmt.where(Restaurant.cuisine_type == cuisine_type)
    
    if min_rating is not None:
        stmt = stmt.where(Restaurant.rating >= min_rating)
    
    if price_range:
        stmt = stmt.where(Restaurant.price_range == price_range)
    
    if search:
        # Busca textual no nome e descrição (case-insensitive)
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            (Restaurant.name.ilike(search_pattern)) |
            (Restaurant.description.ilike(search_pattern))
        )
    
    # Ordenação
    if sort_by == "rating_desc":
        stmt = stmt.order_by(Restaurant.rating.desc(), Restaurant.name.asc())
    elif sort_by == "rating_asc":
        stmt = stmt.order_by(Restaurant.rating.asc(), Restaurant.name.asc())
    elif sort_by == "name_asc":
        stmt = stmt.order_by(Restaurant.name.asc())
    elif sort_by == "name_desc":
        stmt = stmt.order_by(Restaurant.name.desc())
    else:
        # Default: ordenar por rating desc (maior primeiro)
        stmt = stmt.order_by(Restaurant.rating.desc(), Restaurant.name.asc())
    
    stmt = stmt.offset(skip).limit(limit)
    result = db.execute(stmt)
    restaurants = list(result.scalars().all())
    
    # Garantir que não há duplicatas (mesmo ID) - segurança adicional
    seen_ids = set()
    unique_restaurants = []
    for restaurant in restaurants:
        if restaurant.id not in seen_ids:
            unique_restaurants.append(restaurant)
            seen_ids.add(restaurant.id)
    
    return unique_restaurants


def create_restaurant(db: Session, restaurant: RestaurantCreate, embedding: Optional[str] = None) -> Restaurant:
    """Cria um novo restaurante."""
    db_restaurant = Restaurant(
        name=restaurant.name,
        cuisine_type=restaurant.cuisine_type,
        description=restaurant.description,
        rating=float(restaurant.rating),
        price_range=restaurant.price_range,
        location=restaurant.location,
        embedding=embedding
    )
    db.add(db_restaurant)
    db.commit()
    db.refresh(db_restaurant)
    return db_restaurant


def update_restaurant_embedding(db: Session, restaurant_id: int, embedding: str) -> Optional[Restaurant]:
    """Atualiza o embedding de um restaurante."""
    db_restaurant = db.get(Restaurant, restaurant_id)
    if db_restaurant:
        db_restaurant.embedding = embedding
        db.commit()
        db.refresh(db_restaurant)
    return db_restaurant


# ==================== ORDERS ====================

def get_order(db: Session, order_id: int) -> Optional[Order]:
    """Busca um pedido por ID."""
    return db.get(Order, order_id)


def get_user_orders(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[Order]:
    """Lista pedidos de um usuário com eager loading do restaurante."""
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.order_date.desc())
        .options(joinedload(Order.restaurant))
        .offset(skip)
        .limit(limit)
    )
    result = db.execute(stmt)
    return list(result.scalars().unique().all())


def create_order(db: Session, order: OrderCreate, user_id: int) -> Order:
    """Cria um novo pedido."""
    import json
    
    db_order = Order(
        user_id=user_id,
        restaurant_id=order.restaurant_id,
        order_date=order.order_date,
        total_amount=order.total_amount,
        items=json.dumps(order.items) if order.items else None,
        rating=order.rating,
        is_simulation=order.is_simulation if hasattr(order, 'is_simulation') and order.is_simulation else False
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


# ==================== RECOMMENDATIONS ====================

def get_recommendation(
    db: Session,
    user_id: int,
    restaurant_id: int
) -> Optional[Recommendation]:
    """Busca uma recomendação específica."""
    stmt = select(Recommendation).where(
        Recommendation.user_id == user_id,
        Recommendation.restaurant_id == restaurant_id
    )
    return db.execute(stmt).scalar_one_or_none()


def get_user_recommendations(
    db: Session,
    user_id: int,
    limit: int = 10
) -> List[Recommendation]:
    """Lista recomendações de um usuário."""
    stmt = select(Recommendation).where(
        Recommendation.user_id == user_id
    ).order_by(Recommendation.similarity_score.desc()).limit(limit)
    result = db.execute(stmt)
    return list(result.scalars().all())


def create_recommendation(
    db: Session,
    user_id: int,
    restaurant_id: int,
    similarity_score: float,
    insight_text: Optional[str] = None
) -> Recommendation:
    """Cria uma nova recomendação."""
    db_recommendation = Recommendation(
        user_id=user_id,
        restaurant_id=restaurant_id,
        similarity_score=similarity_score,
        insight_text=insight_text
    )
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation


# ==================== USER PREFERENCES ====================

def get_user_preferences(db: Session, user_id: int) -> Optional[UserPreferences]:
    """Busca preferências de um usuário."""
    stmt = select(UserPreferences).where(UserPreferences.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def create_or_update_user_preferences(
    db: Session,
    user_id: int,
    preference_embedding: str,
    favorite_cuisines: Optional[str] = None
) -> UserPreferences:
    """Cria ou atualiza preferências de um usuário."""
    existing = get_user_preferences(db, user_id)
    
    if existing:
        existing.preference_embedding = preference_embedding
        if favorite_cuisines:
            existing.favorite_cuisines = favorite_cuisines
        db.commit()
        db.refresh(existing)
        return existing
    else:
        db_preferences = UserPreferences(
            user_id=user_id,
            preference_embedding=preference_embedding,
            favorite_cuisines=favorite_cuisines
        )
        db.add(db_preferences)
        db.commit()
        db.refresh(db_preferences)
        return db_preferences

