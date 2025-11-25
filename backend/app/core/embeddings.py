"""
Serviço de geração de embeddings usando sentence-transformers.
Otimizado para uso eficiente de memória em ambientes com recursos limitados.
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Carregar modelo globalmente (cache)
_model = None


def get_embedding_model():
    """
    Obtém ou carrega o modelo de embeddings.
    Otimizado para reduzir uso de memória em ambientes com recursos limitados.
    """
    global _model
    if _model is None:
        logger.info(f"Carregando modelo de embeddings: {settings.EMBEDDING_MODEL}")
        
        # Otimizações para reduzir uso de memória
        try:
            import torch
            # Limitar threads para reduzir uso de memória
            torch.set_num_threads(1)
            torch.set_num_interop_threads(1)
            logger.debug("PyTorch configurado com 1 thread para otimização de memória")
        except ImportError:
            pass  # PyTorch não disponível, continuar sem otimizações
        
        # Carregar modelo com otimizações
        _model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device='cpu'  # Forçar uso de CPU (mais eficiente em memória)
        )
        
        # Colocar modelo em modo de avaliação (reduz uso de memória)
        _model.eval()
        
        logger.info("Modelo de embeddings carregado com sucesso (otimizado para memória)")
    return _model


def unload_model():
    """
    Descarrega o modelo de memória (útil para scripts de seed).
    A próxima chamada a get_embedding_model() recarregará o modelo.
    """
    global _model
    if _model is not None:
        logger.info("Descarregando modelo de embeddings da memória")
        del _model
        _model = None
        
        # Limpeza adicional de memória
        try:
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass  # Ignorar erros de limpeza


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

