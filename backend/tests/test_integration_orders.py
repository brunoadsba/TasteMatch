"""
Testes de integração para endpoints de pedidos.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone


class TestOrdersEndpoint:
    """Testes para o endpoint de listagem de pedidos."""

    def test_get_orders_requires_auth(self, client: TestClient):
        """Testa que o endpoint de pedidos requer autenticação."""
        response = client.get("/api/orders")
        assert response.status_code == 403

    def test_get_orders_empty_list(self, client: TestClient, auth_token: str):
        """Testa listagem de pedidos quando usuário não tem pedidos."""
        response = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert "total" in data
        assert "count" in data
        assert data["orders"] == []
        assert data["total"] == 0
        assert data["count"] == 0

    def test_get_orders_with_existing_orders(
        self,
        client: TestClient,
        auth_token: str,
        test_order
    ):
        """Testa listagem de pedidos com pedidos existentes."""
        response = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert len(data["orders"]) > 0
        assert data["total"] > 0
        assert data["count"] > 0
        
        # Verificar estrutura do pedido
        order = data["orders"][0]
        assert "id" in order
        assert "restaurant_id" in order
        assert "restaurant_name" in order
        assert "order_date" in order
        assert "total_amount" in order

    def test_get_orders_with_limit(
        self,
        client: TestClient,
        auth_token: str,
        test_order
    ):
        """Testa listagem de pedidos com limite."""
        response = client.get(
            "/api/orders?limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) <= 5

    def test_create_order_requires_auth(self, client: TestClient):
        """Testa que criação de pedido requer autenticação."""
        response = client.post(
            "/api/orders",
            json={
                "restaurant_id": 1,
                "order_date": datetime.now(timezone.utc).isoformat(),
                "total_amount": 50.0,
            }
        )
        assert response.status_code == 403

    def test_create_order_success(
        self,
        client: TestClient,
        auth_token: str,
        test_restaurant
    ):
        """Testa criação de pedido com sucesso."""
        response = client.post(
            "/api/orders",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "restaurant_id": test_restaurant.id,
                "order_date": datetime.now(timezone.utc).isoformat(),
                "total_amount": 75.50,
                "items": [{"name": "Pizza", "quantity": 2}],
                "rating": 5
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["restaurant_id"] == test_restaurant.id
        assert float(data["total_amount"]) == 75.50
        assert data["rating"] == 5
        # Items é retornado como lista (deserializado do JSON)
        assert isinstance(data["items"], list)

    def test_create_order_nonexistent_restaurant(
        self,
        client: TestClient,
        auth_token: str
    ):
        """Testa criação de pedido com restaurante inexistente."""
        response = client.post(
            "/api/orders",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "restaurant_id": 99999,
                "order_date": datetime.now(timezone.utc).isoformat(),
                "total_amount": 50.0,
            }
        )
        assert response.status_code == 400

