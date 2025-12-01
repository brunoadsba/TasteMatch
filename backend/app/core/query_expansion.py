"""
Módulo de Expansão de Query com Sinônimos

FASE 2: Implementa expansão de query antes da busca RAG para melhorar
recuperação de documentos relevantes usando sinônimos e termos relacionados.

Exemplo:
    "churrasco" → "churrasco OR carne grelhada OR rodízio OR picanha OR brasileira"
"""

from typing import List, Set
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Mapa de Sinônimos e Termos Relacionados
# Chave: termo original | Valor: lista de sinônimos/termos relacionados
SYNONYM_MAP = {
    # Churrasco e Carnes
    "churrasco": ["carne grelhada", "rodízio", "picanha", "churrascaria", "brasileira", "carne na brasa", "espetinho"],
    "churrascaria": ["churrasco", "rodízio", "carne grelhada", "picanha", "brasileira"],
    "rodízio": ["churrasco", "churrascaria", "carne grelhada", "brasileira"],
    "picanha": ["churrasco", "carne grelhada", "brasileira", "rodízio"],
    "carne grelhada": ["churrasco", "picanha", "rodízio", "brasileira", "espetinho"],
    
    # Sushi e Japonesa
    "sushi": ["japonesa", "sashimi", "peixe cru", "temaki", "oriental", "japonês"],
    "sashimi": ["sushi", "japonesa", "peixe cru", "oriental"],
    "japonesa": ["sushi", "sashimi", "temaki", "oriental", "japonês"],
    "japonês": ["japonesa", "sushi", "sashimi", "oriental"],
    
    # Massas e Italiana
    "massa": ["italiana", "macarrão", "pizza", "lasanha", "risoto"],
    "pizza": ["italiana", "massa", "cantina"],
    "italiana": ["massa", "pizza", "macarrão", "lasanha", "risoto", "cantina"],
    "macarrão": ["massa", "italiana", "pasta"],
    
    # Hambúrguer e Fast Food
    "hambúrguer": ["burger", "hamburgueria", "fast food", "lanche", "sanduíche"],
    "burger": ["hambúrguer", "hamburgueria", "fast food", "lanche"],
    "hamburgueria": ["hambúrguer", "burger", "fast food", "lanche"],
    "fast food": ["hambúrguer", "burger", "hamburgueria", "lanche"],
    
    # Árabe
    "árabe": ["esfiha", "quibe", "kibe", "shawarma", "kebab", "libanesa", "síria"],
    "esfiha": ["árabe", "quibe", "kibe", "libanesa"],
    "shawarma": ["árabe", "kebab", "libanesa"],
    "kebab": ["árabe", "shawarma", "libanesa"],
    
    # Vegetariana/Vegana
    "vegetariana": ["vegano", "sem carne", "plantas", "salada", "orgânico"],
    "vegano": ["vegetariana", "sem carne", "plantas", "orgânico"],
    "vegetariano": ["vegetariana", "vegano", "sem carne"],
    "vegan": ["vegano", "vegetariana", "sem carne"],
    
    # Mexicana
    "mexicana": ["tacos", "burritos", "tex-mex", "picante"],
    "tacos": ["mexicana", "burritos", "tex-mex"],
    "burritos": ["mexicana", "tacos", "tex-mex"],
    
    # Outros
    "lanche": ["sanduíche", "hambúrguer", "burger", "fast food"],
    "sanduíche": ["lanche", "hambúrguer", "burger"],
    "salada": ["vegetariana", "vegano", "saudável"],
    "saudável": ["vegetariana", "vegano", "salada", "orgânico"],
    
    # FASE 3: Expansões adicionais
    "brasileira": ["feijoada", "moqueca", "churrasco", "picanha", "rodízio", "carne grelhada", "arroz e feijão"],
    "feijoada": ["brasileira", "comida caseira", "tradicional"],
    "moqueca": ["brasileira", "frutos do mar", "peixe"],
    "oriental": ["japonesa", "chinesa", "sushi", "sashimi", "yakisoba"],
    "chinesa": ["yakisoba", "lámen", "ramen", "oriental", "chop suey"],
    "yakisoba": ["chinesa", "oriental", "massa", "macarrão"],
    "lámen": ["japonesa", "oriental", "sopa", "ramen"],
    "ramen": ["japonesa", "oriental", "sopa", "lámen"],
    "temaki": ["japonesa", "sushi", "peixe cru", "oriental"],
    "cantina": ["italiana", "massa", "pizza", "caseira"],
    "risoto": ["italiana", "massa", "arroz", "cremoso"],
    "lasanha": ["italiana", "massa", "queijo", "molho"],
    "carbonara": ["italiana", "massa", "bacon", "ovo"],
    "bolognese": ["italiana", "massa", "molho", "carne"],
    "frutos do mar": ["peixe", "camarão", "siri", "brasileira", "moqueca"],
    "peixe": ["frutos do mar", "sushi", "sashimi", "moqueca"],
    "carne": ["churrasco", "picanha", "rodízio", "brasileira", "grelhada"],
    "costela": ["churrasco", "brasileira", "rodízio", "carne"],
    "maminha": ["churrasco", "brasileira", "rodízio", "carne"],
    "fraldinha": ["churrasco", "brasileira", "rodízio", "carne"],
    "espetinho": ["churrasco", "carne grelhada", "brasileira"],
    "steakhouse": ["churrasco", "carne", "premium", "brasileira"],
    "libanesa": ["árabe", "esfiha", "quibe", "shawarma"],
    "síria": ["árabe", "libanesa", "esfiha", "quibe"],
    "quibe": ["árabe", "esfiha", "kibe", "libanesa"],
    "kibe": ["árabe", "quibe", "esfiha", "libanesa"],
    "hummus": ["árabe", "libanesa", "grão-de-bico"],
    "falafel": ["árabe", "vegetariana", "grão-de-bico"],
    "tabule": ["árabe", "salada", "libanesa"],
    "tacos": ["mexicana", "burritos", "tex-mex", "picante"],
    "burritos": ["mexicana", "tacos", "tex-mex"],
    "quesadillas": ["mexicana", "queijo", "tortilla"],
    "guacamole": ["mexicana", "abacate", "picante"],
    "nachos": ["mexicana", "queijo", "picante"],
    "tex-mex": ["mexicana", "tacos", "burritos"],
    "picante": ["mexicana", "pimenta", "temperado"],
    "orgânico": ["vegetariana", "vegano", "saudável", "natural"],
    "natural": ["vegetariana", "vegano", "orgânico", "saudável"],
    "sem carne": ["vegetariana", "vegano", "plantas"],
    "plantas": ["vegetariana", "vegano", "orgânico"],
}


def expand_query_with_synonyms(query: str, max_expansions: int = 3) -> str:
    """
    Expande uma query adicionando sinônimos e termos relacionados.
    
    Estratégia:
    1. Identifica termos-chave na query
    2. Busca sinônimos no mapa
    3. Adiciona sinônimos mais relevantes à query
    4. Retorna query expandida
    
    Args:
        query: Query original do usuário
        max_expansions: Número máximo de sinônimos a adicionar por termo
    
    Returns:
        Query expandida com sinônimos (formato: "termo1 OR termo2 OR sinônimo1 OR sinônimo2")
    """
    if not query or not query.strip():
        return query
    
    query_lower = query.lower().strip()
    original_terms = set(query_lower.split())
    
    # Remover stopwords comuns
    stopwords = {
        'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
        'em', 'no', 'na', 'nos', 'nas', 'para', 'com', 'por', 'sobre',
        'que', 'qual', 'quais', 'me', 'você', 'vocês', 'seu', 'sua',
        'mais', 'muito', 'bem', 'melhor', 'melhores', 'quero', 'queria',
        'restaurante', 'restaurantes', 'disponíveis', 'mostre', 'mostrar'
    }
    
    # Filtrar termos relevantes (não stopwords, > 2 caracteres)
    relevant_terms = [
        term for term in original_terms 
        if term not in stopwords and len(term) > 2
    ]
    
    if not relevant_terms:
        # Se não há termos relevantes, retornar query original
        return query
    
    # Coletar sinônimos
    expanded_terms = set(original_terms)  # Começar com termos originais
    
    for term in relevant_terms:
        # Buscar sinônimos no mapa (busca exata e parcial)
        synonyms = []
        
        # Busca exata
        if term in SYNONYM_MAP:
            synonyms.extend(SYNONYM_MAP[term][:max_expansions])
        
        # Busca parcial (termo contém chave ou chave contém termo)
        for key, values in SYNONYM_MAP.items():
            if term in key or key in term:
                synonyms.extend(values[:max_expansions])
                break
        
        # Adicionar sinônimos únicos
        for synonym in synonyms:
            if synonym not in expanded_terms:
                expanded_terms.add(synonym)
    
    # Se não encontrou sinônimos, retornar query original
    if len(expanded_terms) == len(original_terms):
        logger.debug(f"Nenhum sinônimo encontrado para query: {query}")
        return query
    
    # Construir query expandida
    # Estratégia: Manter termos originais + adicionar sinônimos mais relevantes
    expanded_query_parts = list(original_terms)
    
    # Adicionar sinônimos novos (não presentes na query original)
    new_synonyms = expanded_terms - original_terms
    expanded_query_parts.extend(list(new_synonyms)[:max_expansions * len(relevant_terms)])
    
    # Construir query final (termos originais + sinônimos)
    expanded_query = " ".join(expanded_query_parts)
    
    logger.debug(f"Query expandida: '{query}' → '{expanded_query}'")
    
    return expanded_query


def get_synonyms_for_term(term: str) -> List[str]:
    """
    Retorna lista de sinônimos para um termo específico.
    
    Args:
        term: Termo para buscar sinônimos
    
    Returns:
        Lista de sinônimos (pode estar vazia)
    """
    term_lower = term.lower().strip()
    
    # Busca exata
    if term_lower in SYNONYM_MAP:
        return SYNONYM_MAP[term_lower]
    
    # Busca parcial
    for key, values in SYNONYM_MAP.items():
        if term_lower in key or key in term_lower:
            return values
    
    return []


def should_expand_query(query: str) -> bool:
    """
    Decide se uma query deve ser expandida com sinônimos.
    
    Critérios:
    - Query não muito longa (< 50 caracteres)
    - Query não contém muitos termos (> 10 palavras)
    - Query contém termos que podem ter sinônimos
    
    Args:
        query: Query a avaliar
    
    Returns:
        True se deve expandir, False caso contrário
    """
    if not query or len(query.strip()) < 3:
        return False
    
    # Não expandir queries muito longas (provavelmente perguntas complexas)
    if len(query) > 100:
        return False
    
    # Não expandir se tiver muitos termos (pode ser pergunta específica)
    word_count = len(query.split())
    if word_count > 10:
        return False
    
    # Verificar se há termos que podem ter sinônimos
    query_lower = query.lower()
    for key in SYNONYM_MAP.keys():
        if key in query_lower:
            return True
    
    return False

