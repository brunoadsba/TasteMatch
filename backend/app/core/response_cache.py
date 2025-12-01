"""
Sistema de Cache de Respostas do Chef Virtual

FASE 3: Cacheia respostas para perguntas comuns, reduzindo latência
e melhorando consistência. Usa cache em memória (futuramente pode
ser migrado para Redis).

Estratégia:
- Normaliza queries (lowercase, remove pontuação)
- Cacheia respostas completas por um tempo limitado (TTL)
- Invalida cache quando base de conhecimento é atualizada
"""

import hashlib
import time
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ResponseCache:
    """
    Cache simples em memória para respostas do Chef Virtual.
    
    Estrutura:
    {
        "query_hash": {
            "response": {...},
            "timestamp": datetime,
            "ttl_seconds": int
        }
    }
    """
    
    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Inicializa o cache.
        
        Args:
            default_ttl_seconds: TTL padrão em segundos (1 hora por padrão)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds
        self._hits = 0
        self._misses = 0
    
    def _normalize_query(self, query: str) -> str:
        """
        Normaliza query para criar chave consistente.
        
        Args:
            query: Query original
        
        Returns:
            Query normalizada (lowercase, sem pontuação extra)
        """
        # Converter para lowercase e remover espaços extras
        normalized = query.lower().strip()
        
        # Remover pontuação desnecessária (manter apenas espaços e letras)
        import re
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remover espaços múltiplos
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _generate_key(self, query: str, user_id: Optional[int] = None) -> str:
        """
        Gera chave única para o cache baseada na query e user_id.
        
        Args:
            query: Query do usuário
            user_id: ID do usuário (opcional, para cache personalizado)
        
        Returns:
            Hash MD5 da query normalizada + user_id
        """
        normalized = self._normalize_query(query)
        
        # Incluir user_id se fornecido (permite cache personalizado)
        if user_id:
            key_string = f"{normalized}::user_{user_id}"
        else:
            key_string = normalized
        
        # Gerar hash MD5
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(
        self,
        query: str,
        user_id: Optional[int] = None,
        ttl_seconds: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca resposta no cache.
        
        Args:
            query: Query do usuário
            user_id: ID do usuário (opcional)
            ttl_seconds: TTL customizado (opcional, usa default se None)
        
        Returns:
            Resposta cacheada se válida, None caso contrário
        """
        key = self._generate_key(query, user_id)
        
        if key not in self._cache:
            self._misses += 1
            logger.debug(f"Cache MISS para query: '{query[:50]}...'")
            return None
        
        cached_item = self._cache[key]
        ttl = ttl_seconds or cached_item.get('ttl_seconds', self.default_ttl)
        timestamp = cached_item.get('timestamp')
        
        # Verificar se cache expirou
        if timestamp:
            age_seconds = (datetime.now() - timestamp).total_seconds()
            if age_seconds > ttl:
                # Cache expirado, remover
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache EXPIRADO para query: '{query[:50]}...'")
                return None
        
        # Cache hit válido
        self._hits += 1
        logger.debug(f"Cache HIT para query: '{query[:50]}...'")
        return cached_item.get('response')
    
    def set(
        self,
        query: str,
        response: Dict[str, Any],
        user_id: Optional[int] = None,
        ttl_seconds: Optional[int] = None
    ):
        """
        Armazena resposta no cache.
        
        Args:
            query: Query do usuário
            response: Resposta a cachear
            user_id: ID do usuário (opcional)
            ttl_seconds: TTL customizado (opcional, usa default se None)
        """
        key = self._generate_key(query, user_id)
        ttl = ttl_seconds or self.default_ttl
        
        self._cache[key] = {
            'response': response,
            'timestamp': datetime.now(),
            'ttl_seconds': ttl
        }
        
        logger.debug(f"Cache SET para query: '{query[:50]}...' (TTL: {ttl}s)")
    
    def invalidate(self, query: Optional[str] = None, user_id: Optional[int] = None):
        """
        Invalida cache para uma query específica ou limpa todo o cache.
        
        Args:
            query: Query específica a invalidar (None = limpa tudo)
            user_id: ID do usuário (opcional)
        """
        if query is None:
            # Limpar todo o cache
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cache LIMPO completamente ({count} itens removidos)")
        else:
            # Invalidar query específica
            key = self._generate_key(query, user_id)
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache INVALIDADO para query: '{query[:50]}...'")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas (hits, misses, size, hit_rate)
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'total': total,
            'hit_rate': round(hit_rate, 2),
            'size': len(self._cache),
            'default_ttl': self.default_ttl
        }
    
    def cleanup_expired(self):
        """
        Remove itens expirados do cache.
        Útil para limpeza periódica (pode ser chamado em background).
        """
        now = datetime.now()
        expired_keys = []
        
        for key, item in self._cache.items():
            timestamp = item.get('timestamp')
            ttl = item.get('ttl_seconds', self.default_ttl)
            
            if timestamp:
                age_seconds = (now - timestamp).total_seconds()
                if age_seconds > ttl:
                    expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cache LIMPO: {len(expired_keys)} itens expirados removidos")


# Instância global do cache (singleton)
_global_cache: Optional[ResponseCache] = None


def get_response_cache() -> ResponseCache:
    """
    Retorna instância global do cache (singleton).
    
    Returns:
        Instância do ResponseCache
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = ResponseCache(default_ttl_seconds=3600)  # 1 hora por padrão
        logger.info("ResponseCache inicializado (TTL padrão: 1 hora)")
    
    return _global_cache


def should_cache_query(query: str) -> bool:
    """
    Decide se uma query deve ser cacheada.
    
    Critérios:
    - Query não muito longa (< 200 caracteres)
    - Query não contém informações muito específicas/temporais
    - Query é sobre comida/restaurantes (não sobre usuário específico)
    
    Args:
        query: Query a avaliar
    
    Returns:
        True se deve cachear, False caso contrário
    """
    if not query or len(query.strip()) < 3:
        return False
    
    # Não cachear queries muito longas (provavelmente perguntas complexas)
    if len(query) > 200:
        return False
    
    # Não cachear queries com informações temporais específicas
    temporal_keywords = ['hoje', 'agora', 'amanhã', 'semana', 'mês', 'ano']
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in temporal_keywords):
        return False
    
    # Não cachear queries muito pessoais
    personal_keywords = ['meu', 'minha', 'meus', 'minhas', 'eu quero', 'eu gosto']
    if any(keyword in query_lower for keyword in personal_keywords):
        # Mas permitir cache se for pergunta genérica sobre comida
        if any(food_keyword in query_lower for food_keyword in ['churrasco', 'pizza', 'sushi', 'hambúrguer', 'restaurante']):
            return True
        return False
    
    return True

