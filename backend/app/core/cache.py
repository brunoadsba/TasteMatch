"""
Cache em memória thread-safe com política LRU (Least Recently Used).
Evita crescimento infinito e OOM na aplicação.
"""

from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Optional, Tuple
from threading import Lock
from sqlalchemy.orm import Session


class SafeMemoryCache:
    """
    Cache em memória com política LRU (Least Recently Used) e Thread-Safety.
    
    Características:
    - Limite rígido de itens (evita crescimento infinito)
    - TTL (Time To Live) por item
    - Thread-safe (usa Lock para segurança em ambiente multi-thread)
    - LRU: remove automaticamente itens menos usados quando atinge o limite
    
    Args:
        max_items: Número máximo de itens no cache (padrão: 50)
        default_ttl_minutes: TTL padrão em minutos (padrão: 60)
    """
    
    def __init__(self, max_items: int = 50, default_ttl_minutes: int = 60):
        self._cache: OrderedDict[str, Tuple[Any, datetime]] = OrderedDict()
        self._max_items = max_items
        self._default_ttl = default_ttl_minutes
        self._lock = Lock()  # Garante segurança em ambiente com múltiplos threads/workers

    def get(self, key: str) -> Optional[Any]:
        """
        Obtém um item do cache.
        
        Args:
            key: Chave do item
            
        Returns:
            Valor do item ou None se não existir ou estiver expirado
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            data, expiry = self._cache[key]
            
            # Verificar validade (TTL)
            if datetime.now() > expiry:
                del self._cache[key]
                return None
            
            # Move para o fim (marca como usado recentemente - LRU)
            self._cache.move_to_end(key)
            return data

    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None) -> None:
        """
        Adiciona ou atualiza um item no cache.
        
        Args:
            key: Chave do item
            value: Valor a ser armazenado
            ttl_minutes: TTL em minutos (None usa o padrão)
        """
        with self._lock:
            # Limpeza preventiva se atingir limite
            if len(self._cache) >= self._max_items and key not in self._cache:
                # Remove o item mais antigo (primeiro inserido/menos usado)
                self._cache.popitem(last=False)
            
            ttl = ttl_minutes if ttl_minutes is not None else self._default_ttl
            expiry = datetime.now() + timedelta(minutes=ttl)
            
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)

    def clear(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Retorna o número de itens no cache."""
        with self._lock:
            return len(self._cache)


# Instância global do cache
# Limite de 50 chunks de metadados para garantir baixo footprint de memória
metadata_cache = SafeMemoryCache(max_items=50, default_ttl_minutes=60)


def get_cached_restaurants_metadata(db: Session, ttl_minutes: int = 60) -> list:
    """
    Retorna metadados de restaurantes com cache.
    
    OTIMIZAÇÃO: Cache de metadados reduz drasticamente queries ao banco.
    - Primeira chamada: busca do banco e armazena no cache
    - Chamadas subsequentes: retorna do cache (muito mais rápido)
    - TTL padrão: 60 minutos (ajustável)
    
    Args:
        db: Sessão do banco de dados
        ttl_minutes: TTL do cache em minutos (padrão: 60)
        
    Returns:
        Lista de dicionários com metadados dos restaurantes
    """
    cache_key = "all_restaurants_metadata"
    
    # 1. Tenta pegar do cache
    cached_data = metadata_cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 2. Se não existir, carrega do banco (importação local para evitar ciclo)
    from app.database.crud import get_restaurants_metadata
    data = get_restaurants_metadata(db, limit=None)
    
    # 3. Salva no cache
    metadata_cache.set(cache_key, data, ttl_minutes=ttl_minutes)
    
    return data

