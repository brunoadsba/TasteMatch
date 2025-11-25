"""
Testes unitários para módulo de embeddings.
"""
import pytest
import numpy as np

from app.core.embeddings import (
    get_embedding_model,
    generate_restaurant_embedding
)
from app.database.models import Restaurant


class TestEmbeddingModel:
    """Testes para carregamento do modelo de embeddings."""
    
    def test_get_embedding_model_returns_model(self):
        """Testa se get_embedding_model retorna um modelo."""
        model = get_embedding_model()
        
        assert model is not None
    
    def test_model_is_cached(self):
        """Testa se o modelo é carregado em cache (mesma instância)."""
        model1 = get_embedding_model()
        model2 = get_embedding_model()
        
        # Deve retornar a mesma instância (cache)
        assert model1 is model2


class TestRestaurantEmbedding:
    """Testes para geração de embeddings de restaurantes."""
    
    def test_generate_restaurant_embedding_from_dict(self):
        """Testa geração de embedding a partir de dicionário."""
        # Criar objeto simples que funciona como dict
        from types import SimpleNamespace
        restaurant_data = SimpleNamespace(
            name="Test Restaurant",
            cuisine_type="Italian",
            description="A great Italian restaurant"
        )
        
        embedding = generate_restaurant_embedding(restaurant_data)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == 384  # Dimensão do modelo all-MiniLM-L6-v2
        assert embedding.dtype == np.float32 or embedding.dtype == np.float64
    
    def test_generate_restaurant_embedding_from_object(self):
        """Testa geração de embedding a partir de objeto Restaurant."""
        restaurant = Restaurant(
            name="Test Restaurant",
            cuisine_type="Italian",
            description="A great Italian restaurant"
        )
        
        embedding = generate_restaurant_embedding(restaurant)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == 384
    
    def test_embedding_normalized(self):
        """Testa se embedding está normalizado (norma próxima de 1)."""
        from types import SimpleNamespace
        restaurant_data = SimpleNamespace(
            name="Test Restaurant",
            cuisine_type="Italian",
            description=None
        )
        
        embedding = generate_restaurant_embedding(restaurant_data)
        
        # Embedding normalizado deve ter norma próxima de 1
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.1  # Tolerância para normalização
    
    def test_embedding_without_description(self):
        """Testa geração de embedding sem descrição."""
        from types import SimpleNamespace
        restaurant_data = SimpleNamespace(
            name="Test Restaurant",
            cuisine_type="Italian",
            description=None
        )
        
        embedding = generate_restaurant_embedding(restaurant_data)
        
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape[0] == 384
    
    def test_different_restaurants_different_embeddings(self):
        """Testa se restaurantes diferentes geram embeddings diferentes."""
        from types import SimpleNamespace
        restaurant1 = SimpleNamespace(
            name="Italian Restaurant",
            cuisine_type="Italian",
            description="Great pasta"
        )
        restaurant2 = SimpleNamespace(
            name="Sushi Bar",
            cuisine_type="Japanese",
            description="Fresh sushi"
        )
        
        embedding1 = generate_restaurant_embedding(restaurant1)
        embedding2 = generate_restaurant_embedding(restaurant2)
        
        # Embeddings devem ser diferentes
        assert not np.array_equal(embedding1, embedding2)
        
        # Similaridade deve ser menor que 1
        similarity = np.dot(embedding1, embedding2)
        assert similarity < 1.0

