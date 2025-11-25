"""
Testes unitários para módulo de recomendação.
"""
import pytest
import json
from datetime import datetime, timedelta

from app.core.recommender import (
    calculate_weight,
    calculate_user_preference_embedding,
    extract_user_patterns,
    calculate_similarity,
    get_popular_restaurants,
    generate_recommendations
)
from app.database.models import User, Restaurant, Order


class TestCalculateWeight:
    """Testes para cálculo de peso de pedidos."""
    
    def test_recent_order_high_weight(self):
        """Testa que pedidos recentes têm peso alto."""
        recent_date = datetime.now() - timedelta(days=1)
        weight = calculate_weight(recent_date, rating=5)
        
        assert weight > 0.9  # Pedido muito recente e bem avaliado
    
    def test_old_order_low_weight(self):
        """Testa que pedidos antigos têm peso baixo."""
        old_date = datetime.now() - timedelta(days=365)
        weight = calculate_weight(old_date, rating=5)
        
        assert weight < 0.1  # Pedido muito antigo
    
    def test_high_rating_increases_weight(self):
        """Testa que rating alto aumenta o peso."""
        date = datetime.now() - timedelta(days=30)
        
        weight_high = calculate_weight(date, rating=5)
        weight_low = calculate_weight(date, rating=2)
        
        assert weight_high > weight_low
    
    def test_no_rating_default_weight(self):
        """Testa que pedido sem rating usa peso padrão."""
        date = datetime.now() - timedelta(days=30)
        weight = calculate_weight(date, rating=None)
        
        assert 0.0 < weight < 1.0


class TestExtractUserPatterns:
    """Testes para extração de padrões do usuário."""
    
    def test_extract_patterns_empty_orders(self, test_db):
        """Testa extração de padrões com lista vazia de pedidos."""
        user = User(id=1, email="test@example.com", password_hash="hash", name="Test")
        orders = []
        restaurants = []
        
        patterns = extract_user_patterns(1, orders, restaurants)
        
        assert patterns["total_orders"] == 0
        assert patterns["favorite_cuisines"] == []
        assert patterns["average_order_value"] == 0.0
    
    def test_extract_patterns_favorite_cuisines(self, test_db, test_restaurants):
        """Testa extração de culinárias favoritas."""
        user = User(id=1, email="test@example.com", password_hash="hash", name="Test")
        test_db.add(user)
        test_db.commit()
        
        # Criar pedidos para diferentes culinárias
        orders = [
            Order(
                user_id=1,
                restaurant_id=test_restaurants[0].id,  # Italian
                order_date=datetime.now(),
                total_amount=50.0
            ),
            Order(
                user_id=1,
                restaurant_id=test_restaurants[0].id,  # Italian novamente
                order_date=datetime.now(),
                total_amount=45.0
            ),
            Order(
                user_id=1,
                restaurant_id=test_restaurants[1].id,  # Japanese
                order_date=datetime.now(),
                total_amount=60.0
            ),
        ]
        test_db.add_all(orders)
        test_db.commit()
        
        patterns = extract_user_patterns(1, orders, test_restaurants)
        
        assert patterns["total_orders"] == 3
        assert "Italian" in patterns["favorite_cuisines"]
        assert len(patterns["favorite_cuisines"]) > 0
    
    def test_extract_patterns_average_order_value(self, test_db, test_restaurants):
        """Testa cálculo de ticket médio."""
        user = User(id=1, email="test@example.com", password_hash="hash", name="Test")
        test_db.add(user)
        test_db.commit()
        
        orders = [
            Order(
                user_id=1,
                restaurant_id=test_restaurants[0].id,
                order_date=datetime.now(),
                total_amount=50.0
            ),
            Order(
                user_id=1,
                restaurant_id=test_restaurants[1].id,
                order_date=datetime.now(),
                total_amount=100.0
            ),
        ]
        test_db.add_all(orders)
        test_db.commit()
        
        patterns = extract_user_patterns(1, orders, test_restaurants)
        
        assert patterns["average_order_value"] == 75.0


class TestCalculateSimilarity:
    """Testes para cálculo de similaridade."""
    
    def test_identical_embeddings_high_similarity(self):
        """Testa que embeddings idênticos têm similaridade 1."""
        embedding = [0.1, 0.2, 0.3, 0.4]
        
        similarity = calculate_similarity(embedding, embedding)
        
        assert abs(similarity - 1.0) < 0.01
    
    def test_different_embeddings_lower_similarity(self):
        """Testa que embeddings diferentes têm similaridade menor que 1."""
        embedding1 = [1.0, 0.0, 0.0, 0.0]
        embedding2 = [0.0, 1.0, 0.0, 0.0]
        
        similarity = calculate_similarity(embedding1, embedding2)
        
        assert similarity < 1.0
        assert similarity >= -1.0  # Similaridade coseno entre -1 e 1
    
    def test_similarity_range(self):
        """Testa que similaridade está no range correto."""
        embedding1 = [0.1, 0.2, 0.3]
        embedding2 = [0.4, 0.5, 0.6]
        
        similarity = calculate_similarity(embedding1, embedding2)
        
        assert -1.0 <= similarity <= 1.0


class TestGenerateRecommendations:
    """Testes para geração de recomendações."""
    
    def test_cold_start_returns_popular_restaurants(self, test_db, test_restaurants):
        """Testa que usuário sem histórico recebe restaurantes populares."""
        user = User(
            email="newuser@example.com",
            password_hash="hash",
            name="New User"
        )
        test_db.add(user)
        test_db.commit()
        
        recommendations = generate_recommendations(
            user_id=user.id,
            db=test_db,
            limit=5
        )
        
        # Deve retornar restaurantes populares (cold start)
        assert len(recommendations) > 0
        assert len(recommendations) <= 5
        # Todos devem ter similarity_score = 0.5 (fallback)
        for rec in recommendations:
            assert rec["similarity_score"] == 0.5
    
    def test_recommendations_exclude_recent(self, test_db, test_user, test_restaurants):
        """Testa que recomendações excluem restaurantes recentes."""
        # Criar pedido recente
        recent_order = Order(
            user_id=test_user.id,
            restaurant_id=test_restaurants[0].id,
            order_date=datetime.now(),
            total_amount=50.0
        )
        test_db.add(recent_order)
        test_db.commit()
        
        # Gerar recomendações com exclude_recent=True
        recommendations = generate_recommendations(
            user_id=test_user.id,
            db=test_db,
            limit=10,
            exclude_recent=True
        )
        
        # O restaurante recente não deve estar nas recomendações
        recent_restaurant_ids = [rec["restaurant"].id for rec in recommendations]
        assert test_restaurants[0].id not in recent_restaurant_ids
    
    def test_recommendations_respect_min_rating(self, test_db, test_user, test_restaurants):
        """Testa que recomendações respeitam rating mínimo."""
        # Criar restaurante com rating baixo
        low_rating_restaurant = Restaurant(
            name="Low Rating",
            cuisine_type="Fast Food",
            location="123 St, City, ST 12345",
            rating=2.0,  # Rating muito baixo
            embedding='[0.1, 0.2, 0.3]'
        )
        test_db.add(low_rating_restaurant)
        test_db.commit()
        
        recommendations = generate_recommendations(
            user_id=test_user.id,
            db=test_db,
            limit=10,
            min_rating=3.5
        )
        
        # Restaurantes recomendados devem ter rating >= 3.5
        for rec in recommendations:
            assert rec["restaurant"].rating >= 3.5

