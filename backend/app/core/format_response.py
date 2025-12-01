"""
Pós-processamento de resposta para aplicar formatação visual
quando o LLM não segue as instruções de formatação
"""

import re
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document


def get_cuisine_emoji(cuisine_type: str) -> str:
    """
    Retorna emoji contextualmente relevante baseado no tipo de culinária.
    FASE 5: Mapeamento centralizado com correspondência parcial para cobrir variações.
    
    Args:
        cuisine_type: Tipo de culinária (ex: "italiana", "pizzaria", "japonesa")
    
    Returns:
        Emoji correspondente ou emoji padrão se não encontrado
    """
    if not cuisine_type:
        return "🍽️"  # Default genérico
    
    c_lower = cuisine_type.lower()
    
    # Dicionário de mapeamento (ordem importa: termos mais específicos primeiro)
    emoji_map = {
        "pizza": "🍕",
        "hambúrguer": "🍔",
        "burger": "🍔",
        "americana": "🍔",
        "japonesa": "🍣",
        "sushi": "🍣",
        "oriental": "🥢",
        "italiana": "🍝",
        "massa": "🍝",
        "brasileira": "🇧🇷",
        "feijoada": "🍛",
        "mexicana": "🌮",
        "taco": "🌮",
        "churrasco": "🥩",
        "churrascaria": "🥩",
        "carne": "🥩",
        "vegetariana": "🥗",
        "vegana": "🌿",
        "saudável": "🥑",
        "salada": "🥗",
        "café": "☕",
        "cafeteria": "☕",
        "padaria": "🥐",
        "doce": "🍰",
        "sobremesa": "🍨",
        "sorvete": "🍦",
        "frutos do mar": "🦐",
        "peixe": "🐟",
        "arabe": "🥙",
        "árabe": "🥙",
        "libanesa": "🥙",
        "chinesa": "🥡",
        "indiana": "🍛",
        "francesa": "🥖",
        "bebida": "🍹",
        "bar": "🍺",
        "hamburgueria": "🍔",
        "pizzaria": "🍕",
    }
    
    # Verificar correspondência parcial
    for key, emoji in emoji_map.items():
        if key in c_lower:
            return emoji
    
    return "🍽️"  # Fallback


def apply_visual_formatting(
    answer: str,
    source_documents: List[Document],
    question: str
) -> str:
    """
    Aplica formatação visual e REMOVE o texto original duplicado.
    FASE 3: Remoção destrutiva de parágrafos descritivos antes de adicionar cards.
    
    Detecta restaurantes mencionados e aplica formatação completa:
    - Emojis de culinária
    - Separadores visuais
    - Preço formatado
    - Localização
    - Destaque único
    - Rating formatado
    
    Args:
        answer: Resposta do LLM
        source_documents: Documentos recuperados do RAG
        question: Pergunta original
    
    Returns:
        Resposta formatada sem duplicatas
    """
    # CORREÇÃO CRÍTICA: Verificar se há correspondência semântica antes de formatar
    # Se a resposta indica que não há restaurantes relevantes, não formatar documentos não relacionados
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    # Detectar se a resposta indica que não há correspondência
    no_match_indicators = [
        'não temos', 'não tenho', 'não encontrei', 'não encontramos',
        'infelizmente', 'não está disponível', 'não está na lista',
        'não temos na nossa lista', 'não tenho na minha lista'
    ]
    
    has_no_match_indicator = any(indicator in answer_lower for indicator in no_match_indicators)
    
    # Se a resposta indica que não há match, verificar se os documentos são realmente relevantes
    if has_no_match_indicator:
        # Verificar se algum documento tem correspondência semântica com a pergunta
        question_keywords = set([w.lower() for w in question_lower.split() if len(w) > 2])
        has_relevant_doc = False
        
        for doc in source_documents:
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            if metadata.get('type') == 'restaurant':
                name = metadata.get('name', '').lower()
                keywords = metadata.get('keywords', '').lower()
                description = (metadata.get('description', '') or '').lower()
                cuisine = metadata.get('cuisine_type', '').lower()
                
                # Verificar correspondência com palavras-chave da pergunta
                doc_text = f"{name} {keywords} {description} {cuisine}"
                if any(kw in doc_text for kw in question_keywords if len(kw) > 3):
                    has_relevant_doc = True
                    break
        
        # Se não há documento relevante, não formatar (retornar resposta original limpa)
        if not has_relevant_doc:
            # Limpar erros de português e textos incompletos antes de retornar
            cleaned_no_match = answer
            # Remover frases problemáticas
            problematic_patterns = [
                r'(?i)No\s+entanto,\s+posso\s+sugerir\s+algumas\s+alternativas\s+próximas[^.]*\.\s*',
                r'(?i)posso\s+sugerir\s+algumas\s+alternativas\s+próximas[^.]*\.\s*',
                r'(?i)Se\s+você\s+estiver\s+procurando\s+por\s+algo\s+semelhante[^.]*\.\s*',
                r'(?i)eu\s+recomendaria\s+o\s+de\s+ou\s+a[^.]*\.\s*',
                r'(?i)recomendaria\s+o\s+de\s+ou\s+a[^.]*\.\s*',
                r'(?i)recomendaria\s+o\s+de[^.]*\.\s*',
                r'(?i)recomendaria\s+a\s+de[^.]*\.\s*',
            ]
            for pattern in problematic_patterns:
                cleaned_no_match = re.sub(pattern, '', cleaned_no_match, flags=re.IGNORECASE)
            # Limpar espaços duplos e pontuação duplicada
            cleaned_no_match = re.sub(r'\s{2,}', ' ', cleaned_no_match)
            cleaned_no_match = re.sub(r'\.\s*\.', '.', cleaned_no_match)
            cleaned_no_match = cleaned_no_match.strip()
            return cleaned_no_match
    
    # 1. Identificar quais restaurantes foram citados
    restaurant_mentions = extract_restaurant_mentions(answer, source_documents)
    
    if not restaurant_mentions:
        return answer
    
    # 2. REMOÇÃO DESTRUTIVA: Remove trechos onde o LLM descreve o restaurante
    # para evitar que a informação apareça duas vezes (no texto e no card)
    cleaned_answer = answer
    
    # Primeiro: remover texto introdutório verboso antes dos restaurantes
    # CORREÇÃO CRÍTICA: Remover frases genéricas sobre pratos/culinária e erros de português
    verbose_patterns = [
        r'(?i)^.*?posso\s+sugerir[^.]*\.\s*',
        r'(?i)^.*?algumas\s+opções[^.]*\.\s*',
        r'(?i)^.*?restaurantes\s+listados[^.]*\.\s*',
        r'📄\s+visitar[^.]*\.\s*',
        r'⬆️\s*💥\s*',
        r'(?i)^.*?No\s+entanto[^.]*\.\s*',
        # Erros de português e textos incompletos
        r'(?i)No\s+entanto,\s+posso\s+sugerir\s+algumas\s+alternativas\s+próximas[^.]*\.\s*',
        r'(?i)posso\s+sugerir\s+algumas\s+alternativas\s+próximas[^.]*\.\s*',
        r'(?i)Se\s+você\s+estiver\s+procurando\s+por\s+algo\s+semelhante[^.]*\.\s*',
        r'(?i)eu\s+recomendaria\s+o\s+de\s+ou\s+a[^.]*\.\s*',
        r'(?i)recomendaria\s+o\s+de\s+ou\s+a[^.]*\.\s*',
        r'(?i)recomendaria\s+o\s+de[^.]*\.\s*',
        r'(?i)recomendaria\s+a\s+de[^.]*\.\s*',
        # NOVO: Remover frases genéricas sobre pratos/culinária
        r'(?i)^\s*[A-Z][^.!?]*\s+(é|são)\s+um\s+(prato|pratos|tipo|tipos)[^.!?]*delicioso[^.!?]*!?\s*',
        r'(?i)^\s*[A-Z][^.!?]*\s+(é|são)\s+um\s+(prato|pratos|tipo|tipos)[^.!?]*tradicional[^.!?]*!?\s*',
        r'(?i)^\s*[A-Z][^.!?]*\s+(é|são)\s+um\s+(prato|pratos|tipo|tipos)[^.!?]*brasileiro[^.!?]*!?\s*',
        # Exemplo específico: "Churrasco é um prato delicioso e tradicional brasileiro!"
        r'(?i)^\s*churrasco\s+é\s+um\s+prato[^.!?]*!?\s*',
        r'(?i)^\s*pizza\s+é\s+um\s+prato[^.!?]*!?\s*',
        r'(?i)^\s*sushi\s+é\s+um\s+prato[^.!?]*!?\s*',
    ]
    for pattern in verbose_patterns:
        cleaned_answer = re.sub(pattern, '', cleaned_answer, flags=re.MULTILINE)
    
    # Segundo: remover descrições de restaurantes mencionados
    # CORREÇÃO CRÍTICA: Remover cards já formatados pelo LLM antes de adicionar novos
    for mention in restaurant_mentions:
        name = mention["name"]
        
        # Regex melhorada: Procura o nome do restaurante seguido de qualquer texto
        # até encontrar duas quebras de linha, outro restaurante, ou fim da string
        # Também captura variações do nome (com/sem pontuação)
        name_variations = [
            re.escape(name),
            re.escape(name.replace("'", "")),
            re.escape(name.replace(".", "")),
        ]
        
        for name_var in name_variations:
            # NOVO: Padrão para remover cards já formatados pelo LLM (com emoji, rating, etc.)
            # Exemplo: "🍔 **McDonald's**\n⭐ 4.0/5.0 | 💰 (R$ 20-50) | 📍 Centro\n..."
            formatted_card_pattern = re.compile(
                rf"[🔥🍝🍣🍔🍕🌮🥙🦞⭐]?\s*\*\*{name_var}\*\*.*?(?=\n\n[🔥🍝🍣🍔🍕🌮🥙🦞⭐]?\s*\*\*|━━|💡|$)",
                flags=re.IGNORECASE | re.DOTALL
            )
            cleaned_answer = re.sub(formatted_card_pattern, "", cleaned_answer)
            
            # Padrão melhorado: nome + qualquer coisa até próximo restaurante, separador, ou fim de parágrafo
            # CORREÇÃO: Capturar descrições longas que incluem pontuação e emojis
            # Padrão 1: "Nome é/é um/é uma/tem/oferece..." seguido de descrição completa
            pattern = re.compile(
                rf"{name_var}\s+(é|é um|é uma|tem|oferece|especializado|especializada|clássico|clássica)[^.!?]*[.!?]?\s*[🔥⭐]*.*?(?=\n\n|(?:\*\*)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\*\*|━━|\d+\.\d+/\d+\.\d+|$)", 
                flags=re.IGNORECASE | re.DOTALL
            )
            cleaned_answer = re.sub(pattern, "", cleaned_answer)
            
            # Padrão 2: "Nome é um clássico..." seguido de descrição (mais específico)
            pattern2 = re.compile(
                rf"{name_var}\s+é\s+um\s+clássico[^.!?]*[.!?]?\s*[🔥⭐]*.*?(?=\n|\d+\.\d+/\d+\.\d+|$)", 
                flags=re.IGNORECASE | re.DOTALL
            )
            cleaned_answer = re.sub(pattern2, "", cleaned_answer)
            
            # Padrão 3: "Nome é um clássico X com Y e Z. É o lugar perfeito..." (frases compostas)
            pattern3 = re.compile(
                rf"{name_var}\s+é\s+um\s+clássico[^.!?]*\.\s*É\s+o\s+[^.!?]*\.\s*[🔥⭐]*", 
                flags=re.IGNORECASE | re.DOTALL
            )
            cleaned_answer = re.sub(pattern3, "", cleaned_answer)
            
            # Padrão 4: Remover menções simples do nome seguido de metadados (ex: "McDonald's ⭐ 4.0/5.0")
            simple_mention_pattern = re.compile(
                rf"{name_var}\s+[⭐💰📍🎯].*?(?=\n\n|{name_var}|\*\*[A-Z]|$)",
                flags=re.IGNORECASE | re.DOTALL
            )
            cleaned_answer = re.sub(simple_mention_pattern, "", cleaned_answer)
    
    # Limpeza de sobras (linhas vazias extras e espaços)
    cleaned_answer = re.sub(r'\n{3,}', '\n\n', cleaned_answer)
    cleaned_answer = re.sub(r'^\s+|\s+$', '', cleaned_answer, flags=re.MULTILINE)
    cleaned_answer = cleaned_answer.strip()
    
    # CORREÇÃO: Remover comparações duplicadas ou incompletas
    # Exemplo: "Comparação: Ambos os restaurantes oferecem batata frita, mas —"
    comparison_patterns = [
        r'💡\s*\*\*Comparação:\*\*\s*[^.]*mas\s*—\s*',
        r'💡\s*Comparação:\s*[^.]*mas\s*—\s*',
        r'Comparação:\s*[^.]*mas\s*—\s*',
    ]
    for pattern in comparison_patterns:
        cleaned_answer = re.sub(pattern, '', cleaned_answer, flags=re.IGNORECASE | re.MULTILINE)
    
    # Se a limpeza removeu tudo ou deixou muito pouco, restaurar intro padrão
    if len(cleaned_answer) < 15:
        cleaned_answer = "Aqui estão as opções encontradas baseadas no seu pedido:"
    
    # 3. Mapeamento de preço para texto formatado
    price_text_map = {
        "high": "💰💰💰 (R$ 80-120)",
        "medium": "💰💰 (R$ 50-80)",
        "low": "💰 (R$ 20-50)"
    }
    
    # 4. Construir seção visual (cards) - usar função centralizada de emoji
    formatted_sections = []
    
    for restaurant_info in restaurant_mentions[:3]:  # Máximo 3
        name = restaurant_info['name']
        metadata = restaurant_info['metadata']
        
        cuisine = metadata.get('cuisine_type', '')
        rating = metadata.get('rating', '')
        price_range = metadata.get('price_range', '')
        location = metadata.get('location', '')
        
        # Usar função centralizada de emoji (FASE 5)
        emoji = get_cuisine_emoji(cuisine)
        
        # Construir seção formatada
        section = f"{emoji} **{name}**\n"
        
        meta_parts = []
        if rating:
            meta_parts.append(f"⭐ {rating}/5.0")
        if price_range and price_range in price_text_map:
            meta_parts.append(price_text_map[price_range])
        elif price_range:
            price_emoji = "💰" if price_range == "high" else "💵" if price_range == "medium" else "💸"
            meta_parts.append(price_emoji)
        # SEMPRE incluir localização se disponível (ou "Não informado" se não tiver)
        if location:
            meta_parts.append(f"📍 {location}")
        elif not location:  # Se não tem localização, não adicionar (evitar "📍 None")
            pass
        
        if meta_parts:
            section += f"   {'  |  '.join(meta_parts)}\n"
        
        # Destaque único
        try:
            from app.core.chef_chat import get_restaurant_highlight
            highlight = get_restaurant_highlight(metadata)
            if highlight:
                section += f"   🎯 {highlight}\n"
        except ImportError:
            # Fallback se houver problema de import circular
            pass
        
        # CORREÇÃO CRÍTICA: Priorizar description do metadata (fonte primária)
        description = metadata.get('description', '').strip()
        
        # Validar se description não contém metadados técnicos
        if description:
            technical_patterns = [
                r'Restaurante:\s*',
                r'Tipo de culinária:\s*',
                r'Tags e pratos relacionados:\s*',
                r'Avaliação:\s*',
                r'Faixa de preço:\s*',
            ]
            has_technical = any(re.search(pattern, description, re.IGNORECASE) for pattern in technical_patterns)
            if has_technical:
                description = ""  # Rejeitar se contém formato técnico
        
        # FALLBACK 1: Se description do metadata não estiver disponível, extrair da resposta
        if not description or len(description) < 20:
            description = extract_restaurant_description(answer, name, max_len=85)
        
        # FALLBACK 2: Se ainda não houver, gerar baseado em metadados
        if not description or len(description) < 20:
            cuisine = metadata.get('cuisine_type', '')
            keywords = metadata.get('keywords', '')
            if cuisine:
                description = f"Restaurante especializado em {cuisine}"
                if keywords:
                    # Pegar primeira keyword relevante (sem tags técnicas)
                    first_keyword = keywords.split(',')[0].strip()
                    if first_keyword and len(first_keyword) < 30:
                        description += f" com foco em {first_keyword}"
                description = description[:85]
        
        # Validar descrição final antes de usar
        if description and len(description) >= 20:
            # Limpar pontuação solta
            description = description.rstrip(',.')
            # Aplicar blacklist conservadora (apenas se muito longa)
            if len(description) > 100:
                blacklist_patterns = [
                    r'^É um restaurante que\s+',
                    r'^Oferece uma experiência de\s+',
                ]
                for pattern in blacklist_patterns:
                    description = re.sub(pattern, '', description, flags=re.IGNORECASE)
                description = description.strip()[:85]
            
            # Validar que não contém palavras soltas sem sentido
            words = description.split()
            if len(words) >= 3:  # Pelo menos 3 palavras
                section += f"   {description}\n"
        
        formatted_sections.append(section)
    
    if formatted_sections:
        # SEMPRE juntar com separadores visuais
        separator = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # 5. Montagem final: texto limpo + cards formatados
        formatted_cards = separator.join(formatted_sections)
        
        # Se houver apenas 1 restaurante, adicionar separador antes e depois para visibilidade
        if len(formatted_sections) == 1:
            formatted_answer = f"{cleaned_answer}\n\n{separator}{formatted_cards}{separator}"
        else:
            # Se houver múltiplos, juntar com separadores entre eles
            formatted_answer = f"{cleaned_answer}\n\n{separator}{formatted_cards}{separator}"
            # Adicionar comparação
            formatted_answer += "\n\n💡 **Comparação:** " + generate_comparison(restaurant_mentions[:3])
        
        return formatted_answer
    
    # Se não houver cards, retornar resposta limpa
    return cleaned_answer


def extract_restaurant_mentions(
    answer: str,
    source_documents: List[Document]
) -> List[Dict[str, Any]]:
    """
    Extrai restaurantes mencionados na resposta com suporte a variações de grafia.
    FASE 4: Melhoria para capturar variações como "Papa John's" vs "Papa Johns".
    
    Returns:
        Lista de dicionários com 'name' e 'metadata'
    """
    mentions = []
    answer_lower = answer.lower()
    added_ids = set()  # Evitar duplicatas
    
    for doc in source_documents:
        metadata = doc.metadata if hasattr(doc, 'metadata') else {}
        if metadata.get('type') != 'restaurant':
            continue
        
        name = metadata.get('name', '').strip()
        if not name:
            continue
        
        # Criar variações para busca (ex: com/sem apóstrofo, minúsculo, sem hífen)
        variations = [
            name.lower(),
            name.lower().replace("'", ""),
            name.lower().replace("'", ""),
            name.lower().replace("-", " "),
            name.lower().replace(".", ""),
            name.lower().replace("'", "").replace("-", " "),  # Combinação
        ]
        
        # Verificar se alguma variação está na resposta
        if any(v in answer_lower for v in variations):
            # Usar restaurant_id se disponível, senão usar name como ID único
            unique_id = metadata.get('restaurant_id') or metadata.get('id') or name
            
            if unique_id not in added_ids:
                mentions.append({
                    "name": name,
                    "metadata": metadata
                })
                added_ids.add(unique_id)
    
    return mentions


def extract_restaurant_description(answer: str, restaurant_name: str, max_len: int = 85) -> str:
    """
    Extrai descrição concisa, removendo fillers e truncando de forma inteligente.
    Não corta palavras ao meio.
    
    Args:
        answer: Resposta completa do LLM
        restaurant_name: Nome do restaurante
        max_len: Comprimento máximo da descrição (padrão: 85)
    
    Returns:
        Descrição limpa e concisa, ou string vazia se não encontrada
    """
    # Blacklist de frases genéricas que não agregam valor
    blacklist_phrases = [
        r'é um restaurante que',
        r'oferece uma experiência de',
        r'famoso por ser',
        r'uma excelente opção para',
        r'experiência de churrasco',
        r'variedade de opções',
        r'ambiente acolhedor',
    ]
    
    # Procurar por padrões como "X tem/é/oferece..."
    patterns = [
        rf'\b{re.escape(restaurant_name)}\b[^.!?]*?([^.!?]+)',
        rf'\b{re.escape(restaurant_name)}\b.*?tem\s+([^.!?]+)',
        rf'\b{re.escape(restaurant_name)}\b.*?oferece\s+([^.!?]+)',
    ]
    
    desc = ""
    for pattern in patterns:
        match = re.search(pattern, answer, re.IGNORECASE)
        if match:
            desc = match.group(1).strip()
            break
    
    if not desc or len(desc) < 20:
        return ""
    
    # CORREÇÃO: Aplicar blacklist de forma conservadora
    # Apenas remover se a descrição for muito longa
    # E remover frases completas, não partes
    if len(desc) > 100:
        # Remover apenas no início da frase (frases completas)
        blacklist_patterns = [
            r'^É um restaurante que\s+',
            r'^Oferece uma experiência de\s+',
            r'^Famoso por ser\s+',
        ]
        for pattern in blacklist_patterns:
            desc = re.sub(pattern, '', desc, flags=re.IGNORECASE)
    
    desc = desc.strip()
    
    # Validar que a descrição faz sentido (não tem palavras soltas)
    words = desc.split()
    if len(words) < 3:
        return ""  # Rejeitar se tiver menos de 3 palavras
    
    # Truncagem inteligente (não corta palavras ao meio)
    if len(desc) <= max_len:
        return desc
    
    truncated = desc[:max_len]
    last_space = truncated.rfind(' ')
    if last_space != -1:
        truncated = truncated[:last_space]
    
    return truncated + "..."


def generate_comparison(restaurants: List[Dict[str, Any]]) -> str:
    """
    Gera comparação rápida entre restaurantes.
    """
    if len(restaurants) < 2:
        return ""
    
    names = [r['name'] for r in restaurants]
    if len(names) == 2:
        return f"{names[0]} é mais premium, enquanto {names[1]} é mais acessível."
    else:
        return f"{names[0]} é premium, {names[1]} é intermediário, e {names[2]} é mais acessível."

