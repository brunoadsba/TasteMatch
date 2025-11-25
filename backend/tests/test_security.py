"""
Testes unitários para módulo de segurança (hash de senhas e JWT).
"""
import pytest
from datetime import timedelta

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)


class TestPasswordHashing:
    """Testes para hash de senhas."""
    
    def test_get_password_hash_returns_string(self):
        """Testa se hash de senha retorna string."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password
    
    def test_password_hash_is_deterministic_different(self):
        """Testa se o mesmo hash é diferente a cada vez (salt diferente)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Bcrypt gera hash diferente a cada vez devido ao salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Testa verificação de senha correta."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Testa verificação de senha incorreta."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Testa verificação com senha vazia."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


class TestJWT:
    """Testes para tokens JWT."""
    
    def test_create_access_token_returns_string(self):
        """Testa se criação de token retorna string."""
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_valid_token(self):
        """Testa decodificação de token válido."""
        data = {"sub": "123", "email": "test@example.com"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "123"
        assert decoded["email"] == "test@example.com"
        assert "exp" in decoded
    
    def test_decode_invalid_token(self):
        """Testa decodificação de token inválido."""
        invalid_token = "invalid.token.here"
        
        decoded = decode_access_token(invalid_token)
        
        assert decoded is None
    
    def test_decode_expired_token(self):
        """Testa decodificação de token expirado."""
        from datetime import timedelta
        data = {"sub": "123"}
        
        # Criar token com expiração negativa (já expirado)
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        
        # Aguardar um pouco para garantir que expirou
        import time
        time.sleep(0.1)
        
        decoded = decode_access_token(token)
        
        # Token expirado deve retornar None
        assert decoded is None
    
    def test_token_contains_expiration(self):
        """Testa se token contém campo de expiração."""
        data = {"sub": "123"}
        token = create_access_token(data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert "exp" in decoded
        assert isinstance(decoded["exp"], int)
    
    def test_token_with_custom_expiration(self):
        """Testa criação de token com expiração customizada."""
        data = {"sub": "123"}
        custom_expiration = timedelta(hours=2)
        token = create_access_token(data, expires_delta=custom_expiration)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert "exp" in decoded

