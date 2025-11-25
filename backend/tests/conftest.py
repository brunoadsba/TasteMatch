"""
Configuração de testes com fixtures compartilhadas.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os

from app.database.base import Base, get_db
from app.main import app
from app.database.models import User, Restaurant, Order
from app.core.security import get_password_hash


# Criar banco de dados em memória para testes
@pytest.fixture(scope="function")
def test_db():
    """Cria banco de dados SQLite em memória para cada teste."""
    # Usar SQLite em memória
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Criar sessão
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Criar uma sessão
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Cria cliente de teste FastAPI com banco de dados de teste."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(test_db):
    """Cria um usuário de teste."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user_2(test_db):
    """Cria um segundo usuário de teste."""
    user = User(
        email="test2@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User 2"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_restaurant(test_db):
    """Cria um restaurante de teste com embedding."""
    restaurant = Restaurant(
        name="Test Restaurant",
        cuisine_type="Italian",
        description="A test Italian restaurant",
        location="123 Test St, Test City, TS 12345",
        rating=4.5,
        price_range="$$",
        embedding='[0.1, 0.2, 0.3]'  # Embedding simplificado para testes
    )
    test_db.add(restaurant)
    test_db.commit()
    test_db.refresh(restaurant)
    return restaurant


@pytest.fixture
def test_restaurants(test_db):
    """Cria múltiplos restaurantes de teste."""
    restaurants = [
        Restaurant(
            name="Italian Place",
            cuisine_type="Italian",
            description="Great Italian food",
            location="100 Main St, City, ST 12345",
            rating=4.5,
            price_range="$$",
            embedding='[0.1, 0.2, 0.3, 0.4]'
        ),
        Restaurant(
            name="Sushi Bar",
            cuisine_type="Japanese",
            description="Fresh sushi",
            location="200 Main St, City, ST 12345",
            rating=4.8,
            price_range="$$$",
            embedding='[0.2, 0.3, 0.4, 0.5]'
        ),
        Restaurant(
            name="Burger Joint",
            cuisine_type="American",
            description="Classic burgers",
            location="300 Main St, City, ST 12345",
            rating=4.2,
            price_range="$",
            embedding='[0.3, 0.4, 0.5, 0.6]'
        ),
    ]
    
    for restaurant in restaurants:
        test_db.add(restaurant)
    
    test_db.commit()
    
    for restaurant in restaurants:
        test_db.refresh(restaurant)
    
    return restaurants


@pytest.fixture
def test_order(test_db, test_user, test_restaurant):
    """Cria um pedido de teste."""
    from datetime import datetime
    
    order = Order(
        user_id=test_user.id,
        restaurant_id=test_restaurant.id,
        total_amount=45.99,
        order_date=datetime.now(),
        rating=5
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)
    return order


@pytest.fixture
def auth_token(client, test_user):
    """Obtém token JWT autenticado."""
    response = client.post(
        "/auth/login",
        json={
            "email": test_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture
def authenticated_client(client, auth_token):
    """Retorna cliente com token de autenticação configurado."""
    client.headers = {"Authorization": f"Bearer {auth_token}"}
    return client

