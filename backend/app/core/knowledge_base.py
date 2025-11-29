"""
Gerenciamento da base de conhecimento dinâmica do Chef Virtual
Combina dados estáticos (arquivo .txt) com dados dinâmicos do banco
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain_core.documents import Document

from app.database import crud
from app.core.recommender import extract_user_patterns


def load_static_knowledge(file_path: Optional[str] = None) -> str:
    """
    Carrega a base de conhecimento estática do arquivo
    
    Args:
        file_path: Caminho para o arquivo de conhecimento estático (opcional)
    
    Returns:
        Conteúdo do arquivo como string
    """
    if file_path is None:
        # Caminho relativo ao diretório do backend
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(backend_dir, "data", "base_conhecimento_tastematch.txt")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def build_restaurant_documents(db: Session, limit: Optional[int] = None) -> List[Document]:
    """
    Constrói documentos LangChain a partir dos restaurantes do banco
    
    Args:
        db: Sessão do banco de dados
        limit: Limite de restaurantes a processar (None = todos)
    
    Returns:
        Lista de documentos LangChain
    """
    restaurants = crud.get_restaurants(db, skip=0, limit=limit)
    documents = []
    
    for restaurant in restaurants:
        # Criar texto descritivo do restaurante
        content_parts = [
            f"Restaurante: {restaurant.name}",
            f"Tipo de culinária: {restaurant.cuisine_type}",
            f"Avaliação: {restaurant.rating}/5.0",
        ]
        
        if restaurant.description:
            content_parts.append(f"Descrição: {restaurant.description}")
        
        if restaurant.price_range:
            content_parts.append(f"Faixa de preço: {restaurant.price_range}")
        
        content = "\n".join(content_parts)
        
        # Criar documento com metadados
        doc = Document(
            page_content=content,
            metadata={
                "type": "restaurant",
                "restaurant_id": restaurant.id,
                "name": restaurant.name,
                "cuisine_type": restaurant.cuisine_type,
                "rating": float(restaurant.rating),
                "price_range": restaurant.price_range or "N/A"
            }
        )
        documents.append(doc)
    
    return documents


def build_user_preference_documents(
    db: Session, 
    user_id: int
) -> List[Document]:
    """
    Constrói documentos baseados nas preferências do usuário
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
    
    Returns:
        Lista de documentos LangChain com preferências
    """
    # Buscar pedidos do usuário
    orders = crud.get_user_orders(db, user_id=user_id, limit=50)
    
    if not orders:
        return []
    
    # Extrair padrões usando a lógica do recommender
    patterns = extract_user_patterns(user_id, orders, [])
    
    # Converter padrões para formato de preferências
    preferences = {
        "preferred_cuisines": patterns.get("favorite_cuisines", []),
        "preferred_price_range": None,  # Não disponível em extract_user_patterns
        "frequent_restaurants": []
    }
    
    documents = []
    
    # Documento sobre tipos de culinária preferidos
    if preferences.get("preferred_cuisines"):
        cuisines = ", ".join(preferences["preferred_cuisines"])
        doc = Document(
            page_content=f"O usuário tem preferência por culinárias: {cuisines}",
            metadata={
                "type": "user_preference",
                "user_id": user_id,
                "preference_type": "cuisine"
            }
        )
        documents.append(doc)
    
    # Documento sobre faixa de preço preferida
    if preferences.get("preferred_price_range"):
        price_range = preferences["preferred_price_range"]
        doc = Document(
            page_content=f"O usuário prefere restaurantes na faixa de preço: {price_range}",
            metadata={
                "type": "user_preference",
                "user_id": user_id,
                "preference_type": "price_range"
            }
        )
        documents.append(doc)
    
    # Documento sobre restaurantes frequentados
    if preferences.get("frequent_restaurants"):
        restaurants = preferences["frequent_restaurants"]
        restaurant_names = ", ".join([r["name"] for r in restaurants[:5]])
        doc = Document(
            page_content=f"O usuário frequentemente pede de: {restaurant_names}",
            metadata={
                "type": "user_preference",
                "user_id": user_id,
                "preference_type": "frequent_restaurants"
            }
        )
        documents.append(doc)
    
    return documents


def build_static_knowledge_documents() -> List[Document]:
    """
    Constrói documentos a partir da base de conhecimento estática
    
    Returns:
        Lista de documentos LangChain
    """
    static_content = load_static_knowledge()
    
    if not static_content:
        return []
    
    # Dividir em seções menores para melhor recuperação
    sections = static_content.split("\n## ")
    documents = []
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        
        # Primeira seção não tem "## " prefix
        if i == 0:
            title = section.split("\n")[0] if section else "Introdução"
            content = section
        else:
            lines = section.split("\n")
            title = lines[0] if lines else f"Seção {i}"
            content = "\n".join(lines[1:]) if len(lines) > 1 else section
        
        doc = Document(
            page_content=content,
            metadata={
                "type": "static_knowledge",
                "section": title,
                "source": "base_conhecimento_tastematch.txt"
            }
        )
        documents.append(doc)
    
    return documents


def build_complete_knowledge_base(
    db: Session,
    user_id: Optional[int] = None
) -> List[Document]:
    """
    Constrói a base de conhecimento completa (estática + dinâmica)
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário (opcional, para incluir preferências)
    
    Returns:
        Lista completa de documentos
    """
    documents = []
    
    # 1. Adicionar conhecimento estático
    static_docs = build_static_knowledge_documents()
    documents.extend(static_docs)
    
    # 2. Adicionar restaurantes do banco
    restaurant_docs = build_restaurant_documents(db)
    documents.extend(restaurant_docs)
    
    # 3. Adicionar preferências do usuário (se fornecido)
    if user_id:
        preference_docs = build_user_preference_documents(db, user_id)
        documents.extend(preference_docs)
    
    return documents


def update_knowledge_base(
    db: Session,
    rag_service,
    user_id: Optional[int] = None
):
    """
    Atualiza a base de conhecimento no vector store
    
    Args:
        db: Sessão do banco de dados
        rag_service: Instância do RAGService
        user_id: ID do usuário (opcional)
    """
    # Construir documentos completos
    documents = build_complete_knowledge_base(db, user_id)
    
    # Adicionar ao vector store
    if documents:
        rag_service.add_documents(documents)

