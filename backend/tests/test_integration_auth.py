"""
Testes de integração para endpoints de autenticação.
"""
import pytest


class TestAuthEndpoints:
    """Testes para endpoints /auth/register e /auth/login."""
    
    def test_register_new_user(self, client):
        """Testa registro de novo usuário."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert "id" in data["user"]
    
    def test_register_duplicate_email(self, client, test_user):
        """Testa registro com email duplicado."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "name": "Duplicate User"
            }
        )
        
        assert response.status_code == 400
        assert "email" in response.json()["detail"].lower() or "já" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Testa registro com email inválido."""
        response = client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "password": "password123",
                "full_name": "User"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self, client):
        """Testa registro com senha muito curta."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "123",  # Senha muito curta
                "full_name": "User"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_login_success(self, client, test_user):
        """Testa login bem-sucedido."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
    
    def test_login_wrong_password(self, client, test_user):
        """Testa login com senha incorreta."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        detail = response.json()["detail"].lower()
        assert "credenciais" in detail or "incorrect" in detail or "email" in detail or "senha" in detail
    
    def test_login_nonexistent_user(self, client):
        """Testa login com usuário inexistente."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        detail = response.json()["detail"].lower()
        assert "credenciais" in detail or "incorrect" in detail or "email" in detail or "senha" in detail
    
    def test_login_invalid_format(self, client):
        """Testa login com formato inválido."""
        response = client.post(
            "/auth/login",
            json={
                "email": "invalid-email",  # Email inválido
                "password": "password123"
            }
        )
        
        # Pode retornar 422 (validação) ou 401 (tentativa de autenticação falhou)
        assert response.status_code in [422, 401]


class TestProtectedEndpoints:
    """Testes para endpoints protegidos que requerem autenticação."""
    
    def test_get_user_me_requires_auth(self, client):
        """Testa que /api/users/me requer autenticação."""
        response = client.get("/api/users/me")
        
        # Pode retornar 401 (Unauthorized) ou 403 (Forbidden) dependendo da implementação
        assert response.status_code in [401, 403]
    
    def test_get_user_me_with_token(self, authenticated_client, test_user):
        """Testa obter informações do usuário autenticado."""
        response = authenticated_client.get("/api/users/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id
        assert "name" in data
    
    def test_get_user_preferences_requires_auth(self, client):
        """Testa que /api/users/me/preferences requer autenticação."""
        response = client.get("/api/users/me/preferences")
        
        # Pode retornar 401 (Unauthorized) ou 403 (Forbidden) dependendo da implementação
        assert response.status_code in [401, 403]
    
    def test_get_user_preferences_with_token(self, authenticated_client):
        """Testa obter preferências do usuário autenticado."""
        response = authenticated_client.get("/api/users/me/preferences")
        
        assert response.status_code == 200
        data = response.json()
        # Preferências podem estar vazias para novo usuário
        assert isinstance(data, dict)
    
    def test_invalid_token(self, client):
        """Testa requisição com token inválido."""
        client.headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/users/me")
        
        assert response.status_code == 401
    
    def test_expired_token(self, client):
        """Testa requisição com token expirado."""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        # Criar token expirado
        token = create_access_token(
            {"sub": str(1)},
            expires_delta=timedelta(seconds=-1)
        )
        
        client.headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/users/me")
        
        assert response.status_code == 401

