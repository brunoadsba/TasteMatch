"""
Serviço RAG (Retrieval-Augmented Generation) para Chef Virtual
Utiliza PGVector para armazenamento persistente de embeddings
"""

from typing import List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document
import logging
import threading

from app.database.models import Restaurant
from app.database import crud

# LLM será injetado via LangChain Groq

logger = logging.getLogger(__name__)

# OTIMIZAÇÃO MEMÓRIA: Singleton para modelo de embeddings
# Compartilha a mesma instância entre todas as requisições, evitando carregar múltiplas vezes
_shared_embeddings = None
_embeddings_lock = threading.Lock()

def get_shared_embeddings():
    """
    Retorna instância compartilhada do modelo de embeddings (singleton).
    Reduz uso de memória evitando carregar o modelo múltiplas vezes.
    
    Returns:
        HuggingFaceEmbeddings: Instância compartilhada do modelo
    """
    global _shared_embeddings
    
    if _shared_embeddings is None:
        with _embeddings_lock:
            # Double-check locking pattern
            if _shared_embeddings is None:
                model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                _shared_embeddings = HuggingFaceEmbeddings(
                    model_name=model_name,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info("Modelo de embeddings carregado (singleton)")
    
    return _shared_embeddings


def validate_database_requirements(connection_string: str, db: Session) -> dict:
    """
    Valida requisitos do banco de dados para RAG Service.
    
    Verifica:
    - Se é PostgreSQL (não SQLite)
    - Se extensão 'vector' está instalada
    - Se conexão está funcionando
    
    Args:
        connection_string: String de conexão PostgreSQL
        db: Sessão do banco de dados
        
    Returns:
        dict: Resultado da validação com status e mensagens
        
    Raises:
        ValueError: Se algum requisito não for atendido
    """
    errors = []
    warnings = []
    
    # 1. Verificar se é PostgreSQL
    if "sqlite" in connection_string.lower():
        errors.append(
            "PGVector requer PostgreSQL. SQLite não é suportado. "
            "Configure DATABASE_URL para usar PostgreSQL."
        )
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # 2. Verificar conexão ao banco
    try:
        # Testar conexão básica
        result = db.execute(text("SELECT version()"))
        db_version = result.fetchone()[0]
        logger.info(f"Conectado ao PostgreSQL: {db_version[:50]}...")
    except Exception as e:
        errors.append(
            f"Não foi possível conectar ao banco de dados: {str(e)}. "
            "Verifique se DATABASE_URL está correto e se o banco está acessível."
        )
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    # 3. Verificar extensão vector
    try:
        result = db.execute(
            text("SELECT * FROM pg_extension WHERE extname = 'vector'")
        )
        vector_ext = result.fetchone()
        
        if vector_ext is None:
            errors.append(
                "Extensão 'vector' (pgvector) não está instalada no PostgreSQL. "
                "Execute no banco: CREATE EXTENSION IF NOT EXISTS vector;"
            )
        else:
            ext_version = vector_ext[5] if len(vector_ext) > 5 else "desconhecida"
            logger.info(f"Extensão pgvector encontrada: versão {ext_version}")
            
    except Exception as e:
        errors.append(
            f"Erro ao verificar extensão 'vector': {str(e)}. "
            "Certifique-se de que está conectado a um banco PostgreSQL válido."
        )
    
    # 4. Verificar se está usando Supabase (detectar automaticamente)
    is_supabase = "supabase" in connection_string.lower() or "pooler.supabase.com" in connection_string.lower()
    if is_supabase:
        logger.info("Detectado banco Supabase - verificando configurações...")
        
        # Verificar SSL (Supabase requer SSL)
        if "sslmode" not in connection_string.lower():
            warnings.append(
                "Supabase requer SSL. Adicione '?sslmode=require' à DATABASE_URL ou "
                "configure DB_PROVIDER=supabase para configurar SSL automaticamente."
            )
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "is_supabase": is_supabase
    }


class RAGService:
    """Serviço RAG usando PGVector para persistência garantida"""
    
    def __init__(self, db: Session, connection_string: str, validate: bool = True, initialize_vector_store: bool = False):
        """
        Inicializa o serviço RAG
        
        Args:
            db: Sessão do banco de dados
            connection_string: String de conexão PostgreSQL para PGVector
            validate: Se True, valida requisitos do banco antes de inicializar
            initialize_vector_store: Se True, inicializa vector_store imediatamente (eager).
                                    Se False, inicializa apenas quando necessário (lazy, padrão).
        """
        self.db = db
        self.connection_string = connection_string
        self.embeddings = None
        self.vector_store = None
        
        # Validar requisitos do banco se solicitado
        if validate:
            validation = validate_database_requirements(connection_string, db)
            
            if not validation["valid"]:
                error_msg = "Requisitos do banco de dados não atendidos:\n"
                error_msg += "\n".join(f"  - {err}" for err in validation["errors"])
                if validation["warnings"]:
                    error_msg += "\n\nAvisos:\n"
                    error_msg += "\n".join(f"  - {warn}" for warn in validation["warnings"])
                
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            if validation.get("warnings"):
                for warning in validation["warnings"]:
                    logger.warning(warning)
        
        self._initialize_embeddings()
        
        # Inicializar vector_store imediatamente se solicitado (eager initialization)
        if initialize_vector_store:
            self.initialize_vector_store()
            logger.info("RAG Service inicializado com vector_store ativo (eager mode)")
    
    def _initialize_embeddings(self):
        """
        Inicializa o modelo de embeddings HuggingFace usando singleton.
        
        OTIMIZAÇÃO MEMÓRIA: Usa instância compartilhada do modelo para evitar
        carregar múltiplas vezes na memória (reduz ~200-300MB por worker).
        """
        # Usar instância compartilhada (singleton) do modelo de embeddings
        self.embeddings = get_shared_embeddings()
    
    def initialize_vector_store(self, collection_name: str = "tastematch_knowledge"):
        """
        Inicializa ou carrega o vector store PGVector
        
        Args:
            collection_name: Nome da coleção no PGVector
        """
        if self.vector_store is None:
            try:
                logger.info(f"Inicializando PGVector com collection: {collection_name}")
                self.vector_store = PGVector(
                    connection_string=self.connection_string,
                    embedding_function=self.embeddings,
                    collection_name=collection_name,
                    pre_delete_collection=False  # Não deletar coleção existente
                )
                logger.info("PGVector inicializado com sucesso")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Erro ao inicializar PGVector: {error_msg}", exc_info=True)
                
                # Mensagens de erro mais específicas
                if "vector" in error_msg.lower() or "extension" in error_msg.lower():
                    raise ValueError(
                        f"Extensão 'vector' (pgvector) não está instalada ou habilitada no PostgreSQL. "
                        f"Execute no banco: CREATE EXTENSION IF NOT EXISTS vector; "
                        f"Erro original: {error_msg}"
                    )
                elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    raise ValueError(
                        f"Erro de conexão ao banco de dados: {error_msg}. "
                        f"Verifique se DATABASE_URL está correto e se o banco está acessível."
                    )
                elif "authentication" in error_msg.lower() or "password" in error_msg.lower():
                    raise ValueError(
                        f"Erro de autenticação: {error_msg}. "
                        f"Verifique se as credenciais em DATABASE_URL estão corretas."
                    )
                else:
                    raise ValueError(
                        f"Erro ao inicializar PGVector: {error_msg}. "
                        f"Verifique se o banco está configurado corretamente."
                    )
    
    def add_documents(self, documents: List[Document]):
        """
        Adiciona documentos ao vector store
        
        Args:
            documents: Lista de documentos LangChain
        """
        if self.vector_store is None:
            self.initialize_vector_store()
        
        self.vector_store.add_documents(documents)
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 4,
        filter: Optional[dict] = None
    ) -> List[Document]:
        """
        Busca semântica por similaridade
        
        Args:
            query: Texto da consulta
            k: Número de resultados
            filter: Filtros opcionais (ex: {"metadata": {"type": "restaurant"}})
        
        Returns:
            Lista de documentos relevantes
        """
        if self.vector_store is None:
            self.initialize_vector_store()
        
        if filter:
            return self.vector_store.similarity_search(
                query, k=k, filter=filter
            )
        return self.vector_store.similarity_search(query, k=k)
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None
    ) -> List[tuple]:
        """
        Busca semântica com scores de similaridade
        
        Returns:
            Lista de tuplas (Document, score)
        """
        if self.vector_store is None:
            self.initialize_vector_store()
        
        if filter:
            return self.vector_store.similarity_search_with_score(
                query, k=k, filter=filter
            )
        return self.vector_store.similarity_search_with_score(query, k=k)
    
    def get_retriever(self, k: int = 4, search_type: str = "similarity"):
        """
        Retorna um retriever LangChain configurado
        
        Args:
            k: Número de documentos a recuperar
            search_type: Tipo de busca ("similarity" ou "mmr")
        
        Returns:
            Retriever LangChain
        """
        if self.vector_store is None:
            self.initialize_vector_store()
        
        return self.vector_store.as_retriever(
            search_kwargs={"k": k},
            search_type=search_type
        )
    
    def has_documents(self) -> bool:
        """
        Verifica se há documentos no vector store
        
        Returns:
            True se há documentos, False caso contrário
        """
        if self.vector_store is None:
            self.initialize_vector_store()
        
        try:
            # Tentar buscar 1 documento para verificar se há conteúdo
            results = self.vector_store.similarity_search("test", k=1)
            return len(results) > 0
        except Exception:
            # Se falhar, assumir que não há documentos
            return False
    
    def _exact_search_restaurants(
        self,
        query: str,
        k: int = 4
    ) -> List[Document]:
        """
        Busca exata de restaurantes usando SQL LIKE/ILIKE
        
        Args:
            query: Texto da consulta
            k: Número máximo de resultados
        
        Returns:
            Lista de documentos de restaurantes encontrados por busca exata
        """
        # Palavras comuns a ignorar (stopwords)
        stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
            'em', 'no', 'na', 'nos', 'nas', 'para', 'com', 'por', 'sobre',
            'que', 'qual', 'quais', 'me', 'você', 'vocês', 'meu', 'minha',
            'meus', 'minhas', 'seu', 'sua', 'seus', 'suas', 'nosso', 'nossa',
            'tem', 'têm', 'são', 'é', 'está', 'estão', 'foi', 'foram',
            'restaurante', 'restaurantes', 'disponíveis', 'mostre', 'mostrar',
            'recomende', 'recomendar', 'sugira', 'sugerir', 'quero', 'queria'
        }
        
        # Extrair possíveis nomes de restaurantes da query
        query_lower = query.lower()
        # Remover pontuação e dividir em palavras
        import re
        words = [w.strip() for w in re.split(r'[\s,\.!?;:]+', query_lower) 
                 if w.strip() and w.strip() not in stopwords and len(w.strip()) >= 3]
        
        if not words:
            return []
        
        documents = []
        seen_ids: Set[int] = set()
        
        # Buscar por nome exato primeiro (maior prioridade)
        # Tentar busca completa primeiro, depois palavras individuais
        full_query_restaurants = crud.get_restaurants(
            db=self.db,
            skip=0,
            limit=k,
            search=query  # Buscar pela query completa
        )
        
        for restaurant in full_query_restaurants:
            if restaurant.id not in seen_ids:
                seen_ids.add(restaurant.id)
                doc = self._create_restaurant_document(restaurant, search_type="exact")
                documents.append(doc)
                if len(documents) >= k:
                    break
        
        # Se não encontrou o suficiente, buscar por palavras individuais
        if len(documents) < k:
            for word in words:
                if len(documents) >= k:
                    break
                
                restaurants = crud.get_restaurants(
                    db=self.db,
                    skip=0,
                    limit=k * 2,
                    search=word
                )
                
                for restaurant in restaurants:
                    if restaurant.id in seen_ids:
                        continue
                    seen_ids.add(restaurant.id)
                    doc = self._create_restaurant_document(restaurant, search_type="exact")
                    documents.append(doc)
                    if len(documents) >= k:
                        break
        
        return documents[:k]
    
    def _create_restaurant_document(
        self,
        restaurant: Restaurant,
        search_type: str = "semantic"
    ) -> Document:
        """
        Cria um documento LangChain a partir de um restaurante
        
        Args:
            restaurant: Objeto Restaurant
            search_type: Tipo de busca ("exact" ou "semantic")
        
        Returns:
            Document LangChain
        """
        content_parts = [
            f"Restaurante: {restaurant.name}",
            f"Tipo de culinária: {restaurant.cuisine_type}",
            f"Avaliação: {restaurant.rating}/5.0",
        ]
        
        if restaurant.description:
            content_parts.append(f"Descrição: {restaurant.description}")
        
        if restaurant.price_range:
            content_parts.append(f"Faixa de preço: {restaurant.price_range}")
        
        return Document(
            page_content="\n".join(content_parts),
            metadata={
                "type": "restaurant",
                "restaurant_id": restaurant.id,
                "name": restaurant.name,
                "cuisine_type": restaurant.cuisine_type,
                "rating": float(restaurant.rating),
                "price_range": restaurant.price_range or "N/A",
                "search_type": search_type
            }
        )
    
    def hybrid_search(
        self,
        query: str,
        k: int = 4,
        exact_weight: float = 0.6,
        semantic_weight: float = 0.4
    ) -> List[Document]:
        """
        Busca híbrida: combina busca exata (SQL) + busca semântica (PGVector)
        
        Estratégia:
        1. Busca exata tem prioridade (para nomes exatos como "McDonald's")
        2. Busca semântica complementa (para intenções como "algo apimentado")
        3. Remove duplicatas (prioriza busca exata)
        
        Args:
            query: Texto da consulta
            k: Número total de resultados desejados
            exact_weight: Peso da busca exata (0.0 a 1.0)
            semantic_weight: Peso da busca semântica (0.0 a 1.0)
        
        Returns:
            Lista de documentos combinados (exatos primeiro, depois semânticos)
        """
        # Calcular quantos resultados buscar de cada tipo
        k_exact = max(1, int(k * exact_weight))
        k_semantic = max(1, int(k * semantic_weight))
        
        # 1. Busca exata (prioridade)
        exact_docs = self._exact_search_restaurants(query, k=k_exact)
        
        # 2. Busca semântica (complemento)
        semantic_docs = self.similarity_search(query, k=k_semantic * 2)  # Buscar mais para ter opções
        
        # 3. Combinar resultados (exatos primeiro, depois semânticos)
        combined_docs = []
        seen_ids: Set[int] = set()
        
        # Adicionar documentos exatos primeiro (prioridade)
        for doc in exact_docs:
            restaurant_id = doc.metadata.get("restaurant_id")
            if restaurant_id and restaurant_id not in seen_ids:
                combined_docs.append(doc)
                seen_ids.add(restaurant_id)
        
        # Adicionar documentos semânticos (sem duplicatas)
        for doc in semantic_docs:
            restaurant_id = doc.metadata.get("restaurant_id")
            doc_id = restaurant_id if restaurant_id else id(doc)  # Usar ID do restaurante ou ID do objeto
            
            if doc_id not in seen_ids:
                # Marcar como busca semântica se não for exata
                if doc.metadata.get("search_type") != "exact":
                    doc.metadata["search_type"] = "semantic"
                combined_docs.append(doc)
                seen_ids.add(doc_id)
            
            if len(combined_docs) >= k:
                break
        
        return combined_docs[:k]


def get_rag_service(db: Session, connection_string: str, eager: bool = False) -> RAGService:
    """
    Factory function para criar instância do RAGService
    
    Args:
        db: Sessão do banco de dados (cada requisição tem sua própria sessão)
        connection_string: String de conexão PostgreSQL
        eager: Se True, inicializa vector_store imediatamente (sempre ativo).
               Se False, inicializa apenas quando necessário (lazy, padrão).
    
    Returns:
        Instância do RAGService
        
    Nota:
        Cada requisição cria nova instância (não compartilhamos db entre requisições).
        Mas se eager=True, o vector_store é inicializado imediatamente, tornando
        a primeira busca mais rápida e detectando erros cedo.
    """
    # Criar nova instância (cada requisição tem sua própria sessão db)
    rag_service = RAGService(
        db=db,
        connection_string=connection_string,
        validate=True,
        initialize_vector_store=eager
    )
    
    if eager:
        logger.debug("RAG Service criado com vector_store inicializado (eager mode)")
    
    return rag_service

