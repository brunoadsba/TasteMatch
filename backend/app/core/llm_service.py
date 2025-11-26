"""
Serviço de integração com LLM (Groq API) para geração de insights contextualizados.
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from groq import Groq
from groq import APIConnectionError, APIError, RateLimitError

from app.config import settings
from app.core.logging_config import get_logger
from app.database.crud import get_recommendation
from app.database.models import Restaurant
# extract_user_patterns será usado apenas quando necessário (evitar import circular)

logger = get_logger(__name__)


def format_cuisine_type(cuisine_type: str) -> str:
    """
    Formata tipo de culinária para uso em texto, adicionando 'comida' quando apropriado.
    
    Args:
        cuisine_type: Tipo de culinária (ex: "brasileira", "japonesa")
        
    Returns:
        str: Tipo formatado (ex: "comida brasileira", "comida japonesa")
    """
    # Se já contém "comida", retornar como está
    if "comida" in cuisine_type.lower():
        return cuisine_type
    
    # Adicionar "comida" antes do tipo
    return f"comida {cuisine_type}"


# Cliente Groq global (singleton)
_groq_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    """
    Obtém ou cria cliente Groq (singleton).
    
    Returns:
        Groq: Cliente Groq configurado
        
    Raises:
        ValueError: Se GROQ_API_KEY não estiver configurada
    """
    global _groq_client
    
    if _groq_client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY não configurada. Configure no arquivo .env ou variáveis de ambiente."
            )
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    
    return _groq_client


def build_insight_prompt(
    user_context: Dict[str, Any],
    restaurant: Restaurant,
    similarity_score: float,
    user_patterns: Optional[Dict[str, Any]] = None
) -> str:
    """
    Constrói prompt contextualizado para geração de insight.
    
    Args:
        user_context: Contexto do usuário (nome, total de pedidos, etc.)
        restaurant: Objeto Restaurant recomendado
        similarity_score: Score de similaridade (0.0 a 1.0)
        user_patterns: Padrões do usuário (opcional)
        
    Returns:
        str: Prompt completo formatado
    """
    # Extrair informações do usuário
    user_name = user_context.get("name", "Usuário")
    total_orders = user_context.get("total_orders", 0)
    favorite_cuisines = user_context.get("favorite_cuisines", [])
    
    # Padrões do usuário (se disponível)
    patterns_text = ""
    if user_patterns:
        patterns_list = []
        if user_patterns.get("preferred_hours"):
            patterns_list.append(f"Horários preferidos: {', '.join(user_patterns['preferred_hours'])}")
        if user_patterns.get("average_order_value"):
            patterns_list.append(f"Ticket médio: R$ {user_patterns['average_order_value']}")
        if patterns_list:
            patterns_text = " - ".join(patterns_list)
    
    # Informações do restaurante
    restaurant_name = restaurant.name
    cuisine_type = restaurant.cuisine_type
    cuisine_type_formatted = format_cuisine_type(cuisine_type)
    rating = float(restaurant.rating or 0)
    description = restaurant.description or "Sem descrição disponível"
    price_range = restaurant.price_range or "não especificado"
    
    # Construir prompt
    prompt = f"""Você é um assistente de recomendações da TasteMatch. 
Seu papel é explicar de forma clara e natural por que um restaurante foi recomendado para um usuário.

CONTEXTO DO USUÁRIO:
- Nome: {user_name}
- Total de pedidos: {total_orders}
- Culinárias favoritas: {', '.join(favorite_cuisines) if favorite_cuisines else 'Nenhuma preferência identificada ainda'}
{f'- Padrões: {patterns_text}' if patterns_text else ''}

RESTAURANTE RECOMENDADO:
- Nome: {restaurant_name}
- Tipo: {cuisine_type_formatted}
- Avaliação: {rating}/5.0
- Faixa de preço: {price_range}
- Descrição: {description}
- Score de similaridade: {similarity_score:.2f}

INSTRUÇÕES IMPORTANTES:
- NÃO mencione o nome do restaurante (já está visível no card)
- NÃO mencione o nome do usuário no início (já está visível no contexto)
- Explique APENAS o motivo da recomendação de forma direta e concisa
- Mencione conexões com o histórico do usuário se relevante
- Destaque 1-2 características principais (rating, tipo de culinária, ou qualidade)
- Seja específico e pessoal, mas breve
- Máximo de 2 frases curtas (50-80 palavras no total)
- Use tom amigável e direto
- Escreva em português do Brasil
- Foque no "por quê" da recomendação, não em descrever o restaurante
- Ao mencionar tipo de culinária, use "comida [tipo]" (ex: "comida brasileira", "comida japonesa")

Exemplos de BOA resposta:
- "Alinhado com seu gosto por {cuisine_type_formatted}, com avaliação de {rating}/5.0."
- "Excelente opção para quem busca alta qualidade, avaliado em {rating}/5.0."
- "Recomendado baseado no seu histórico de preferência por restaurantes com alta avaliação."

Gere o insight (máximo 80 palavras):"""
    
    return prompt


def generate_insight_with_retry(
    prompt: str,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    max_tokens: int = 80
) -> Optional[str]:
    """
    Gera insight usando Groq API com retry e backoff exponencial.
    
    Args:
        prompt: Prompt para enviar ao LLM
        max_retries: Número máximo de tentativas
        initial_delay: Delay inicial em segundos
        max_delay: Delay máximo em segundos
        backoff_factor: Fator de multiplicação do delay a cada retry
        
    Returns:
        Optional[str]: Insight gerado ou None em caso de falha
    """
    client = get_groq_client()
    # Modelos disponíveis: llama-3.3-70b-versatile (mais recente), llama-3.1-8b-instant (mais rápido)
    model = "llama-3.3-70b-versatile"  # Modelo mais recente e recomendado para qualidade
    
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um assistente especializado em recomendações personalizadas de restaurantes. Seja claro, específico e natural. Escreva sempre em português do Brasil."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Balance entre criatividade e consistência
                max_tokens=max_tokens,  # Tokens permitidos (padrão 80 para insights, mais para explicações)
                timeout=10.0  # Timeout de 10 segundos
            )
            
            insight = response.choices[0].message.content.strip()
            return insight
            
        except RateLimitError:
            # Rate limit: aguardar mais tempo
            if attempt < max_retries - 1:
                wait_time = min(delay, max_delay)
                time.sleep(wait_time)
                delay *= backoff_factor
            else:
                return None
                
        except (APIConnectionError, APIError) as e:
            # Erro de conexão ou API: tentar novamente
            if attempt < max_retries - 1:
                wait_time = min(delay, max_delay)
                time.sleep(wait_time)
                delay *= backoff_factor
            else:
                # Última tentativa falhou
                logger.error(
                    f"Erro ao gerar insight após {max_retries} tentativas",
                    extra={"error_type": type(e).__name__, "error": str(e), "attempt": attempt + 1}
                )
                return None
                
        except Exception as e:
            # Outro erro inesperado
            logger.error(
                "Erro inesperado ao gerar insight",
                extra={"error_type": type(e).__name__, "error": str(e)},
                exc_info=True
            )
            return None
    
    return None


def get_cached_insight(
    user_id: int,
    restaurant_id: int,
    db: Any,  # Session
    ttl_days: int = 7
) -> Optional[str]:
    """
    Busca insight em cache da tabela recommendations.
    
    Args:
        user_id: ID do usuário
        restaurant_id: ID do restaurante
        db: Sessão do banco de dados
        ttl_days: TTL em dias (padrão: 7 dias)
        
    Returns:
        Optional[str]: Insight cached ou None se não existir/expirado
    """
    recommendation = get_recommendation(db, user_id=user_id, restaurant_id=restaurant_id)
    
    if recommendation and recommendation.insight_text:
        # Verificar se ainda é válido (não expirou)
        if recommendation.generated_at:
            days_ago = (datetime.now() - recommendation.generated_at).days
            if days_ago < ttl_days:
                return recommendation.insight_text
    
    return None


def generate_insight(
    user_id: int,
    restaurant: Restaurant,
    similarity_score: float,
    user_context: Dict[str, Any],
    user_patterns: Optional[Dict[str, Any]] = None,
    db: Optional[Any] = None,  # Session
    use_cache: bool = True,
    ttl_days: int = 7
) -> str:
    """
    Gera insight contextualizado para uma recomendação.
    
    Args:
        user_id: ID do usuário
        restaurant: Restaurante recomendado
        similarity_score: Score de similaridade
        user_context: Contexto do usuário (nome, pedidos, etc.)
        user_patterns: Padrões do usuário (opcional)
        db: Sessão do banco de dados (opcional, para cache)
        use_cache: Se True, tenta usar cache antes de gerar novo
        ttl_days: TTL do cache em dias
        
    Returns:
        str: Insight gerado ou genérico em caso de falha
    """
    # 1. Tentar buscar do cache
    if use_cache and db:
        cached_insight = get_cached_insight(user_id, restaurant.id, db, ttl_days)
        if cached_insight:
            logger.debug(
                "Insight encontrado em cache",
                extra={"user_id": user_id, "restaurant_id": restaurant.id}
            )
            return cached_insight
    
    # 2. Construir prompt
    prompt = build_insight_prompt(
        user_context=user_context,
        restaurant=restaurant,
        similarity_score=similarity_score,
        user_patterns=user_patterns
    )
    
    # 3. Gerar insight com retry
    insight = generate_insight_with_retry(prompt)
    
    # 4. Fallback: insight genérico se falhar
    if not insight:
        # Insight genérico baseado em informações disponíveis
        favorite_cuisines = user_context.get("favorite_cuisines", [])
        cuisine_match = ""
        if restaurant.cuisine_type in favorite_cuisines:
            cuisine_match = f" Você já pediu comida {restaurant.cuisine_type} antes e "
        
        insight = (
            f"Recomendamos {restaurant.name} porque{cuisine_match}"
            f"ele tem uma avaliação de {restaurant.rating}/5.0 e se alinha com suas preferências."
        )
    
    return insight


def generate_fallback_insight(restaurant: Restaurant) -> str:
    """
    Gera insight genérico como fallback quando LLM não está disponível.
    
    Args:
        restaurant: Restaurante recomendado
        
    Returns:
        str: Insight genérico
    """
    rating = float(restaurant.rating or 0)
    cuisine_type_formatted = format_cuisine_type(restaurant.cuisine_type)
    
    return (
        f"Recomendamos {restaurant.name}, um restaurante de {cuisine_type_formatted} "
        f"com avaliação de {rating}/5.0 estrelas, baseado nas suas preferências."
    )


def build_chef_explanation_prompt(
    user_context: Dict[str, Any],
    restaurant: Restaurant,
    reasoning: List[str],
    similarity_score: float,
    confidence: float,
    user_patterns: Optional[Dict[str, Any]] = None
) -> str:
    """
    Constrói prompt para geração de explicação personalizada do Chef.
    
    Args:
        user_context: Contexto do usuário (nome, total de pedidos, etc.)
        restaurant: Restaurante recomendado
        reasoning: Lista de razões para a recomendação
        similarity_score: Score de similaridade (0.0 a 1.0)
        confidence: Confiança da recomendação (0.0 a 1.0)
        user_patterns: Padrões do usuário (opcional)
        
    Returns:
        str: Prompt completo formatado
    """
    user_name = user_context.get("name", "Usuário")
    total_orders = user_context.get("total_orders", 0)
    favorite_cuisines = user_context.get("favorite_cuisines", [])
    
    # Informações do restaurante
    restaurant_name = restaurant.name
    cuisine_type = restaurant.cuisine_type
    cuisine_type_formatted = format_cuisine_type(cuisine_type)
    rating = float(restaurant.rating or 0)
    description = restaurant.description or "Sem descrição disponível"
    price_range = restaurant.price_range or "não especificado"
    
    # Construir prompt
    prompt = f"""Você é um Chef especialista em recomendações da TasteMatch. 
Seu papel é fazer uma recomendação única, direta e personalizada para o usuário, explicando por que este restaurante foi escolhido especialmente para ele.

CONTEXTO DO USUÁRIO:
- Nome: {user_name}
- Total de pedidos: {total_orders}
- Culinárias favoritas: {', '.join(favorite_cuisines) if favorite_cuisines else 'Ainda explorando preferências'}
{f'- Padrões: {user_patterns}' if user_patterns else ''}

RESTAURANTE RECOMENDADO:
- Nome: {restaurant_name}
- Tipo: {cuisine_type_formatted}
- Avaliação: {rating}/5.0
- Faixa de preço: {price_range}
- Descrição: {description}

RAZÕES DA ESCOLHA:
{chr(10).join(f'- {reason}' for reason in reasoning) if reasoning else '- Baseado nas suas preferências e padrões de pedidos'}

INSTRUÇÕES IMPORTANTES:
- Seja DIRETO e CONVINCENTE (como um chef recomenda pessoalmente)
- Use tom CONVERSACIONAL e AMIGÁVEL (1ª pessoa: "eu recomendo", "escolhi para você")
- Mencione o NOME do restaurante de forma natural
- Explique o "POR QUÊ" de forma clara e específica (use as razões fornecidas)
- Destaque o que torna esta escolha ESPECIAL para este usuário
- Seja BREVE mas IMPACTANTE (3-4 frases, máximo 100 palavras)
- Use português do Brasil
- Seja ENTUASIÁSTA mas AUTÊNTICO
- Conecte com o histórico do usuário quando relevante
- Termine com um convite sutil para experimentar
- Não mencione termos técnicos como "score de similaridade" ou números de similaridade

ESTRUTURA SUGERIDA:
1. Abertura: "Eu escolhi [nome do restaurante] especialmente para você porque..."
2. Corpo: Explicar 2-3 razões principais (usar as razões fornecidas)
3. Fechamento: Convite sutil para experimentar

Exemplo de BOA explicação:
"Eu escolhi {restaurant_name} especialmente para você porque você costuma pedir comida {cuisine_type} e este restaurante tem uma avaliação excelente de {rating}/5.0. Além disso, é uma opção nova que ainda não experimentou, perfeita para variar seus pedidos. Tenho certeza que você vai adorar!"

Gere a explicação do Chef (máximo 100 palavras):"""
    
    return prompt


def generate_chef_explanation(
    user_id: int,
    restaurant: Restaurant,
    reasoning: List[str],
    similarity_score: float,
    confidence: float,
    user_context: Dict[str, Any],
    user_patterns: Optional[Dict[str, Any]] = None,
    db: Optional[Any] = None
) -> str:
    """
    Gera explicação personalizada do Chef para a recomendação escolhida.
    
    Args:
        user_id: ID do usuário
        restaurant: Restaurante recomendado
        reasoning: Lista de razões para a recomendação
        similarity_score: Score de similaridade
        confidence: Confiança da recomendação
        user_context: Contexto do usuário
        user_patterns: Padrões do usuário (opcional)
        db: Sessão do banco de dados (opcional)
        
    Returns:
        str: Explicação gerada pelo Chef
    """
    # Construir prompt
    prompt = build_chef_explanation_prompt(
        user_context=user_context,
        restaurant=restaurant,
        reasoning=reasoning,
        similarity_score=similarity_score,
        confidence=confidence,
        user_patterns=user_patterns
    )
    
    # Gerar explicação com retry (mais tokens para explicação mais completa)
    explanation = generate_insight_with_retry(prompt, max_retries=3, max_tokens=150)
    
    # Fallback: explicação genérica baseada nas razões
    if not explanation:
        rating = float(restaurant.rating or 0)
        cuisine_type_formatted = format_cuisine_type(restaurant.cuisine_type)
        
        reasoning_text = ". ".join(reasoning) if reasoning else "baseado nas suas preferências"
        
        explanation = (
            f"Eu escolhi {restaurant.name} especialmente para você porque {reasoning_text}. "
            f"Este restaurante de {cuisine_type_formatted} tem uma avaliação de {rating}/5.0 "
            f"e tenho certeza que você vai adorar!"
        )
    
    return explanation

