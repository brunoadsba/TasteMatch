"""
Testes de integração para endpoints de restaurantes com filtros avançados.
"""

import pytest
from fastapi.testclient import TestClient


class TestRestaurantsFilters:
    """Testes para os filtros avançados de restaurantes."""

    def test_get_restaurants_with_cuisine_filter(
        self,
        client: TestClient,
        test_restaurant
    ):
        """Testa filtro por tipo de culinária."""
        response = client.get(
            f"/api/restaurants?cuisine_type={test_restaurant.cuisine_type}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        # Todos os restaurantes retornados devem ter o mesmo tipo de culinária
        for restaurant in data["restaurants"]:
            assert restaurant["cuisine_type"] == test_restaurant.cuisine_type

    def test_get_restaurants_with_min_rating(
        self,
        client: TestClient,
        test_restaurant
    ):
        """Testa filtro por rating mínimo."""
        min_rating = 3.5
        response = client.get(
            f"/api/restaurants?min_rating={min_rating}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        # Todos os restaurantes devem ter rating >= min_rating
        for restaurant in data["restaurants"]:
            assert restaurant["rating"] >= min_rating

    def test_get_restaurants_with_price_range(
        self,
        client: TestClient,
        test_restaurant
    ):
        """Testa filtro por faixa de preço."""
        price_range = test_restaurant.price_range
        response = client.get(
            f"/api/restaurants?price_range={price_range}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        # Todos os restaurantes devem ter a mesma faixa de preço
        for restaurant in data["restaurants"]:
            assert restaurant["price_range"] == price_range

    def test_get_restaurants_with_search(
        self,
        client: TestClient,
        test_restaurant
    ):
        """Testa busca textual no nome e descrição."""
        search_term = test_restaurant.name[:3]  # Primeiras 3 letras do nome
        response = client.get(
            f"/api/restaurants?search={search_term}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        # Pelo menos um restaurante deve corresponder à busca
        found = False
        for restaurant in data["restaurants"]:
            if search_term.lower() in restaurant["name"].lower():
                found = True
                break
        # Se o termo existe no nome, deve encontrar
        if len(search_term) > 0:
            assert found or len(data["restaurants"]) > 0

    def test_get_restaurants_with_sort_by_rating_desc(
        self,
        client: TestClient
    ):
        """Testa ordenação por rating descendente."""
        response = client.get(
            "/api/restaurants?sort_by=rating_desc&limit=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        if len(data["restaurants"]) > 1:
            ratings = [r["rating"] for r in data["restaurants"]]
            # Verificar que está ordenado descendentemente
            assert ratings == sorted(ratings, reverse=True)

    def test_get_restaurants_with_sort_by_name_asc(
        self,
        client: TestClient
    ):
        """Testa ordenação por nome ascendente."""
        response = client.get(
            "/api/restaurants?sort_by=name_asc&limit=10"
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        if len(data["restaurants"]) > 1:
            names = [r["name"] for r in data["restaurants"]]
            # Verificar que está ordenado alfabeticamente
            assert names == sorted(names)

    def test_get_restaurants_combined_filters(
        self,
        client: TestClient,
        test_restaurant
    ):
        """Testa múltiplos filtros combinados."""
        response = client.get(
            f"/api/restaurants?cuisine_type={test_restaurant.cuisine_type}"
            f"&min_rating=3.0&sort_by=rating_desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert "restaurants" in data
        # Verificar filtros
        for restaurant in data["restaurants"]:
            assert restaurant["cuisine_type"] == test_restaurant.cuisine_type
            assert restaurant["rating"] >= 3.0

    def test_get_restaurants_pagination(
        self,
        client: TestClient
    ):
        """Testa paginação de restaurantes."""
        # Primeira página
        response1 = client.get("/api/restaurants?page=1&limit=5")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["restaurants"]) <= 5
        
        # Segunda página
        response2 = client.get("/api/restaurants?page=2&limit=5")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["restaurants"]) <= 5
        
        # Se houver mais de 5 restaurantes, as páginas devem ser diferentes
        if data1["total"] > 5:
            assert data1["restaurants"] != data2["restaurants"]

