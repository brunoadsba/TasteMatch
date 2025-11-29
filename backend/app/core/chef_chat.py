"""
Lógica específica do Chef Virtual
Gerencia prompts, chains LangChain e integração com RAG
"""

from typing import List, Dict, Any, Optional
import re
from sqlalchemy.orm import Session
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from langchain_groq import ChatGroq
from app.config import settings
from app.core.rag_service import RAGService
from app.core.recommender import extract_user_patterns, generate_recommendations
from app.core.prompt_versions import get_prompt_version_for_user
from app.core.llm_monitoring import LLMMonitoringCallback, log_llm_metrics
from app.database import crud


def create_chef_prompt_template(
    user_preferences: Optional[Dict[str, Any]] = None,
    user_patterns: Optional[Dict[str, Any]] = None,
    user_name: Optional[str] = None,
    prompt_version: str = "v1",
    recommendations: Optional[List[Dict[str, Any]]] = None
) -> PromptTemplate:
    """
    Cria o template de prompt para o Chef Virtual com múltiplas versões para testes A/B
    
    Args:
        user_preferences: Dicionário com preferências do usuário
        user_patterns: Dicionário com padrões extraídos (favorite_cuisines, preferred_hours, etc.)
        user_name: Nome do usuário (opcional)
        prompt_version: Versão do prompt ("v1", "v2", "v3") para testes A/B
    
    Returns:
        PromptTemplate configurado
    """
    # Construir contexto de preferências detalhado
    preferences_text = ""
    if user_patterns or user_preferences:
        pref_parts = []
        
        # Usar padrões extraídos se disponível (mais completo)
        patterns = user_patterns or {}
        prefs = user_preferences or {}
        
        # Culinárias favoritas
        favorite_cuisines = patterns.get("favorite_cuisines") or prefs.get("preferred_cuisines", [])
        if favorite_cuisines:
            cuisines = ", ".join(favorite_cuisines)
            pref_parts.append(f"prefere culinárias: {cuisines}")
        
        # Horários preferidos
        preferred_hours = patterns.get("preferred_hours", [])
        if preferred_hours:
            hours = ", ".join(preferred_hours)
            pref_parts.append(f"geralmente pede na {hours}")
        
        # Ticket médio (se disponível)
        avg_order = patterns.get("average_order_value", 0)
        if avg_order > 0:
            pref_parts.append(f"ticket médio: R$ {avg_order:.2f}")
        
        # Faixa de preço (se disponível)
        price_range = prefs.get("preferred_price_range")
        if price_range:
            pref_parts.append(f"prefere faixa de preço: {price_range}")
        
        if pref_parts:
            user_context = f"{user_name}, " if user_name else "O usuário "
            preferences_text = f"\n{user_context}{', '.join(pref_parts)}. "
            preferences_text += "Se ele pedir algo que não combina com suas preferências, sugira alternativas educadamente."
    
    # Adicionar recomendações ao contexto se disponíveis
    recommendations_text = ""
    if recommendations:
        rec_parts = []
        for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recomendações
            restaurant = rec.get("restaurant")
            if restaurant:
                score = rec.get("similarity_score", 0)
                rec_parts.append(
                    f"{i}. {restaurant.name} ({restaurant.cuisine_type}) - "
                    f"Rating: {restaurant.rating}/5.0 - Similaridade: {score:.2f}"
                )
        
        if rec_parts:
            recommendations_text = (
                f"\n\n**Recomendações Personalizadas para o Usuário:**\n"
                f"{chr(10).join(rec_parts)}\n"
                f"Use essas recomendações quando o usuário pedir sugestões ou quando não houver contexto específico suficiente."
            )
    
    # Versões diferentes do prompt para testes A/B
    if prompt_version == "v2":
        # Versão mais concisa e direta
        user_greeting = f"Olá, {user_name}!" if user_name else "Olá!"
        system_prompt = f"""Você é o Chef Virtual do TasteMatch, especialista em restaurantes e comida.
Seja direto, objetivo e natural.
{user_greeting}
{preferences_text}{recommendations_text}

**ESCOPO**: APENAS restaurantes, comida, pratos, receitas e alimentação.

**REGRAS CRÍTICAS:**
- **CONTEXTO GEOGRÁFICO**: Estamos no Brasil. Priorize restaurantes brasileiros quando disponíveis.
- **USE APENAS O CONTEXTO FORNECIDO**: Use EXCLUSIVAMENTE as informações do campo "Contexto" abaixo. NÃO invente restaurantes, NÃO use conhecimento geral.
- Se mencionar restaurantes, use APENAS os nomes que aparecem EXATAMENTE no contexto ou nas recomendações.
- **RESPEITE O ORÇAMENTO**: Não julgue ou condescenda sobre orçamento limitado. Sugira alternativas dentro do orçamento. Seja empático.
- **SEJA DIRETO E OBJETIVO**: 
  - NÃO use frases como "Com base no contexto", "Eu diria que", "Lembre-se de que", "Você mencionou", "Você quer"
  - NÃO repita a pergunta do usuário
  - NÃO mencione o nome do usuário na resposta
  - NÃO seja condescendente (evite "acho que você pode se arrepender")
  - **SEMPRE mencione o nome do restaurante antes de falar sobre características**: NÃO use "Eles têm", "Eles são", "Eles oferecem" sem mencionar o restaurante primeiro. Use: "[Nome do Restaurante] tem/é/oferece..."
  - Evite frases vagas como "Eles podem ter opções que sejam parecidas", "Pode ser uma boa opção" - seja específico
  - Vá direto ao ponto: mencione restaurantes e características relevantes
  - Evite repetições de informações (avaliação/preço)
  - Seja conciso: remova palavras desnecessárias
- Se não souber algo baseado no contexto, diga: "Não tenho informações específicas sobre isso no momento."
- **CRÍTICO**: Você NÃO responde perguntas sobre viagens, tecnologia, entretenimento, saúde, educação ou qualquer outro assunto fora de comida/restaurantes. Se perguntarem algo fora do escopo, responda: "Desculpe, eu sou especializado APENAS em restaurantes, comida e alimentação. Não posso ajudar com outros assuntos. Como posso ajudá-lo a encontrar um restaurante, prato ou receita hoje?"

Contexto:
{{context}}

Histórico:
{{chat_history}}

Pergunta: {{question}}

Resposta:"""
    
    elif prompt_version == "v3":
        # Versão mais amigável e conversacional
        user_greeting = f"Olá, {user_name}! 🍽️" if user_name else "Olá! 🍽️"
        system_prompt = f"""Você é o Chef Virtual do TasteMatch!
Seja super amigável, conversacional e entusiasmado sobre comida e restaurantes.
{user_greeting}
{preferences_text}{recommendations_text}

**MEU ESCOPO**: Apenas restaurantes, pratos, receitas, culinária e alimentação.

**REGRAS IMPORTANTES:**
- **USE APENAS O CONTEXTO FORNECIDO**: Use EXCLUSIVAMENTE as informações do campo "Contexto disponível" abaixo. NÃO invente restaurantes, NÃO use conhecimento geral.
- Use apenas restaurantes que aparecem EXATAMENTE no contexto abaixo ou nas recomendações.
- **SEJA DIRETO E OBJETIVO**: 
  - NÃO use frases como "Com base no contexto", "Eu diria que", "Lembre-se de que", "Você mencionou", "Você quer"
  - NÃO repita a pergunta do usuário
  - NÃO mencione o nome do usuário na resposta
  - **SEMPRE mencione o nome do restaurante antes de falar sobre características**: NÃO use "Eles têm", "Eles são", "Eles oferecem" sem mencionar o restaurante primeiro. Use: "[Nome do Restaurante] tem/é/oferece..."
  - Evite frases vagas como "Eles podem ter opções que sejam parecidas", "Pode ser uma boa opção" - seja específico
  - Vá direto ao ponto: mencione restaurantes e características relevantes
  - Evite repetições de informações (avaliação/preço)
  - Seja conciso: remova palavras desnecessárias
- Seja amigável e conversacional, mas sempre direto.
- Se não souber algo baseado no contexto, seja honesto: "Não tenho informações específicas sobre isso no momento."
- **CRÍTICO**: Eu NÃO respondo perguntas sobre viagens, tecnologia, entretenimento, saúde, educação ou qualquer outro assunto. Se o usuário perguntar algo fora do escopo, responda educadamente: "Desculpe, eu sou especializado APENAS em restaurantes, comida e alimentação. Não posso ajudar com outros assuntos. Como posso ajudá-lo a encontrar um restaurante, prato ou receita hoje?"

Contexto disponível:
{{context}}

Nossa conversa anterior:
{{chat_history}}

O que você quer saber: {{question}}

Minha resposta:"""
    
    else:
        # Versão padrão (v1) - balanceada e natural
        user_greeting = f"Olá, {user_name}!" if user_name else "Olá!"
        system_prompt = f"""Você é o Chef Virtual do TasteMatch, um especialista em restaurantes e comida.
Seja natural, conversacional e amigável, como se estivesse conversando com um amigo que conhece bem restaurantes.
{user_greeting}
{preferences_text}{recommendations_text}

**ESCOPO DO SEU TRABALHO (APENAS ISSO):**
- Restaurantes e seus cardápios
- Pratos, receitas e ingredientes
- Tipos de culinária (italiana, japonesa, brasileira, etc.)
- Preferências gastronômicas e recomendações
- Avaliações e preços de restaurantes
- Dicas sobre comida e alimentação
- Delivery e pedidos de comida

**REGRAS CRÍTICAS:**
1. **CONTEXTO GEOGRÁFICO**: Estamos no Brasil. Priorize restaurantes brasileiros quando disponíveis. Use culinária e contexto brasileiro.
2. **USE APENAS O CONTEXTO FORNECIDO**: Você DEVE usar EXCLUSIVAMENTE as informações que aparecem no campo "Contexto relevante" abaixo. NÃO use conhecimento geral, NÃO invente restaurantes, NÃO mencione restaurantes que não aparecem explicitamente no contexto.
3. Se o contexto não contiver restaurantes específicos, use as recomendações personalizadas fornecidas acima (se houver).
4. **PROIBIDO MENCIONAR RESTAURANTES FORA DO CONTEXTO**: Se mencionar restaurantes, use APENAS os nomes que aparecem EXATAMENTE no contexto fornecido ou nas recomendações. Se um restaurante não está no contexto, NÃO o mencione, mesmo que você "saiba" que ele existe.
5. **RESPEITE O ORÇAMENTO DO USUÁRIO**: Não julgue ou condescenda sobre orçamento limitado. Sugira alternativas dentro do orçamento informado. Seja empático e respeitoso.
4. **SEJA DIRETO, OBJETIVO E NATURAL**: 
   - NÃO use frases como "Com base no contexto", "Com base nas informações", "Eu diria que", "Lembre-se de que", "Além disso", "É importante verificar"
   - NÃO repita a pergunta do usuário: não diga "Você mencionou...", "Você quer...", "Você está procurando..."
   - NÃO mencione o nome do usuário na resposta (o nome só deve aparecer na saudação inicial, se houver)
   - Vá direto ao ponto: mencione os restaurantes e suas características relevantes
   - **SEMPRE mencione o nome do restaurante antes de falar sobre suas características**: NÃO use "Eles têm", "Eles são", "Eles oferecem" sem mencionar o restaurante primeiro. Use: "[Nome do Restaurante] tem/é/oferece..."
   - Evite repetições: se mencionar avaliação/preço uma vez, não repita para cada restaurante
   - Evite frases vagas como "Eles podem ter opções que sejam parecidas", "Pode ser uma boa opção" - seja específico
   - Seja conciso: remova palavras desnecessárias e informações redundantes
   - Foque no que o usuário precisa saber, não em explicações sobre o processo
   - Seja natural e conversacional, como se estivesse conversando com um amigo que conhece restaurantes
   - Use linguagem simples e direta, evite formalidades excessivas
5. Se não souber algo com certeza baseado no contexto, seja honesto e diga: "Não tenho informações específicas sobre isso no momento. Como posso ajudá-lo de outra forma?"
6. **SOBRE iFood**: Se perguntarem sobre iFood, use APENAS as informações que aparecem no contexto. Se não houver informações sobre iFood no contexto, responda de forma genérica sobre delivery de comida, mas NÃO invente características específicas.
6. **CRÍTICO - FORA DO ESCOPO**: Você NÃO pode e NÃO deve responder perguntas sobre:
   - Viagens, passagens, turismo, hotéis, aeroportos
   - Tecnologia, computadores, celulares, aplicativos (exceto apps de delivery)
   - Entretenimento, filmes, séries, música, shows
   - Serviços financeiros, bancos, cartões de crédito
   - Saúde, medicina, planos de saúde (exceto dietas e restrições alimentares)
   - Educação, escolas, cursos, universidades
   - Automóveis, transporte (exceto delivery)
   - Moda, roupas, acessórios
   - QUALQUER outro assunto que não seja relacionado a comida, restaurantes ou alimentação
   
7. **RESPOSTA PADRÃO PARA FORA DO ESCOPO**: Se o usuário perguntar algo fora do escopo, responda EXATAMENTE assim (sem variações):
   "Desculpe, eu sou especializado APENAS em restaurantes, comida e alimentação. Não posso ajudar com outros assuntos. Como posso ajudá-lo a encontrar um restaurante, prato ou receita hoje?"

**IMPORTANTE**: Se a pergunta não for sobre comida/restaurantes, você DEVE recusar educadamente e redirecionar para o seu escopo.

Contexto relevante:
{{context}}

Histórico da conversa:
{{chat_history}}

Pergunta do usuário: {{question}}

Resposta do Chef Virtual:"""
    
    return PromptTemplate(
        template=system_prompt,
        input_variables=["context", "chat_history", "question"]
    )


def get_conversation_history(
    user_id: int,
    db: Optional[Session] = None,
    max_messages: int = 10
) -> List:
    """
    Obtém histórico de conversa do usuário do banco de dados
    
    Args:
        user_id: ID do usuário
        db: Sessão do banco de dados (opcional, se None retorna lista vazia)
        max_messages: Número máximo de mensagens a retornar
    
    Returns:
        Lista de mensagens (HumanMessage, AIMessage)
    """
    if not db:
        return []
    
    # Buscar mensagens recentes do banco
    messages = crud.get_user_chat_messages_recent(db, user_id, limit=max_messages)
    
    # Converter para formato LangChain (HumanMessage, AIMessage)
    langchain_messages = []
    for msg in reversed(messages):  # Reverter para ordem cronológica (mais antigas primeiro)
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            langchain_messages.append(AIMessage(content=msg.content))
    
    return langchain_messages


def add_to_conversation_history(
    user_id: int,
    human_message: str,
    ai_message: str,
    db: Optional[Session] = None,
    audio_url: Optional[str] = None
):
    """
    Adiciona mensagens ao histórico de conversa no banco de dados
    
    Args:
        user_id: ID do usuário
        human_message: Mensagem do usuário
        ai_message: Resposta do assistente
        db: Sessão do banco de dados (opcional, se None não salva)
        audio_url: URL do áudio da resposta (opcional)
    """
    if not db:
        return
    
    # Salvar mensagem do usuário
    crud.create_chat_message(
        db=db,
        user_id=user_id,
        role="user",
        content=human_message
    )
    
    # Salvar mensagem do assistente
    crud.create_chat_message(
        db=db,
        user_id=user_id,
        role="assistant",
        content=ai_message,
        audio_url=audio_url
    )


def create_chef_chain(
    rag_service: RAGService,
    user_id: Optional[int] = None,
    db: Optional[Session] = None
):
    """
    Cria a chain LangChain para o Chef Virtual usando LCEL (LangChain Expression Language)
    
    Args:
        rag_service: Instância do RAGService
        user_id: ID do usuário (opcional)
        db: Sessão do banco de dados (opcional)
    
    Returns:
        Chain configurada usando LCEL
    """
    # Obter LLM usando LangChain Groq
    # Usar modelo Llama mais antigo e estável que não envia reasoning_effort/reasoning_format
    # llama-3.1-8b-instant é mais estável e não tem esses problemas
    llm = ChatGroq(
        groq_api_key=settings.GROQ_API_KEY,
        model="llama-3.1-8b-instant",  # Modelo estável, sem problemas de reasoning params
        temperature=0.5  # Temperatura mais baixa para respostas mais diretas e objetivas
    )
    
    # Obter preferências e padrões do usuário
    user_preferences = None
    user_patterns = None
    user_name = None
    recommendations = None
    
    if user_id and db:
        # Buscar informações do usuário
        user = crud.get_user(db, user_id)
        if user:
            user_name = user.name
        
        orders = crud.get_user_orders(db, user_id=user_id, limit=50)
        if orders:
            # Buscar restaurantes para extract_user_patterns
            restaurants = crud.get_restaurants(db, skip=0, limit=1000)
            user_patterns = extract_user_patterns(user_id, orders, restaurants)
            
            # Converter padrões para formato de preferências (compatibilidade)
            user_preferences = {
                "preferred_cuisines": user_patterns.get("favorite_cuisines", []),
                "preferred_price_range": None,
                "frequent_restaurants": []
            }
        
        # Buscar recomendações personalizadas do usuário
        try:
            recommendations = generate_recommendations(
                user_id=user_id,
                db=db,
                limit=5,  # Top 5 recomendações
                exclude_recent=True,
                refresh=False
            )
        except Exception as e:
            # Se erro ao buscar recomendações, continuar sem elas
            recommendations = None
    
    # Obter versão do prompt para A/B testing
    prompt_version = get_prompt_version_for_user(user_id)
    
    # Obter retriever com mais documentos para incluir restaurantes
    # Aumentar k para garantir que restaurantes sejam incluídos
    retriever = rag_service.get_retriever(k=10)
    
    # Criar prompt com histórico e perfil completo do usuário
    system_prompt_text = create_chef_prompt_template(
        user_preferences=user_preferences,
        user_patterns=user_patterns,
        user_name=user_name,
        prompt_version=prompt_version,
        recommendations=recommendations
    ).template
    
    def format_docs(docs):
        """Formata documentos para o contexto, incluindo metadados relevantes"""
        formatted = []
        for doc in docs:
            content = doc.page_content
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            # Adicionar informações de metadados se for restaurante
            if metadata.get('type') == 'restaurant':
                name = metadata.get('name', '')
                cuisine = metadata.get('cuisine_type', '')
                if name:
                    formatted.append(f"Restaurante: {name}" + (f" (Culinária: {cuisine})" if cuisine else "") + f"\n{content}")
                else:
                    formatted.append(content)
            else:
                formatted.append(content)
        
        return "\n\n".join(formatted)
    
    # Criar chain usando LCEL
    # Ajustar para receber question como string diretamente
    def create_input_dict(query: str):
        docs = retriever.invoke(query)
        return {
            "context": format_docs(docs),
            "question": query,
            "chat_history": get_conversation_history(user_id or 0, db=db)
        }
    
    chain = (
        RunnablePassthrough() | create_input_dict
        | ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt_text),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}\n\n**CONTEXTO DISPONÍVEL:**\n{context}\n\n**INSTRUÇÕES CRÍTICAS**: Seja natural, direto e conversacional. NÃO use frases como 'Com base no contexto', 'Eu diria que', 'Você mencionou', 'Você quer'. NÃO repita a pergunta do usuário. NÃO mencione o nome do usuário. **SEMPRE mencione o nome do restaurante antes de falar sobre características - NÃO use 'Eles têm' ou 'Eles são' sem mencionar o restaurante primeiro.** Vá direto ao ponto. Evite repetições. Fale como um amigo que conhece restaurantes."),
        ])
        | llm
        | StrOutputParser()
    )
    
    return chain


def extract_restaurant_names_from_text(text: str) -> List[str]:
    """
    Extrai possíveis nomes de restaurantes mencionados no texto
    
    Args:
        text: Texto para analisar
    
    Returns:
        Lista de possíveis nomes de restaurantes
    """
    # Frases comuns a ignorar completamente
    ignore_phrases = {
        'gostaria de saber', 'da lista', 'da comida', 'dos restaurantes',
        'variedade de restaurantes', 'restaurantes da lista', 'menu do',
        'italianos da lista', 'ser da comida', 'restaurantes de comida'
    }
    
    # Palavras comuns a ignorar (stopwords)
    stopwords = {
        'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
        'em', 'no', 'na', 'nos', 'nas', 'para', 'com', 'por', 'sobre',
        'que', 'qual', 'quais', 'me', 'você', 'vocês', 'seu', 'sua',
        'mais', 'muito', 'bem', 'melhor', 'melhores', 'antes', 'depois',
        'algo', 'algum', 'alguma', 'alguns', 'algumas', 'lista', 'menu',
        'ifood', 'tastematch'
    }
    
    # Padrões mais específicos para identificar nomes de restaurantes
    # Focar em nomes próprios reais (começam com maiúscula, não são frases comuns)
    patterns = [
        # Nomes em negrito (markdown) - mais confiável
        r'\*\*([A-Z][a-zA-Z][a-zA-Z\s]{2,}?)\*\*',
        # Nomes após "no", "do", "da", "o", "a" seguidos de vírgula ou ponto
        r'(?:^|\s)(?:no|do|da|dos|das|restaurante|o|a)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:[,\.!?]|$)',
        # Nomes no início de linha seguidos de ":" (formato de lista)
        r'^(\d+\.\s*)?\*\*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\*\*?:',
        # Nomes próprios compostos (ex: "Fogo de Chão", "Papa John's")
        r'\b([A-Z][a-z]+(?:\s+(?:de|da|dos|das|do)\s+[A-Z][a-z]+)+)\b',
        # Nomes de marcas conhecidas (KFC, Popeyes, etc.) - após "o", "a", "no", etc.
        r'\b(?:o|a|no|na|do|da)\s+([A-Z]{2,}[a-z]*)\b',
        # Nomes próprios simples após vírgula ou ponto (ex: "Popeyes. Popeyes têm...")
        r'[\.!?]\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)\s+(?:têm|tem|é|são|oferece|oferecem)',
    ]
    
    restaurant_names = []
    text_lower = text.lower()
    
    # Primeiro, verificar se há frases a ignorar
    for ignore_phrase in ignore_phrases:
        if ignore_phrase in text_lower:
            # Remover a frase ignorada do texto antes de processar
            text = re.sub(re.escape(ignore_phrase), '', text, flags=re.IGNORECASE)
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.MULTILINE)
        for match in matches:
            # match pode ser tupla ou string
            if isinstance(match, tuple):
                # Pegar o último elemento não vazio
                name = next((m for m in match if m and m.strip()), None)
            else:
                name = match
            
            if name:
                name = name.strip()
                # Filtrar nomes muito curtos
                if len(name) < 4:
                    continue
                
                words = name.split()
                # Nome deve ter pelo menos 1 palavra significativa
                significant_words = [w for w in words 
                                   if w.lower() not in stopwords 
                                   and len(w) > 2 
                                   and w[0].isupper()]  # Deve começar com maiúscula
                
                if not significant_words:
                    continue
                
                # Verificar se não é uma frase comum
                name_lower = name.lower()
                if any(ignore in name_lower for ignore in ignore_phrases):
                    continue
                
                # Verificar se tem pelo menos uma palavra que parece nome próprio
                # (começa com maiúscula e tem mais de 3 caracteres)
                if any(len(w) > 3 and w[0].isupper() for w in words):
                    restaurant_names.append(name)
    
    # Remover duplicatas e normalizar
    unique_names = []
    seen = set()
    for name in restaurant_names:
        name_lower = name.lower().strip()
        # Filtrar nomes que são apenas stopwords
        words = name_lower.split()
        if all(w in stopwords for w in words):
            continue
        
        if name_lower not in seen and len(name_lower) > 3:
            unique_names.append(name)
            seen.add(name_lower)
    
    return unique_names


def validate_answer_against_context(
    answer: str,
    source_documents: List[Any],
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Valida se a resposta menciona apenas restaurantes que estão no contexto e no banco de dados
    
    Args:
        answer: Resposta gerada pela IA
        source_documents: Documentos usados como contexto
        db: Sessão do banco de dados (opcional, para validação completa)
    
    Returns:
        Dicionário com validação e score de confiança
    """
    # Extrair nomes de restaurantes do contexto
    context_restaurant_names = set()
    for doc in source_documents:
        metadata = doc.metadata if hasattr(doc, 'metadata') else doc.get('metadata', {})
        if metadata.get('type') == 'restaurant':
            name = metadata.get('name', '')
            if name:
                context_restaurant_names.add(name.lower())
                # Também adicionar variações (sem acentos, etc.)
                context_restaurant_names.add(name.lower().replace('ã', 'a').replace('õ', 'o'))
    
    # Se db disponível, buscar todos os restaurantes do banco para validação completa
    all_restaurant_names = set()
    if db:
        try:
            restaurants = crud.get_restaurants(db, skip=0, limit=1000)
            for restaurant in restaurants:
                all_restaurant_names.add(restaurant.name.lower())
                all_restaurant_names.add(restaurant.name.lower().replace('ã', 'a').replace('õ', 'o'))
        except Exception:
            pass  # Se erro, usar apenas contexto
    
    # Extrair nomes mencionados na resposta
    mentioned_restaurants = extract_restaurant_names_from_text(answer)
    mentioned_lower = [name.lower() for name in mentioned_restaurants]
    
    # Verificar quais estão no contexto E no banco (se disponível)
    valid_mentions = []
    invalid_mentions = []
    
    for mention in mentioned_lower:
        # Verificar correspondência exata ou parcial no contexto
        found_in_context = False
        for context_name in context_restaurant_names:
            if mention in context_name or context_name in mention:
                found_in_context = True
                break
        
        # Se db disponível, também verificar se existe no banco
        found_in_db = False
        if db and all_restaurant_names:
            for db_name in all_restaurant_names:
                if mention in db_name or db_name in mention:
                    found_in_db = True
                    break
        
        # Restaurante é válido se está no contexto OU (se db disponível, está no banco)
        if found_in_context or (db and found_in_db):
            valid_mentions.append(mention)
        elif len(mention) > 3:  # Ignorar palavras muito curtas
            invalid_mentions.append(mention)
    
    # Calcular score de confiança
    total_restaurant_docs = sum(1 for doc in source_documents 
                                if (doc.metadata if hasattr(doc, 'metadata') else doc.get('metadata', {})).get('type') == 'restaurant')
    total_sources = len(source_documents)
    
    # Score baseado em:
    # - Quantidade de documentos de restaurantes no contexto (0.0 a 0.5)
    # - Validação de nomes mencionados (0.0 a 0.5)
    context_score = min(0.5, (total_restaurant_docs / max(1, total_sources)) * 0.5)
    
    if mentioned_restaurants:
        validation_score = (len(valid_mentions) / len(mentioned_restaurants)) * 0.5
    else:
        # Se não mencionou restaurantes, não há problema de alucinação
        validation_score = 0.5
    
    confidence_score = context_score + validation_score
    
    return {
        "confidence_score": round(confidence_score, 2),
        "total_sources": total_sources,
        "restaurant_sources": total_restaurant_docs,
        "mentioned_restaurants": mentioned_restaurants,
        "valid_mentions": valid_mentions,
        "invalid_mentions": invalid_mentions,
        "has_potential_hallucination": len(invalid_mentions) > 0
    }


def fix_vague_restaurant_references(answer: str, source_documents: List[Any]) -> str:
    """
    Corrige referências vagas a restaurantes (ex: "Eles têm" sem mencionar o restaurante)
    
    Args:
        answer: Resposta gerada
        source_documents: Documentos de contexto
    
    Returns:
        Resposta corrigida
    """
    import re
    
    # Extrair nomes de restaurantes do contexto
    restaurant_names = []
    for doc in source_documents:
        metadata = doc.metadata if hasattr(doc, 'metadata') else doc.get('metadata', {})
        if metadata.get('type') == 'restaurant':
            name = metadata.get('name', '')
            if name:
                restaurant_names.append(name)
    
    if not restaurant_names:
        return answer
    
    # Padrões de referências vagas
    vague_patterns = [
        (r'\bEles têm\b', 'têm'),
        (r'\bEles são\b', 'são'),
        (r'\bEles oferecem\b', 'oferecem'),
        (r'\bEles podem ter\b', 'podem ter'),
        (r'\bEles também são\b', 'também são'),
        (r'\bEles também oferecem\b', 'também oferecem'),
    ]
    
    # Dividir em frases (por ponto, exclamação ou interrogação)
    sentences = re.split(r'([.!?]\s+)', answer)
    corrected_sentences = []
    last_mentioned_restaurant = None
    
    for i in range(0, len(sentences), 2):  # Processar pares (frase + pontuação)
        if i >= len(sentences):
            break
        
        sentence = sentences[i]
        punctuation = sentences[i+1] if i+1 < len(sentences) else ''
        sentence_lower = sentence.lower()
        
        # Verificar se há nome de restaurante na frase atual
        current_restaurant = None
        for name in restaurant_names:
            if name.lower() in sentence_lower:
                current_restaurant = name
                last_mentioned_restaurant = name
                break
        
        # Verificar se a frase tem referência vaga
        for pattern, verb in vague_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                # Se não há restaurante na frase atual, corrigir
                if not current_restaurant:
                    if last_mentioned_restaurant:
                        # Usar o último restaurante mencionado
                        sentence = re.sub(
                            pattern,
                            f'{last_mentioned_restaurant} {verb}',
                            sentence,
                            flags=re.IGNORECASE,
                            count=1
                        )
                        current_restaurant = last_mentioned_restaurant
                    else:
                        # Usar o primeiro restaurante do contexto
                        if restaurant_names:
                            sentence = re.sub(
                                pattern,
                                f'{restaurant_names[0]} {verb}',
                                sentence,
                                flags=re.IGNORECASE,
                                count=1
                            )
                            current_restaurant = restaurant_names[0]
                            last_mentioned_restaurant = restaurant_names[0]
                break
        
        corrected_sentences.append(sentence)
        if punctuation:
            corrected_sentences.append(punctuation)
    
    return ''.join(corrected_sentences)


def clean_answer(answer: str, user_name: Optional[str] = None, question: Optional[str] = None) -> str:
    """
    Limpa a resposta removendo frases proibidas, repetições e informações desnecessárias
    
    Args:
        answer: Resposta gerada pelo LLM
        user_name: Nome do usuário (opcional, para remover menções)
        question: Pergunta original (opcional, para detectar repetições)
    
    Returns:
        Resposta limpa
    """
    import re
    
    # Frases proibidas a remover
    forbidden_phrases = [
        r'\bEu diria que\b',
        r'\bAlém disso\b',
        r'\bLembre-se de que\b',
        r'\bCom base no contexto\b',
        r'\bCom base nas informações\b',
        r'\bEles podem ter opções que sejam parecidas\b',
        r'\bPode ser uma boa opção\b',
        r'\bÉ uma opção muito\b',
        r'\bcom um preço que se encaixa perfeitamente no seu orçamento\b',
        r'\bpara completar\b',
        r'\bÉ uma opção muito econômica\b',
        r'\bcom um preço que se encaixa\b',
        r'\bno seu orçamento\b',
        r'\bVocê pode pedir\b',
        # Frases condescendentes sobre orçamento
        r'\bacho que você pode se arrepender\b',
        r'\bvocê pode se arrepender\b',
        r'\bse arrepender\b',
        r'\bnão ter mais dinheiro\b',
        r'\bvocê pode se arrepender de não ter\b',
    ]
    
    # Remover frases proibidas
    for phrase in forbidden_phrases:
        answer = re.sub(phrase, '', answer, flags=re.IGNORECASE)
    
    # Remover menções ao nome do usuário no início da resposta
    if user_name:
        # Padrões como "Bruno, você quer..." ou "Bruno, você está procurando..."
        patterns = [
            rf'^{re.escape(user_name)},\s*',
            rf'^{re.escape(user_name)}\s+você\s+',
            rf'^{re.escape(user_name)}\s+quer\s+',
            # Padrão completo: "Bruno, você quer [tudo até o ponto]"
            rf'^{re.escape(user_name)},\s+você\s+quer\s+[^.]*?\.\s*',
        ]
        for pattern in patterns:
            answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
    
    # Remover repetições da pergunta do usuário
    if question:
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # Padrões de repetição da pergunta (mais específicos e completos)
        repetition_patterns = [
            # Padrões gerais de repetição
            r'você\s+quer\s+[^.]*?\.\s*',
            r'você\s+está\s+procurando\s+[^.]*?\.\s*',
            r'você\s+mencionou\s+[^.]*?\.\s*',
            r'você\s+quer\s+gastar\s+[^.]*?\.\s*',
            r'você\s+quer\s+um\s+[^.]*?\.\s*',
            r'você\s+quer\s+comer\s+[^.]*?\.\s*',
            r'você\s+quer\s+[^.]*?e\s+quer\s+[^.]*?\.\s*',  # "você quer X e quer Y"
            # Padrões com nome do usuário
            r'[A-Z][a-z]+,\s+você\s+quer\s+[^.]*?\.\s*',
            r'[A-Z][a-z]+\s+você\s+quer\s+[^.]*?\.\s*',
        ]
        
        for pattern in repetition_patterns:
            answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
        
        # Detectar se o início da resposta é uma repetição da pergunta
        answer_words = answer.split()
        question_words = question.split()
        
        if len(answer_words) > 3 and len(question_words) > 3:
            # Verificar se a resposta começa repetindo a pergunta
            # Comparar primeiras palavras (ignorando stopwords)
            stopwords = {'você', 'quer', 'um', 'uma', 'de', 'do', 'da', 'com', 'e', 'ou', 'para', 'em', 'no', 'na', 'dos', 'das', 'o', 'a', 'os', 'as'}
            
            # Pegar primeiras 10 palavras da resposta e pergunta (sem stopwords)
            answer_start_words = [w.lower() for w in answer_words[:10] if w.lower() not in stopwords]
            question_start_words = [w.lower() for w in question_words if w.lower() not in stopwords]
            
            # Verificar sobreposição
            if len(answer_start_words) > 0 and len(question_start_words) > 0:
                # Contar quantas palavras da resposta estão na pergunta
                matches = sum(1 for w in answer_start_words[:5] if w in question_start_words)
                
                # Se mais de 3 palavras iniciais da resposta estão na pergunta, é repetição
                if matches >= 3:
                    # Encontrar onde começa a resposta real (após ponto, vírgula ou quebra)
                    match = re.search(r'[.,]\s+([A-Z])', answer)
                    if match:
                        answer = answer[match.start() + 2:]  # Remover até a vírgula/ponto + espaço
                    else:
                        # Procurar por palavras-chave de restaurantes ou informações úteis
                        restaurant_keywords = ['restaurante', 'casa', 'giraffas', 'coco', 'viena', 'pão', 'especializado', 'avaliação', 'preço']
                        for i, word in enumerate(answer_words):
                            if any(kw in word.lower() for kw in restaurant_keywords):
                                answer = ' '.join(answer_words[i:])
                                break
                        else:
                            # Se não encontrar, remover primeiras 5 palavras
                            if len(answer_words) > 5:
                                answer = ' '.join(answer_words[5:])
    
    # Remover repetições de nomes de restaurantes no mesmo parágrafo
    # Dividir em sentenças (por ponto, vírgula ou ponto e vírgula)
    sentences = re.split(r'([.,;]\s+)', answer)
    corrected_sentences = []
    seen_restaurant_names_in_paragraph = set()
    
    for i, sentence in enumerate(sentences):
        # Detectar nomes de restaurantes na sentença (nomes próprios com mais de 3 caracteres)
        # Padrão: palavras que começam com maiúscula e têm mais de 3 caracteres
        restaurant_name_pattern = r'\b([A-Z][a-záàâãéèêíìîóòôõúùûç]+(?:\s+[A-Z][a-záàâãéèêíìîóòôõúùûç]+)*)\b'
        names_in_sentence = re.findall(restaurant_name_pattern, sentence)
        
        # Filtrar apenas nomes que parecem restaurantes (mais de 3 caracteres, não são palavras comuns)
        common_words = {'Bruno', 'Você', 'Eles', 'Ela', 'Ele', 'Nós', 'Vós', 'Eles', 'Elas'}
        restaurant_names = [name for name in names_in_sentence 
                          if len(name) > 3 and name not in common_words]
        
        # Verificar se algum nome já foi mencionado neste parágrafo
        for name in restaurant_names:
            name_lower = name.lower()
            if name_lower in seen_restaurant_names_in_paragraph:
                # Remover esta ocorrência do nome (substituir por string vazia)
                sentence = re.sub(
                    r'\b' + re.escape(name) + r'\b',
                    '',
                    sentence,
                    count=1,  # Apenas a primeira ocorrência nesta sentença
                    flags=re.IGNORECASE
                )
            else:
                # Adicionar à lista de nomes vistos neste parágrafo
                seen_restaurant_names_in_paragraph.add(name_lower)
        
        # Se a sentença termina com ponto, limpar a lista (novo parágrafo)
        if sentence.strip().endswith('.'):
            seen_restaurant_names_in_paragraph.clear()
        
        corrected_sentences.append(sentence)
    
    answer = ''.join(corrected_sentences)
    
    # Remover espaços duplos e limpar
    answer = re.sub(r'\s+', ' ', answer)
    answer = re.sub(r'\s+([.,!?])', r'\1', answer)  # Remover espaço antes de pontuação
    answer = answer.strip()
    
    # Se a resposta começa com vírgula ou ponto, remover
    answer = re.sub(r'^[.,]\s*', '', answer)
    
    # Capitalizar primeira letra
    if answer and answer[0].islower():
        answer = answer[0].upper() + answer[1:]
    
    return answer


def get_chef_response(
    question: str,
    rag_service: RAGService,
    user_id: Optional[int] = None,
    db: Optional[Session] = None,
    audio_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtém resposta do Chef Virtual para uma pergunta
    
    Args:
        question: Pergunta do usuário
        rag_service: Instância do RAGService
        user_id: ID do usuário (opcional)
        db: Sessão do banco de dados (opcional)
    
    Returns:
        Dicionário com resposta, metadados e validação
    """
    # Criar chain
    chain = create_chef_chain(rag_service, user_id, db)
    
    # Decidir qual tipo de busca usar
    question_lower = question.lower()
    
    # Usar Hybrid Search se:
    # 1. Pergunta menciona "restaurante" ou "restaurantes"
    # 2. Pergunta contém palavras que podem ser nomes de restaurantes (palavras com mais de 3 letras)
    # 3. Pergunta pede algo específico (ex: "McDonald's", "pizza", "italiano")
    use_hybrid = (
        'restaurante' in question_lower or 
        'restaurantes' in question_lower or
        'disponíveis' in question_lower or
        any(len(word) > 3 for word in question_lower.split())  # Possível nome de restaurante
    )
    
    if use_hybrid:
        # Usar busca híbrida (exata + semântica)
        source_documents = rag_service.hybrid_search(question, k=8, exact_weight=0.6, semantic_weight=0.4)
    else:
        # Usar apenas busca semântica
        source_documents = rag_service.similarity_search(question, k=8)
    
    # Verificar se há contexto suficiente
    restaurant_docs = [doc for doc in source_documents 
                      if (doc.metadata if hasattr(doc, 'metadata') else {}).get('type') == 'restaurant']
    
    # Verificar se a pergunta é sobre recomendações ou sugestões
    is_recommendation_request = any(keyword in question_lower for keyword in [
        'recomend', 'suger', 'sugest', 'indic', 'indicar', 'qual', 'quais',
        'melhor', 'melhores', 'top', 'favorito', 'favoritos'
    ])
    
    # Fallback se não houver contexto relevante
    # Mas se houver recomendações e a pergunta for sobre recomendações, usar a chain (já tem recomendações no prompt)
    if len(restaurant_docs) == 0 and ('restaurante' in question_lower or 'restaurantes' in question_lower):
        # Se a pergunta é sobre recomendações, a chain já tem recomendações no prompt
        # Então podemos continuar mesmo sem documentos de restaurantes
        if not is_recommendation_request:
            fallback_message = (
                "Não encontrei restaurantes específicos no momento. "
                "Que tal perguntar sobre tipos de culinária ou suas preferências gastronômicas?"
            )
            
            return {
                "answer": fallback_message,
                "source_documents": [
                    {
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                    }
                    for doc in source_documents
                ],
                "validation": {
                    "confidence_score": 0.0,
                    "total_sources": len(source_documents),
                    "restaurant_sources": 0,
                    "mentioned_restaurants": [],
                    "valid_mentions": [],
                    "invalid_mentions": [],
                    "has_potential_hallucination": False,
                    "used_fallback": True
                }
            }
    
    # Criar callback de monitoramento
    monitoring_callback = LLMMonitoringCallback(user_id=user_id, question=question)
    
    # Executar chain com callback de monitoramento
    try:
        answer = chain.invoke(question, config={"callbacks": [monitoring_callback]})
    except Exception as e:
        # Em caso de erro, registrar no callback
        monitoring_callback.on_llm_error(e)
        raise
    
    # Obter métricas do callback (passar resposta para cálculo correto de tamanho)
    metrics = monitoring_callback.get_metrics(response_text=answer)
    
    # Registrar métricas (salvar no banco e log)
    try:
        log_llm_metrics(metrics, db=db, save_to_db=True)
    except Exception as e:
        # Não falhar se houver erro ao salvar métricas
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.warning(f"Erro ao salvar métricas LLM: {e}")
    
    # Obter nome do usuário para limpeza
    user_name_for_cleaning = None
    if user_id and db:
        user = crud.get_user(db, user_id)
        if user:
            user_name_for_cleaning = user.name
    
    # Limpar resposta removendo frases proibidas e repetições
    answer = clean_answer(answer, user_name=user_name_for_cleaning, question=question)
    
    # Corrigir referências vagas a restaurantes ("Eles têm" sem mencionar o restaurante)
    answer = fix_vague_restaurant_references(answer, source_documents)
    
    # Validação adicional: verificar se a resposta está relacionada a comida/restaurantes
    answer_lower = answer.lower()
    food_keywords_in_answer = [
        "restaurante", "restaurantes", "comida", "prato", "pratos",
        "culinária", "culinaria", "cardápio", "cardapio", "menu",
        "pedido", "pedidos", "delivery", "entrega", "ifood",
        "pizza", "hambúrguer", "hamburguer", "massa", "massas",
        "japonês", "japones", "italiano", "brasileiro", "mexicano",
        "chines", "chinesa", "árabe", "arabe", "vegetariano",
        "vegano", "lanche", "lanches", "café", "cafe", "bebida",
        "sobremesa", "sobremesas", "almoço", "almoco", "jantar",
        "chef", "cozinha", "receita", "receitas", "ingrediente",
        "sabor", "gosto", "preferência", "preferencia", "recomendação",
        "recomendacao", "avaliação", "avaliacao", "rating", "nota",
        "preço", "preco", "valor", "barato", "caro", "promoção",
        "promocao", "desconto", "cupom", "tastematch", "gastronômico",
        "gastronomico", "culinário", "culinario", "prato do dia"
    ]
    
    # Palavras que indicam que a resposta está fora do escopo
    out_of_scope_indicators = [
        "passagem", "avião", "viagem", "viajar", "hotel", "turismo",
        "computador", "celular", "smartphone", "filme", "música", "banco",
        "aeroporto", "voo", "destino", "férias", "ferias", "país", "países",
        "gringa", "hospedagem", "netflix", "streaming", "show", "concerto"
    ]
    
    has_food_content = any(keyword in answer_lower for keyword in food_keywords_in_answer)
    has_out_of_scope_content = any(indicator in answer_lower for indicator in out_of_scope_indicators)
    
    # Se detectar conteúdo fora do escopo na resposta E não houver conteúdo sobre comida, substituir
    if has_out_of_scope_content and not has_food_content:
        answer = (
            "Desculpe, eu só ajudo com restaurantes e comida. "
            "Como posso ajudá-lo a encontrar um restaurante ou prato hoje?"
        )
    
    # Validar resposta contra o contexto e banco de dados
    validation = validate_answer_against_context(answer, source_documents, db=db)
    
    # Se detectar alucinação potencial, tomar ação mais rigorosa
    if validation["has_potential_hallucination"]:
        invalid_count = len(validation["invalid_mentions"])
        valid_count = len(validation["valid_mentions"])
        total_mentioned = len(validation["mentioned_restaurants"])
        
        # Se a maioria dos restaurantes mencionados são inválidos, substituir resposta
        if invalid_count > valid_count and total_mentioned > 0:
            # Remover menções inválidas da resposta ou substituir por resposta genérica
            answer = (
                "Alguns restaurantes mencionados não estão disponíveis no momento. "
                "Como posso ajudá-lo a encontrar um restaurante ou prato hoje?"
            )
        else:
            # Se apenas alguns são inválidos, adicionar aviso (mas verificar se já não existe)
            # Não adicionar aviso na resposta - já está no rodapé do frontend
            # O aviso foi movido para o rodapé fixo do componente
            pass
    
    # Adicionar ao histórico
    if user_id:
        add_to_conversation_history(user_id, question, answer, db=db, audio_url=audio_url)
    
    return {
        "answer": answer,
        "source_documents": [
            {
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
            }
            for doc in source_documents
        ],
        "validation": validation
    }


def detect_social_interaction(message: str) -> Optional[str]:
    """
    Detecta interações sociais (agradecimentos, saudações, despedidas) e retorna resposta natural
    
    Args:
        message: Mensagem do usuário
    
    Returns:
        Resposta natural se detectar interação social, None caso contrário
    """
    import random
    message_lower = message.lower().strip()
    words = message_lower.split()
    
    # Agradecimentos
    gratitude_keywords = [
        "obrigado", "obrigada", "obrigad", "valeu", "vlw", "vlws",
        "thanks", "thank you", "grato", "grata", "agradeço", "agradecida",
        "perfeito", "show", "top", "massa", "demais"
    ]
    
    # Saudações
    greeting_keywords = [
        "oi", "olá", "ola", "hey", "hi", "hello", "e aí", "eai",
        "bom dia", "bomdia", "boa tarde", "boatarde", "boa noite", "boanoite",
        "tudo bem", "tudobem", "td bem", "tdbem"
    ]
    
    # Despedidas
    farewell_keywords = [
        "tchau", "até", "ate", "falou", "flw", "bye", "goodbye",
        "até logo", "atelogo", "até mais", "atemais", "até breve", "atebreve"
    ]
    
    # Verificar agradecimentos
    gratitude_count = sum(1 for word in words if any(kw in word for kw in gratitude_keywords))
    if gratitude_count > 0:
        if "chef" in message_lower or any(kw in message_lower for kw in ["obrigado", "obrigada", "valeu", "perfeito"]):
            responses = [
                "De nada! Qualquer coisa, só chamar! 😊",
                "Por nada! Estou sempre aqui para ajudar!",
                "Disponha! Bom apetite! 🍽️",
                "Imagina! Foi um prazer ajudar!",
                "De nada! Aproveite sua refeição!",
                "Por nada! Se precisar de mais alguma coisa, é só falar!"
            ]
            return random.choice(responses)
    
    # Verificar saudações simples (sem pergunta)
    greeting_count = sum(1 for word in words if any(kw in word for kw in greeting_keywords))
    if greeting_count > 0 and len(words) <= 3:  # Saudações curtas
        # Verificar se não há pergunta junto
        question_indicators = ["?", "qual", "quais", "onde", "como", "quando", "quanto"]
        has_question = any(ind in message_lower for ind in question_indicators)
        
        if not has_question:
            # Respostas baseadas no horário (se possível) ou genéricas
            responses = [
                "Olá! Como posso ajudá-lo a encontrar um restaurante hoje?",
                "Oi! Em que posso ajudar com restaurantes e comida?",
                "Olá! Que tipo de comida você está procurando?",
                "Oi! Pronto para descobrir novos restaurantes?",
                "Olá! Como posso ajudá-lo hoje?"
            ]
            return random.choice(responses)
    
    # Verificar despedidas
    farewell_count = sum(1 for word in words if any(kw in word for kw in farewell_keywords))
    if farewell_count > 0 and len(words) <= 3:  # Despedidas curtas
        responses = [
            "Até logo! Bom apetite! 🍽️",
            "Tchau! Volte sempre!",
            "Até mais! Aproveite sua refeição!",
            "Tchau! Qualquer coisa, só chamar!",
            "Até logo! Espero ter ajudado!"
        ]
        return random.choice(responses)
    
    return None


def validate_question(question: str) -> tuple[bool, Optional[str]]:
    """
    Valida a pergunta e aplica guardrails básicos
    
    Args:
        question: Pergunta do usuário
    
    Returns:
        Tupla (é válida, mensagem de erro se inválida)
    """
    # Guardrails básicos
    inappropriate_keywords = [
        "hack", "exploit", "bypass", "crack",
        # Adicionar mais palavras se necessário
    ]
    
    # Palavras-chave que indicam perguntas fora do escopo (qualquer coisa que NÃO seja comida/restaurantes)
    out_of_scope_keywords = [
        # Viagens e turismo
        "passagem", "avião", "viagem", "viajar", "gringa", "país", "países",
        "turismo", "hotel", "hospedagem", "voo", "voos", "aeroporto",
        "destino", "turístico", "turística", "férias", "ferias",
        # Tecnologia e outros serviços
        "computador", "celular", "smartphone", "notebook", "laptop",
        "internet", "wi-fi", "wifi", "aplicativo", "app",
        # Entretenimento
        "filme", "cinema", "série", "serie", "netflix", "streaming",
        "música", "musica", "show", "concerto", "festival",
        # Outros serviços
        "banco", "cartão", "cartao", "crédito", "credito", "débito", "debito",
        "seguro", "plano de saúde", "medicina", "médico", "medico",
        "escola", "universidade", "curso", "aula", "estudar",
        "carro", "automóvel", "automovel", "moto", "bicicleta",
        "roupa", "moda", "vestido", "calça", "sapato",
        # Geral
        "outro assunto", "outra coisa", "qualquer coisa"
    ]
    
    # Palavras-chave relacionadas a comida/restaurantes (validação positiva)
    food_related_keywords = [
        "restaurante", "restaurantes", "comida", "prato", "pratos",
        "culinária", "culinaria", "cardápio", "cardapio", "menu",
        "pedido", "pedidos", "delivery", "entrega", "ifood",
        "pizza", "hambúrguer", "hamburguer", "massa", "massas",
        "japonês", "japones", "italiano", "brasileiro", "mexicano",
        "chines", "chinesa", "árabe", "arabe", "vegetariano",
        "vegano", "lanche", "lanches", "café", "cafe", "bebida",
        "sobremesa", "sobremesas", "almoço", "almoco", "jantar",
        "café da manhã", "cafe da manha", "breakfast", "brunch",
        "chef", "cozinha", "receita", "receitas", "ingrediente",
        "sabor", "gosto", "preferência", "preferencia", "recomendação",
        "recomendacao", "avaliação", "avaliacao", "rating", "nota",
        "preço", "preco", "valor", "barato", "caro", "promoção",
        "promocao", "desconto", "cupom", "cupom de desconto"
    ]
    
    question_lower = question.lower()
    
    # Verificar palavras inapropriadas
    for keyword in inappropriate_keywords:
        if keyword in question_lower:
            return False, "Desculpe, não posso ajudar com esse tipo de pergunta."
    
    # Verificar se a pergunta está fora do escopo
    for keyword in out_of_scope_keywords:
        if keyword in question_lower:
            return False, (
                "Desculpe, eu sou especializado APENAS em restaurantes, comida e alimentação. "
                "Não posso ajudar com outros assuntos como viagens, tecnologia, entretenimento, etc. "
                "Como posso ajudá-lo a encontrar um restaurante, prato ou receita hoje?"
            )
    
    # Validação positiva: verificar se a pergunta está relacionada a comida/restaurantes
    # Se não houver palavras relacionadas a comida, mas também não houver palavras fora do escopo,
    # ainda permitir (pode ser uma pergunta genérica que o LLM pode redirecionar)
    has_food_keyword = any(keyword in question_lower for keyword in food_related_keywords)
    
    # Verificar se a pergunta não está vazia
    if not question.strip():
        return False, "Por favor, faça uma pergunta sobre restaurantes, comida ou alimentação."
    
    # Verificar tamanho máximo
    if len(question) > 1000:
        return False, "Sua pergunta é muito longa. Por favor, seja mais conciso."
    
    return True, None

