"""
Serviço RAG (Retrieval-Augmented Generation) para Chef Virtual
Utiliza PGVector para armazenamento persistente de embeddings
"""

from typing import List, Optional, Set
from sqlalchemy.orm import Session
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_core.documents import Document

from app.database.models import Restaurant
from app.database import crud

# LLM será injetado via LangChain Groq


class RAGService:
    """Serviço RAG usando PGVector para persistência garantida"""
    
    def __init__(self, db: Session, connection_string: str):
        """
        Inicializa o serviço RAG
        
        Args:
            db: Sessão do banco de dados
            connection_string: String de conexão PostgreSQL para PGVector
        """
        self.db = db
        self.connection_string = connection_string
        self.embeddings = None
        self.vector_store = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Inicializa o modelo de embeddings HuggingFace"""
        # Usar modelo leve e eficiente para embeddings
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    
    def initialize_vector_store(self, collection_name: str = "tastematch_knowledge"):
        """
        Inicializa ou carrega o vector store PGVector
        
        Args:
            collection_name: Nome da coleção no PGVector
        """
        if self.vector_store is None:
            # Verificar se é PostgreSQL (não SQLite)
            if "sqlite" in self.connection_string.lower():
                raise ValueError(
                    "PGVector requer PostgreSQL. SQLite não é suportado. "
                    "Configure DATABASE_URL para usar PostgreSQL."
                )
            
            try:
                self.vector_store = PGVector(
                    connection_string=self.connection_string,
                    embedding_function=self.embeddings,
                    collection_name=collection_name,
                    pre_delete_collection=False  # Não deletar coleção existente
                )
            except Exception as e:
                # Se falhar ao criar, pode ser que a extensão vector não esteja instalada
                error_msg = str(e)
                if "vector" in error_msg.lower() or "extension" in error_msg.lower():
                    raise ValueError(
                        f"Extensão 'vector' não está instalada no PostgreSQL. "
                        f"Execute: CREATE EXTENSION IF NOT EXISTS vector; "
                        f"Erro original: {error_msg}"
                    )
                raise
    
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


def get_rag_service(db: Session, connection_string: str) -> RAGService:
    """
    Factory function para criar instância do RAGService
    
    Args:
        db: Sessão do banco de dados
        connection_string: String de conexão PostgreSQL
    
    Returns:
        Instância do RAGService
    """
    return RAGService(db, connection_string)

