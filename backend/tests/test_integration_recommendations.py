"""
Testes de integração para endpoints de recomendações.
"""
import pytest
import json
from datetime import datetime


class TestRecommendationsEndpoint:
    """Testes para endpoint /api/recommendations."""
    
    def test_get_recommendations_requires_auth(self, client):
        """Testa que endpoint de recomendações requer autenticação."""
        response = client.get("/api/recommendations")
        
        # Pode retornar 401 (Unauthorized) ou 403 (Forbidden) dependendo da implementação
        assert response.status_code in [401, 403]
    
    def test_get_recommendations_cold_start(self, authenticated_client, test_user, test_restaurants):
        """Testa recomendações para usuário sem histórico (cold start)."""
        response = authenticated_client.get("/api/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert "count" in data
        assert "generated_at" in data
        
        recommendations = data["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0  # Deve retornar restaurantes populares
    
    def test_get_recommendations_with_limit(self, authenticated_client, test_restaurants):
        """Testa recomendações com parâmetro limit."""
        response = authenticated_client.get("/api/recommendations?limit=2")
        
        assert response.status_code == 200
        data = response.json()
        recommendations = data["recommendations"]
        
        assert len(recommendations) <= 2
    
    def test_get_recommendations_structure(self, authenticated_client, test_restaurants):
        """Testa estrutura da resposta de recomendações."""
        response = authenticated_client.get("/api/recommendations?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "recommendations" in data
        assert "count" in data
        assert "generated_at" in data
        
        if len(data["recommendations"]) > 0:
            rec = data["recommendations"][0]
            assert "restaurant" in rec
            assert "similarity_score" in rec
            assert isinstance(rec["similarity_score"], (int, float))
            assert 0 <= rec["similarity_score"] <= 1
    
    def test_get_recommendations_with_history(self, authenticated_client, test_user, test_restaurants, test_db):
        """Testa recomendações para usuário com histórico de pedidos."""
        from app.database.models import Order
        
        # Criar pedidos para o usuário
        orders = [
            Order(
                user_id=test_user.id,
                restaurant_id=test_restaurants[0].id,
                order_date=datetime.now(),
                total_amount=50.0,
                rating=5
            ),
            Order(
                user_id=test_user.id,
                restaurant_id=test_restaurants[0].id,
                order_date=datetime.now(),
                total_amount=45.0,
                rating=4
            ),
        ]
        test_db.add_all(orders)
        
        # Adicionar embeddings aos restaurantes
        for restaurant in test_restaurants:
            if not restaurant.embedding:
                restaurant.embedding = json.dumps([0.1 + i * 0.1, 0.2 + i * 0.1, 0.3 + i * 0.1, 0.4 + i * 0.1] * 96)  # 384 dims
        test_db.commit()
        
        response = authenticated_client.get("/api/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) > 0


class TestInsightEndpoint:
    """Testes para endpoint /api/recommendations/{id}/insight."""
    
    def test_get_insight_requires_auth(self, client, test_restaurant):
        """Testa que endpoint de insight requer autenticação."""
        response = client.get(f"/api/recommendations/{test_restaurant.id}/insight")
        
        # Pode retornar 401 (Unauthorized) ou 403 (Forbidden) dependendo da implementação
        assert response.status_code in [401, 403]
    
    def test_get_insight_nonexistent_restaurant(self, authenticated_client):
        """Testa insight para restaurante inexistente."""
        response = authenticated_client.get("/api/recommendations/99999/insight")
        
        assert response.status_code == 404
    
    @pytest.mark.skip(reason="Require GROQ_API_KEY - pode falhar em ambiente sem API key")
    def test_get_insight_success(self, authenticated_client, test_restaurant):
        """Testa geração de insight para restaurante existente."""
        # Este teste pode falhar se GROQ_API_KEY não estiver configurada
        response = authenticated_client.get(f"/api/recommendations/{test_restaurant.id}/insight")
        
        # Pode retornar 200 com insight ou 503/500 se API não disponível
        assert response.status_code in [200, 503, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "insight" in data
            assert isinstance(data["insight"], str)
            assert len(data["insight"]) > 0


class TestRecommendationsIntegration:
    """Testes de integração completa de recomendações."""
    
    def test_full_flow(self, client, test_db, test_restaurants):
        """Testa fluxo completo: registro -> login -> recomendações."""
        # 1. Registrar usuário
        register_response = client.post(
            "/auth/register",
            json={
                "email": "flowuser@example.com",
                "password": "password123",
                "name": "Flow User"
            }
        )
        assert register_response.status_code == 201
        token = register_response.json()["token"]
        
        # 2. Fazer login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "flowuser@example.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        assert "token" in login_response.json()
        
        # 3. Obter recomendações
        client.headers = {"Authorization": f"Bearer {token}"}
        rec_response = client.get("/api/recommendations")
        
        assert rec_response.status_code == 200
        data = rec_response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0

