"""
Serviço de geração de embeddings usando sentence-transformers.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from app.config import settings

# Carregar modelo globalmente (cache)
_model = None


def get_embedding_model():
    """Obtém ou carrega o modelo de embeddings."""
    global _model
    if _model is None:
        print(f"📥 Carregando modelo de embeddings: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        print("✅ Modelo carregado!")
    return _model


def generate_restaurant_embedding(restaurant) -> np.ndarray:
    """
    Gera embedding vetorial para um restaurante.
    
    Args:
        restaurant: Objeto RestaurantCreate ou Restaurant
        
    Returns:
        np.ndarray: Embedding vetorial (384 dimensões)
    """
    model = get_embedding_model()
    
    # Construir texto para embedding
    text = f"{restaurant.name} {restaurant.cuisine_type}"
    if restaurant.description:
        text += f" {restaurant.description}"
    
    # Gerar embedding
    embedding = model.encode(text, normalize_embeddings=True)
    
    return embedding

