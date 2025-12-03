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
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from typing import Any, Dict, List, Optional
from app.config import settings
from app.core.rag_service import RAGService
from app.core.recommender import extract_user_patterns, generate_recommendations
from app.core.prompt_versions import get_prompt_version_for_user
from app.core.llm_monitoring import LLMMonitoringCallback, log_llm_metrics
from app.core.query_expansion import expand_query_with_synonyms, should_expand_query
from app.core.response_cache import get_response_cache, should_cache_query
from app.database import crud
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ChatGroqFiltered(ChatGroq):
    """
    Wrapper robusto que intercepta chamadas ao cliente Groq para remover
    parâmetros não suportados (reasoning_format, reasoning_effort).
    
    Esta solução funciona interceptando no último momento possível (cliente Groq),
    garantindo que nenhum parâmetro não suportado chegue à API.
    
    Estratégia: Monkey patch no cliente + override em _generate para defense in depth.
    """
    
    def __init__(self, *args, **kwargs):
        """Inicializa o wrapper e aplica patch no cliente Groq."""
        super().__init__(*args, **kwargs)
        self._apply_client_patch()
    
    def _apply_client_patch(self):
        """
        Aplica patch no cliente Groq para filtrar parâmetros não suportados.
        
        Intercepta no nível do cliente (antes da requisição HTTP), garantindo
        que parâmetros problemáticos sejam removidos independente de onde foram
        adicionados no fluxo do LangChain.
        
        Nota: self.client já é groq.resources.chat.completions.Completions,
        então fazemos patch diretamente em self.client.create()
        """
        try:
            # Verificar se cliente existe e tem método create
            if not hasattr(self, 'client'):
                return
            
            if not hasattr(self.client, 'create'):
                return
            
            # Guardar referência do método original
            original_create = self.client.create
            
            # Wrapper que remove parâmetros problemáticos
            def filtered_create(*args, **kwargs):
                """
                Wrapper que filtra parâmetros não suportados antes de chamar API Groq.
                
                Lista de parâmetros não suportados pelo modelo llama-3.1-8b-instant:
                - reasoning_format: Parâmetro para modelos de reasoning (DeepSeek R1, etc)
                - reasoning_effort: Esforço de reasoning (não suportado em modelos básicos)
                """
                # Lista de parâmetros não suportados pelo modelo
                unsupported_params = ['reasoning_format', 'reasoning_effort']
                
                # Remover silenciosamente (sem log para evitar poluição)
                for param in unsupported_params:
                    kwargs.pop(param, None)
                
                # Chamar método original com kwargs limpos
                return original_create(*args, **kwargs)
            
            # Aplicar patch diretamente no método create do cliente
            self.client.create = filtered_create
            
            # Também fazer patch no async_client se existir
            if hasattr(self, 'async_client') and hasattr(self.async_client, 'create'):
                original_async_create = self.async_client.create
                
                async def filtered_async_create(*args, **kwargs):
                    """Wrapper async que também filtra parâmetros não suportados."""
                    unsupported_params = ['reasoning_format', 'reasoning_effort']
                    for param in unsupported_params:
                        kwargs.pop(param, None)
                    return await original_async_create(*args, **kwargs)
                
                self.async_client.create = filtered_async_create
                
        except Exception as e:
            # Log mas não falhar - se patch falhar, tentar continuar sem patch
            # O override em _generate ainda pode ajudar
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Erro ao aplicar patch no cliente Groq: {e}. "
                "Tentando continuar com override em _generate apenas."
            )
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Override adicional como camada extra de segurança (defense in depth).
        
        Remove parâmetros problemáticos também neste nível, caso o patch
        no cliente não tenha sido aplicado ou tenha falhado.
        """
        # Limpeza redundante (defense in depth)
        unsupported_params = ['reasoning_format', 'reasoning_effort']
        
        # Remover dos kwargs
        for param in unsupported_params:
            kwargs.pop(param, None)
        
        # Também limpar model_kwargs se existir
        if hasattr(self, 'model_kwargs') and self.model_kwargs:
            for param in unsupported_params:
                self.model_kwargs.pop(param, None)
        
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)


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

**⚠️ REGRA CRÍTICA DE CONTEXTO:**
- **FOQUE APENAS NA PERGUNTA ATUAL**: Analise a pergunta do usuário e responda SOMENTE a ela.
- **NÃO continue conversas anteriores**: Se o histórico mencionar outros assuntos ou perguntas antigas, IGNORE-OS completamente.
- **NÃO faça referências a mensagens antigas**: Responda como se esta fosse a primeira interação, baseando-se apenas na pergunta atual e no contexto disponível.
- **Se a pergunta atual for sobre "churrasco", responda sobre churrasco. Se for "oi" ou "tudo bem?", responda de forma breve e amigável, mas NÃO mencione ou continue assuntos de conversas anteriores.**

**REGRAS CRÍTICAS:**
- **CONTEXTO GEOGRÁFICO**: Estamos no Brasil. Priorize restaurantes brasileiros quando disponíveis.

- **DIRETRIZES DE RACIOCÍNIO (Protocolo Chef Resiliente)**:
  
  **🕵️‍♂️ ANÁLISE DE DADOS (RAG)**:
  - Verifique o campo "Contexto" abaixo.
  - **ATENÇÃO ESPECIAL**: Analise o campo "Tags e pratos relacionados" nos documentos de restaurantes.
  - Se o usuário pedir "Churrasco" e você encontrar um restaurante "Brasileira" com a tag "churrasco", ISSO É UM MATCH. Recomende-o!
  - Se houver restaurantes que atendam ao pedido: RECOMENDE-OS DIRETAMENTE.
  
  **🔄 GESTÃO DE EXPECTATIVA (Fallback)**:
  - Se o contexto estiver VAZIO: NÃO diga "não encontrei". Use conhecimento geral sobre o prato e sugira alternativas próximas.
  
  **🚫 REGRAS DE SEGURANÇA**:
  - JAMAIS invente nomes de restaurantes. Use estritamente os dados do Contexto.

- Se mencionar restaurantes específicos, use APENAS os nomes que aparecem EXATAMENTE no contexto ou nas recomendações.
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
- **QUANDO NÃO HÁ CONTEXTO ESPECÍFICO**: Se a pergunta for sobre comida/restaurantes mas não houver contexto relevante:
  - Responda de forma útil usando conhecimento geral sobre comida, culinária e restaurantes
  - Foque em tipos de culinária, pratos, ingredientes e dicas gastronômicas
  - NÃO invente nomes de restaurantes específicos
  - Seja honesto: "Não tenho informações sobre restaurantes específicos no momento, mas posso ajudar com [tipo de culinária/prato/dica relacionada]"
- **CRÍTICO**: Você NÃO responde perguntas sobre viagens, tecnologia, entretenimento, saúde, educação ou qualquer outro assunto fora de comida/restaurantes. Se perguntarem algo fora do escopo, responda: "Desculpe, eu sou especializado APENAS em restaurantes, comida e alimentação. Não posso ajudar com outros assuntos. Como posso ajudá-lo a encontrar um restaurante, prato ou receita hoje?"

Contexto:
{{context}}

⚠️ **REGRA CRÍTICA DE CONTEXTO:**
- FOQUE APENAS NA PERGUNTA ATUAL abaixo.
- NÃO continue conversas anteriores do histórico.
- Analise a pergunta e responda SOMENTE a ela, ignorando assuntos antigos.

Histórico (apenas referência - IGNORE se não relevante):
{{chat_history}}

**PERGUNTA ATUAL (RESPONDA APENAS A ESTA):**
{{question}}

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
- **DIRETRIZES DE RACIOCÍNIO (Protocolo Chef Resiliente)**:
  
  **🕵️‍♂️ ANÁLISE DE DADOS (RAG)**:
  - Verifique o campo "Contexto disponível" abaixo.
  - **ATENÇÃO ESPECIAL**: Analise o campo "Tags e pratos relacionados" nos documentos de restaurantes.
  - Se encontrar match via tags (ex: "churrasco" em restaurante brasileiro), recomende explicando a conexão!
  
  **🔄 GESTÃO DE EXPECTATIVA (Fallback)**:
  - Se o contexto estiver VAZIO: Use conhecimento geral sobre o prato e sugira alternativas próximas.
  - NÃO diga apenas "não encontrei". Seja consultivo e útil.
  
  **🚫 REGRAS DE SEGURANÇA**:
  - JAMAIS invente nomes de restaurantes. Use estritamente os dados do Contexto.

- Se mencionar restaurantes específicos, use apenas os que aparecem EXATAMENTE no contexto abaixo ou nas recomendações.
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
- **QUANDO NÃO HÁ CONTEXTO ESPECÍFICO**: Se a pergunta for sobre comida/restaurantes mas não houver contexto relevante:
  - Responda de forma útil usando conhecimento geral sobre comida, culinária e restaurantes
  - Foque em tipos de culinária, pratos, ingredientes e dicas gastronômicas
  - NÃO invente nomes de restaurantes específicos
  - Seja honesto: "Não tenho informações sobre restaurantes específicos no momento, mas posso ajudar com [tipo de culinária/prato/dica relacionada]"
- **CRÍTICO**: Eu NÃO respondo perguntas sobre viagens, tecnologia, entretenimento, saúde, educação ou qualquer outro assunto. Se o usuário perguntar algo fora do escopo, responda educadamente: "Desculpe, eu sou especializado APENAS em restaurantes, comida e alimentação. Não posso ajudar com outros assuntos. Como posso ajudá-lo a encontrar um restaurante, prato ou receita hoje?"

Contexto disponível:
{{context}}

⚠️ **FOQUE APENAS NA PERGUNTA ATUAL**: Analise a pergunta abaixo e responda SOMENTE a ela. NÃO continue conversas anteriores.

Nossa conversa anterior (apenas referência):
{{chat_history}}

**O que você quer saber AGORA:**
{{question}}

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

2. **DIRETRIZES DE RACIOCÍNIO (Protocolo Chef Resiliente)**:
   
   **🕵️‍♂️ ANÁLISE DE DADOS (RAG)**:
   - Verifique o campo "Contexto relevante" abaixo.
   - **ATENÇÃO ESPECIAL**: Analise o campo "Tags e pratos relacionados" nos documentos de restaurantes.
   - Se o usuário pedir "Churrasco" e você encontrar um restaurante "Brasileira" com a tag "churrasco" ou "carne grelhada", ISSO É UM MATCH. Recomende-o explicando a conexão!
   - Se houver restaurantes listados que atendam ao pedido: RECOMENDE-OS DIRETAMENTE, citando nome, avaliação e por que combina.
   - **FASE 3**: Use sinônimos e termos relacionados para fazer conexões inteligentes (ex: "rodízio" = "churrasco", "sushi" = "japonesa").
   
   **🔄 GESTÃO DE EXPECTATIVA (Fallback Estratégico)**:
   - Se o usuário pedir algo específico (ex: "Quero Churrasco") e o contexto estiver VAZIO ou irrelevante:
     - **NÃO DIGA** "Não encontrei nada" ou "Alguns restaurantes não estão disponíveis".
     - **DIGA**: "No momento, não tenho uma churrascaria tradicional listada na minha base direta..."
     - **AÇÃO EDUCATIVA**: Use seu conhecimento geral para comentar brevemente sobre o prato (ex: "Um bom churrasco pede uma picanha suculenta, certo?").
     - **AÇÃO CONSULTIVA**: Sugira a alternativa mais próxima disponível nas "Recomendações Personalizadas" ou no contexto geral (ex: "...mas vejo que o [Restaurante Y] tem ótimas opções de carnes grelhadas/pratos brasileiros que podem matar sua vontade.").
   
   **🎓 USO DE CONHECIMENTO GERAL**:
   - Você tem acesso a um manual interno sobre tipos de culinária (Brasileira, Italiana, etc.) no contexto estático.
   - Use essas informações para descrever *por que* uma recomendação é boa (ex: "Este prato usa cortes nobres, típico de um bom churrasco...").
   - Quando não há contexto específico, use conhecimento geral sobre comida, culinária e dicas gastronômicas para responder de forma útil.
   
   **🚫 REGRAS DE SEGURANÇA (Alucinação Zero)**:
   - Você pode usar conhecimento geral para falar sobre *comida* (ingredientes, cultura, tipos de culinária).
   - Você **JAMAIS** pode inventar nomes de *restaurantes* que não estejam no contexto ou nas recomendações fornecidas.

3. **SOBRE RESTAURANTES ESPECÍFICOS**: Se mencionar restaurantes específicos, use APENAS os nomes que aparecem EXATAMENTE no contexto fornecido ou nas recomendações. Se um restaurante não está no contexto, NÃO o mencione pelo nome, mas você pode falar sobre tipos de culinária, pratos e características gerais.
5. **RESPEITE O ORÇAMENTO DO USUÁRIO**: Não julgue ou condescenda sobre orçamento limitado. Sugira alternativas dentro do orçamento informado. Seja empático e respeitoso.
4. **FORMATAÇÃO VISUAL OBRIGATÓRIA** (quando recomendar restaurantes):
   - **CRÍTICO**: Você DEVE seguir EXATAMENTE este formato. NÃO invente variações.
   - **SEMPRE use separadores visuais**: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ entre restaurantes
   - **SEMPRE inclua emojis de culinária**: 🔥 (brasileira), 🍝 (italiana), 🍣 (japonesa), 🍔 (americana), etc.
   - **SEMPRE formate preço**: 💰💰💰 (R$ 80-120), 💰💰 (R$ 50-80), ou 💰 (R$ 20-50)
   - **SEMPRE inclua localização**: 📍 [localização] quando disponível no contexto
   - **SEMPRE adicione destaque único**: 🎯 [destaque específico do restaurante]
   - **SEMPRE mostre rating**: ⭐ [rating]/5.0 (use o rating do contexto, não invente)
   - **Formato OBRIGATÓRIO para cada restaurante** (copie exatamente):
     ```
     🔥 **Nome do Restaurante**
        ⭐ 4.8/5.0  |  💰💰💰 (R$ 80-120)  |  📍 Localização
        🎯 Destaque único do restaurante
        Descrição específica (2-3 linhas sobre o que torna este restaurante especial)
     
     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     
     🔥 **Outro Restaurante**
        ⭐ 4.5/5.0  |  💰💰 (R$ 50-80)  |  📍 Outra Localização
        🎯 Destaque único diferente
        Descrição específica diferente
     ```
   - **Máximo 2-3 restaurantes** por resposta
   - **Adicione comparação rápida** no final: 💡 **Comparação:** [breve comparação entre os restaurantes]
   - **IMPORTANTE**: Se o contexto já fornecer informações formatadas (com emojis, preços, etc.), USE-AS. Não reescreva de forma diferente.

5. **SEJA DIRETO, OBJETIVO E NATURAL**: 
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
6. **QUANDO NÃO HÁ CONTEXTO ESPECÍFICO**: Se a pergunta for sobre comida/restaurantes mas não houver contexto relevante:
   - Responda de forma útil usando conhecimento geral sobre comida, culinária e restaurantes
   - Foque em tipos de culinária, pratos, ingredientes e dicas gastronômicas
   - NÃO invente nomes de restaurantes específicos
   - Seja honesto: "Não tenho informações sobre restaurantes específicos no momento, mas posso ajudar com [tipo de culinária/prato/dica relacionada]"
   - Sempre mantenha o foco em comida e restaurantes
7. **SOBRE iFood**: Se perguntarem sobre iFood, use APENAS as informações que aparecem no contexto. Se não houver informações sobre iFood no contexto, responda de forma genérica sobre delivery de comida, mas NÃO invente características específicas.
8. **CRÍTICO - FORA DO ESCOPO**: Você NÃO pode e NÃO deve responder perguntas sobre:
   - Viagens, passagens, turismo, hotéis, aeroportos
   - Tecnologia, computadores, celulares, aplicativos (exceto apps de delivery)
   - Entretenimento, filmes, séries, música, shows
   - Serviços financeiros, bancos, cartões de crédito
   - Saúde, medicina, planos de saúde (exceto dietas e restrições alimentares)
   - Educação, escolas, cursos, universidades
   - Automóveis, transporte (exceto delivery)
   - Moda, roupas, acessórios
   - QUALQUER outro assunto que não seja relacionado a comida, restaurantes ou alimentação
   
9. **RESPOSTA PADRÃO PARA FORA DO ESCOPO**: Se o usuário perguntar algo fora do escopo, responda EXATAMENTE assim (sem variações):
   "Desculpe, eu sou especializado APENAS em restaurantes, comida e alimentação. Não posso ajudar com outros assuntos. Como posso ajudá-lo a encontrar um restaurante, prato ou receita hoje?"

**IMPORTANTE**: Se a pergunta não for sobre comida/restaurantes, você DEVE recusar educadamente e redirecionar para o seu escopo.

Contexto relevante:
{{context}}

⚠️ **REGRA CRÍTICA**: FOQUE APENAS NA PERGUNTA ATUAL. NÃO continue conversas anteriores do histórico.

Histórico da conversa (apenas referência - IGNORE se não relevante):
{{chat_history}}

**PERGUNTA ATUAL DO USUÁRIO (RESPONDA APENAS A ESTA):**
{{question}}

Resposta do Chef Virtual:"""
    
    return PromptTemplate(
        template=system_prompt,
        input_variables=["context", "chat_history", "question"]
    )


def get_conversation_history(
    user_id: int,
    db: Optional[Session] = None,
    max_messages: int = 4,  # REDUZIDO: Apenas últimas 2-3 interações (4 mensagens = 2 perguntas + 2 respostas)
    current_question: Optional[str] = None
) -> List:
    """
    Obtém histórico de conversa do usuário do banco de dados
    MELHORIA: Limita histórico e filtra mensagens irrelevantes
    
    Args:
        user_id: ID do usuário
        db: Sessão do banco de dados (opcional, se None retorna lista vazia)
        max_messages: Número máximo de mensagens a retornar (padrão: 4 = 2 interações)
        current_question: Pergunta atual (para filtrar histórico relevante)
    
    Returns:
        Lista de mensagens (HumanMessage, AIMessage) - apenas últimas interações relevantes
    """
    if not db:
        return []
    
    # Buscar mensagens recentes do banco (apenas últimas 2-3 interações)
    messages = crud.get_user_chat_messages_recent(db, user_id, limit=max_messages)
    
    if not messages:
        return []
    
    # Converter para formato LangChain (HumanMessage, AIMessage)
    langchain_messages = []
    
    # MELHORIA: Filtrar mensagens relevantes se temos pergunta atual
    if current_question:
        current_question_lower = current_question.lower().strip()
        
        # Detectar se é pergunta curta (cumprimento/saudação)
        short_greetings = ['oi', 'olá', 'ola', 'hey', 'hi', 'tudo bem', 'tudo bom', 'e aí', 'eai']
        is_short_greeting = (
            len(current_question_lower.split()) <= 3 and 
            any(greeting in current_question_lower for greeting in short_greetings)
        )
        
        # Para cumprimentos curtos, NÃO usar histórico (evitar continuar conversas antigas)
        if is_short_greeting:
            logger.debug(f"Pergunta curta detectada ('{current_question}') - não usando histórico")
            return []  # Retornar histórico vazio para cumprimentos
        
        # Para perguntas sobre comida, usar histórico filtrado
        # Palavras-chave da pergunta atual (apenas palavras significativas)
        current_keywords = set(word for word in current_question_lower.split() 
                              if len(word) > 3 and word not in ['quero', 'queria', 'gostaria', 'preciso'])
        
        # Incluir apenas mensagens que tenham alguma relação com a pergunta atual
        # OU que sejam muito recentes (última interação apenas)
        relevant_messages = []
        for i, msg in enumerate(reversed(messages)):  # Mais recentes primeiro
            # Para perguntas sobre comida, incluir apenas última interação (2 mensagens)
            # para contexto imediato, mas não mais que isso
            if i < 2:  # Apenas última pergunta + resposta
                relevant_messages.append(msg)
            # Para mensagens mais antigas, verificar relevância semântica
            elif current_keywords:
                msg_lower = msg.content.lower()
                # Se mensagem tem palavras-chave em comum, é relevante
                if any(keyword in msg_lower for keyword in current_keywords):
                    relevant_messages.append(msg)
                    break  # Parar após encontrar primeira mensagem relevante
        
        messages = list(reversed(relevant_messages))  # Voltar ordem cronológica
    
    # Converter para LangChain (ordem cronológica: mais antigas primeiro)
    for msg in reversed(messages):
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
    # Validar GROQ_API_KEY antes de criar LLM
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY não configurada. Configure no arquivo .env ou variáveis de ambiente."
        )
    
    # Obter LLM usando LangChain Groq com wrapper que filtra parâmetros não suportados
    # Usar modelo Llama mais antigo e estável que não envia reasoning_effort/reasoning_format
    # llama-3.1-8b-instant é mais estável e não tem esses problemas
    try:
        llm = ChatGroqFiltered(
            groq_api_key=settings.GROQ_API_KEY,
            model="llama-3.1-8b-instant",  # Modelo estável, sem problemas de reasoning params
            temperature=0.5  # Temperatura mais baixa para respostas mais diretas e objetivas
        )
    except Exception as e:
        raise ValueError(f"Erro ao criar ChatGroq: {str(e)}")
    
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
            # OTIMIZAÇÃO MEMÓRIA: Usar get_restaurants_metadata() que carrega apenas metadados essenciais
            # Reduz uso de memória em ~60-80% comparado a get_restaurants(limit=1000)
            restaurants = crud.get_restaurants_metadata(db, limit=500)  # Reduzido de 1000 para 500
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
    # FASE 2: Aumentado k de 10 para 15 para melhor recuperação de contexto
    retriever = rag_service.get_retriever(k=15)
    
    # Criar prompt com histórico e perfil completo do usuário
    system_prompt_text = create_chef_prompt_template(
        user_preferences=user_preferences,
        user_patterns=user_patterns,
        user_name=user_name,
        prompt_version=prompt_version,
        recommendations=recommendations
    ).template
    
    def format_docs(docs):
        """
        Formata documentos para o contexto, removendo duplicatas e formatando de forma concisa.
        
        PROTOCOLO CHEF RESILIENTE: Destaca tags semânticas para facilitar
        conexões entre perguntas do usuário e restaurantes disponíveis.
        MELHORIA UX/UI: Formatação visual moderna com separadores, preço formatado,
        localização e destaques únicos.
        """
        formatted = []
        seen_restaurants = set()  # Evitar duplicatas
        
        # Mapeamento de preço para texto formatado
        price_text_map = {
            "high": "💰💰💰 (R$ 80-120)",
            "medium": "💰💰 (R$ 50-80)",
            "low": "💰 (R$ 20-50)"
        }
        
        # Mapeamento de tipo de culinária para emoji
        cuisine_emoji_map = {
            "brasileira": "🔥",
            "italiana": "🍝",
            "japonesa": "🍣",
            "americana": "🍔",
            "mexicana": "🌮",
            "árabe": "🥙",
            "hamburgueria": "🍔",
            "pizzaria": "🍕"
        }
        
        for doc in docs:
            content = doc.page_content
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            # Adicionar informações de metadados se for restaurante
            if metadata.get('type') == 'restaurant':
                name = metadata.get('name', '').strip()
                
                # Pular se já vimos este restaurante
                if name and name.lower() in seen_restaurants:
                    continue
                
                if name:
                    seen_restaurants.add(name.lower())
                    cuisine = metadata.get('cuisine_type', '')
                    keywords = metadata.get('keywords', '')
                    rating = metadata.get('rating', '')
                    price_range = metadata.get('price_range', '')
                    location = metadata.get('location', '')
                    
                    # Emoji identificador por tipo de culinária
                    cuisine_lower = cuisine.lower() if cuisine else ''
                    emoji = cuisine_emoji_map.get(cuisine_lower, "🍽️")
                    
                    # Formato profissional e conciso com melhor hierarquia visual
                    header_parts = [f"{emoji} **{name}**"]
                    
                    # Linha de metadados (rating, preço, localização)
                    meta_parts = []
                    if rating:
                        meta_parts.append(f"⭐ {rating}/5.0")
                    if price_range and price_range in price_text_map:
                        meta_parts.append(price_text_map[price_range])
                    elif price_range:
                        price_emoji = "💰" if price_range == "high" else "💵" if price_range == "medium" else "💸"
                        meta_parts.append(price_emoji)
                    if location:
                        meta_parts.append(f"📍 {location}")
                    
                    # Destaque único (será gerado pelo LLM, mas fornecemos contexto)
                    highlight = get_restaurant_highlight(metadata)
                    
                    # CORREÇÃO: NÃO usar page_content diretamente (contém formato técnico)
                    # Usar description do metadata ou gerar descrição baseada em metadados
                    description_for_context = metadata.get('description', '').strip()
                    
                    # Se não houver description, gerar baseada em metadados
                    if not description_for_context or len(description_for_context) < 20:
                        cuisine = metadata.get('cuisine_type', '')
                        if cuisine:
                            description_for_context = f"Restaurante especializado em {cuisine}"
                            keywords = metadata.get('keywords', '')
                            if keywords:
                                first_keyword = keywords.split(',')[0].strip()
                                if first_keyword and len(first_keyword) < 30:
                                    description_for_context += f" com foco em {first_keyword}"
                    
                    # Limitar a 120 caracteres para contexto
                    if description_for_context:
                        content_preview = description_for_context[:120].strip()
                        if len(description_for_context) > 120:
                            content_preview += "..."
                    else:
                        # Fallback: usar apenas nome e tipo de culinária
                        content_preview = f"Restaurante {name}"
                        if cuisine:
                            content_preview += f" especializado em {cuisine}"
                    
                    # Montar formato completo
                    formatted_doc = f"{header_parts[0]}"
                    if meta_parts:
                        formatted_doc += f"\n   {'  |  '.join(meta_parts)}"
                    if highlight:
                        formatted_doc += f"\n   🎯 {highlight}"
                    if keywords:
                        formatted_doc += f"\n   • Tags: {keywords}"
                    formatted_doc += f"\n   {content_preview}"
                    
                    formatted.append(formatted_doc)
                else:
                    formatted.append(content)
            else:
                formatted.append(content)
        
        # Separar com separadores visuais
        return "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n".join(formatted)
    
    # Criar chain usando LCEL
    # Ajustar para receber question como string diretamente
    def create_input_dict(query: str):
        try:
            logger.debug(f"Buscando documentos no RAG para: '{query[:100]}...'")
            docs = retriever.invoke(query)
            logger.debug(f"Documentos recuperados pelo retriever: {len(docs)}")
            
            context = format_docs(docs)
            # MELHORIA: Passar pergunta atual para filtrar histórico relevante
            chat_history = get_conversation_history(user_id or 0, db=db, current_question=query)
            
            logger.debug(f"Contexto formatado: {len(context)} caracteres")
            logger.debug(f"Histórico de conversa: {len(chat_history)} mensagens (filtrado para relevância)")
            
            return {
                "context": context,
                "question": query,
                "chat_history": chat_history
            }
        except Exception as e:
            import traceback
            logger.error(f"Erro em create_input_dict: {type(e).__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Retornar valores vazios para não quebrar a chain
            return {
                "context": "",
                "question": query,
                "chat_history": []
            }
    
    chain = (
        RunnablePassthrough() | create_input_dict
        | ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt_text),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}\n\n**CONTEXTO DISPONÍVEL:**\n{context}\n\n**INSTRUÇÕES CRÍTICAS DE FORMATAÇÃO**: \n\n1. **USE O FORMATO EXATO DO CONTEXTO**: Se o contexto já mostra restaurantes formatados com emojis (🔥, 🍝, etc.), preços (💰💰💰), localização (📍) e destaques (🎯), COPIE ESSE FORMATO EXATAMENTE.\n\n2. **FORMATO OBRIGATÓRIO para cada restaurante**:\n   ```\n   🔥 **Nome do Restaurante**\n      ⭐ [rating]/5.0  |  💰💰💰 (R$ 80-120)  |  📍 [localização]\n      🎯 [destaque único]\n      [descrição específica 2-3 linhas]\n   \n   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n   ```\n\n3. **VALIDAÇÃO SEMÂNTICA RIGOROSA**: Só recomende restaurantes que tenham tags/características que correspondam EXATAMENTE ao que foi pedido. Se o usuário pedir 'churrasco', só recomende restaurantes com tags 'churrasco', 'rodízio', 'churrascaria' ou 'picanha'. NÃO invente características.\n\n4. **Máximo 2-3 restaurantes**. Adicione comparação rápida no final: 💡 **Comparação:** [breve comparação].\n\n5. **NÃO repita descrições genéricas. Diferencie claramente cada restaurante. NÃO use frases vagas. Vá direto ao ponto. Seja objetivo, profissional e moderno.**"),
        ])
        | llm
        | StrOutputParser()
    )
    
    return chain


def get_restaurant_highlight(restaurant_metadata: dict) -> str:
    """
    Gera destaque único baseado em características do restaurante.
    
    Args:
        restaurant_metadata: Dicionário com metadados do restaurante
    
    Returns:
        String com destaque único ou vazio se não houver
    """
    name = restaurant_metadata.get('name', '').strip().lower()
    keywords = restaurant_metadata.get('keywords', '').lower()
    cuisine = restaurant_metadata.get('cuisine_type', '').lower()
    
    # Mapeamento de nomes conhecidos para destaques específicos
    name_highlights = {
        'fogo de chão': 'Melhor picanha da região',
        'barbacoa': 'Tradição gaúcha autêntica',
        'churrascaria gaúcha': 'Churrasco gaúcho tradicional',
        'bovinus': 'Rodízio premium com cortes especiais',
        'rodeio grill': 'Ambiente descontraído e acolhedor',
        'outback steakhouse': 'Carnes grelhadas premium',
        'coco bambu': 'Frutos do mar frescos',
        'sushi house': 'Sushi artesanal de qualidade',
        'cantina italiana': 'Massas caseiras e vinhos selecionados',
        'papa john\'s': 'Pizzas artesanais',
        'habib\'s': 'Comida árabe autêntica',
        'viena': 'Comida brasileira tradicional',
        'giraffas': 'Comida brasileira rápida e saborosa',
        'casa do pão de queijo': 'Pães de queijo e café mineiro',
        'popeyes': 'Frango frito estilo Louisiana',
        'kfc': 'Frango frito crocante',
        'taco bell': 'Comida mexicana rápida',
        'bob\'s': 'Hambúrgueres e milkshakes',
    }
    
    # Verificar se há destaque específico para o nome
    if name in name_highlights:
        return name_highlights[name]
    
    # Fallback baseado em keywords
    if keywords:
        keyword_highlights = {
            'rodízio': 'Rodízio completo premium',
            'picanha': 'Picanha especial',
            'churrasco': 'Churrasco autêntico',
            'churrascaria': 'Churrascaria tradicional',
            'sushi': 'Sushi artesanal',
            'pizza': 'Pizzas artesanais',
            'hamburguer': 'Hambúrgueres gourmet',
            'massa': 'Massas caseiras',
            'frutos do mar': 'Frutos do mar frescos',
            'feijoada': 'Feijoada tradicional',
        }
        
        for keyword, highlight in keyword_highlights.items():
            if keyword in keywords:
                return highlight
    
    # Fallback baseado em tipo de culinária
    if cuisine:
        cuisine_highlights = {
            'brasileira': 'Culinária brasileira autêntica',
            'italiana': 'Culinária italiana tradicional',
            'japonesa': 'Culinária japonesa autêntica',
            'americana': 'Culinária americana',
            'mexicana': 'Culinária mexicana tradicional',
            'árabe': 'Culinária árabe autêntica',
        }
        
        if cuisine in cuisine_highlights:
            return cuisine_highlights[cuisine]
    
    # Retornar vazio se não houver destaque específico
    # O LLM pode gerar um destaque baseado no contexto
    return ''


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
    
    common_dishes = {
        'pizza', 'sushi', 'churrasco', 'acarajé', 'feijoada', 'hambúrguer', 
        'massa', 'taco', 'burrito', 'frango frito', 'pão de queijo', 'coxinha',
        'pastel', 'esfiha', 'kibe', 'falafel', 'shawarma', 'paella', 'risoto',
        'lasanha', 'nhoque', 'ravioli', 'tempura', 'yakisoba', 'sashimi',
        'temaki', 'poke', 'galeto', 'picanha', 'costela', 'moqueca', 'vatapá',
        'acaraje', 'feijoada', 'hamburguer', 'massa', 'frango frito', 'pao de queijo',
        'esfiha', 'kibe', 'risoto', 'lasanha', 'nhoque', 'yakisoba', 'sashimi',
        'temaki', 'poke', 'galeto', 'picanha', 'costela', 'moqueca', 'vatapa'
    }
    
    # Filtrar pratos comuns que não devem ser tratados como restaurantes
    final_names = []
    for name in unique_names:
        name_lower = name.lower().strip()
        if name_lower not in common_dishes:
            final_names.append(name)
            
    return final_names


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
    # OTIMIZAÇÃO MEMÓRIA: Usar get_restaurants_metadata() que carrega apenas metadados (não descrições)
    all_restaurant_names = set()
    if db:
        try:
            restaurants = crud.get_restaurants_metadata(db, limit=500)  # Reduzido de 1000 para 500
            for restaurant in restaurants:
                restaurant_name = restaurant.get('name') if isinstance(restaurant, dict) else restaurant.name
                all_restaurant_names.add(restaurant_name.lower())
                all_restaurant_names.add(restaurant_name.lower().replace('ã', 'a').replace('õ', 'o'))
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


def clean_markdown_artifacts(text: str) -> str:
    """
    Remove artefatos de markdown e tokens de conexão soltos deixados pelo LLM.
    Sanitização agressiva para garantir base limpa antes de qualquer processamento.
    
    Args:
        text: Texto a ser limpo
    
    Returns:
        Texto limpo sem artefatos
    """
    import re
    
    if not text:
        return text
    
    # 1. Remove "🔥 de", "🔥 é", etc. em QUALQUER lugar (não só no início)
    # Melhorado: captura com/sem espaço antes do emoji
    text = re.sub(r'(?i)(?:^|\s)[🔥🍝🍣🍔🍕🌮🥙🦞]\s+(de|é|tem|oferece|do|da|dos|das)\s+', ' ', text)
    
    # 2. Remove padrão "🔥 ****" (emoji + espaço + asteriscos)
    text = re.sub(r'[🔥🍝🍣🍔🍕🌮🥙🦞]\s+\*{3,}', '', text)
    
    # 3. Remove asteriscos soltos (3+ asteriscos consecutivos, como ****)
    text = re.sub(r'\*{3,}', '', text)
    
    # 4. Remove linhas que contêm apenas um emoji solto
    text = re.sub(r'^\s*[🔥🍝🍣🍔🍕🌮🥙🦞]\s*$', '', text, flags=re.MULTILINE)
    
    # 5. Remove texto introdutório verboso comum do LLM
    # Padrões como "No entanto, posso sugerir...", "📄 visitar...", "⬆️ 💥"
    # CORREÇÃO CRÍTICA: Remover frases genéricas sobre pratos/culinária
    verbose_intro_patterns = [
        r'(?i)^\s*\*\*\s*No\s+entanto[^.]*\.\s*',
        r'(?i)^\s*No\s+entanto[^.]*\.\s*',
        r'(?i)No\s+entanto,\s+posso\s+sugerir[^.]*\.\s*',
        r'(?i)No\s+entanto,\s+posso\s+recomendar[^.]*\.\s*',
        r'(?i)posso\s+sugerir\s+algumas\s+alternativas\s+próximas[^.]*\.\s*',
        r'(?i)posso\s+sugerir\s+algumas\s+alternativas[^.]*\.\s*',
        r'(?i)Se\s+você\s+estiver\s+procurando\s+por\s+algo\s+semelhante[^.]*\.\s*',
        r'(?i)eu\s+recomendaria\s+o\s+de\s+ou\s+a[^.]*\.\s*',
        r'(?i)recomendaria\s+o\s+de\s+ou\s+a[^.]*\.\s*',
        r'(?i)recomendaria\s+o\s+de[^.]*\.\s*',
        r'(?i)recomendaria\s+a\s+de[^.]*\.\s*',
        r'(?i)^\s*posso\s+sugerir[^.]*\.\s*',
        r'📄\s+visitar[^.]*\.\s*',
        r'⬆️\s*💥\s*',
        r'💥\s*\*\*',
        r'(?i)algumas\s+opções\s+que\s+podem\s+ser\s+úteis[^.]*\.\s*',
        r'(?i)restaurantes\s+listados\s+abaixo[^.]*\.\s*',
        # NOVO: Remover frases genéricas sobre pratos/culinária
        r'(?i)^\s*[A-Z][^.!?]*\s+(é|são)\s+um\s+(prato|pratos|tipo|tipos)[^.!?]*delicioso[^.!?]*!?\s*',
        r'(?i)^\s*[A-Z][^.!?]*\s+(é|são)\s+um\s+(prato|pratos|tipo|tipos)[^.!?]*tradicional[^.!?]*!?\s*',
        r'(?i)^\s*[A-Z][^.!?]*\s+(é|são)\s+um\s+(prato|pratos|tipo|tipos)[^.!?]*brasileiro[^.!?]*!?\s*',
        # Exemplo específico: "Churrasco é um prato delicioso e tradicional brasileiro!"
        r'(?i)^\s*churrasco\s+é\s+um\s+prato[^.!?]*!?\s*',
        r'(?i)^\s*pizza\s+é\s+um\s+prato[^.!?]*!?\s*',
        r'(?i)^\s*sushi\s+é\s+um\s+prato[^.!?]*!?\s*',
    ]
    for pattern in verbose_intro_patterns:
        text = re.sub(pattern, '', text, flags=re.MULTILINE)
    
    # 6. Remove emojis soltos no início de linhas que não fazem parte de cards
    # Mas preserva emojis que estão antes de nomes em negrito (cards válidos)
    text = re.sub(r'^(?![🔥🍝🍣🍔🍕🌮🥙🦞]\s+\*\*)[🔥🍝🍣🍔🍕🌮🥙🦞]\s+', '', text, flags=re.MULTILINE)
    
    # 6.1. Remove emojis soltos em linhas vazias ou isolados (incluindo ⭐)
    text = re.sub(r'^\s*[🔥🍝🍣🍔🍕🌮🥙🦞⭐]\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[🔥🍝🍣🍔🍕🌮🥙🦞⭐]\s*\n', '', text, flags=re.MULTILINE)
    
    # 7. Corrige espaçamento duplo gerado após remoções
    text = re.sub(r'\s{2,}', ' ', text)
    
    # 8. Remove espaços no início e fim de linhas
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
    
    # 9. Limpar linhas vazias excessivas
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def clean_technical_metadata(text: str) -> str:
    """
    Remove agressivamente metadados técnicos e artefatos de RAG que vazaram para a resposta.
    FASE 2: Regex expandida e mais agressiva para capturar todos os padrões.
    
    Args:
        text: Texto a ser limpo
    
    Returns:
        Texto limpo sem metadados técnicos
    """
    import re
    
    if not text:
        return text
    
    # Lista expandida de padrões técnicos (Case Insensitive + Multiline)
    technical_patterns = [
        r'Restaurante:\s*.*$',                              # "Restaurante: ..."
        r'Tipo de culinária:\s*.*$',                        # "Tipo de culinária: ..."
        r'e pratos relacionados:\s*.*$',                    # "e pratos relacionados: ..."
        r'Tags(?:\s*e\s*pratos\s*relacionados)?:\s*.*$',  # "Tags:" ou "Tags e pratos relacionados:"
        r'Avaliação:\s*.*$',                                # "Avaliação: ..."
        r'Faixa de preço:\s*.*$',                           # "Faixa de preço: ..."
        r'Descrição:\s*.*$',                                # "Descrição: ..."
        r'Source:\s*.*$',                                   # Artefatos LangChain
        r'Metadata:\s*\{.*?\}',                            # JSON cru
        r'Localização:\s*.*$',                              # "Localização: ..."
        r'\*\*[\d/.]+\*+',                                  # Remove padrões de score de confiança vazados (ex: **5/5.8/5.)
    ]
    
    cleaned_text = text
    
    # Aplicar remoção para cada padrão
    for pattern in technical_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Limpar espaços em branco excessivos (3+ quebras de linha → 2)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    return cleaned_text.strip()


def is_structurally_valid(text: str) -> bool:
    """
    Validação estrita: resposta só é aceita se estruturalmente perfeita.
    Qualquer dúvida = False (força pós-processamento).
    
    Args:
        text: Texto a ser validado
    
    Returns:
        True se estrutura está perfeita, False caso contrário
    """
    import re
    
    # 1. Deve ter separadores claros
    has_separators = '━━' in text or '━━━' in text
    
    # 2. Deve ter nomes em negrito logo após emojis ou no início de linhas
    has_bold_names = bool(re.search(
        r'(?:^|\n)\s*[🔥🍝🍣🍔🍕🌮🥙]\s+\*\*[^*]+\*\*', 
        text, 
        re.MULTILINE
    ))
    
    # 3. NÃO deve ter artefatos óbvios (verificar em QUALQUER lugar, não só no início)
    has_artifacts = (
        '****' in text or 
        re.search(r'[🔥🍝🍣🍔🍕🌮🥙]\s+(de|é|tem|oferece)\s+', text, re.IGNORECASE) or
        re.search(r'[🔥🍝🍣🍔🍕🌮🥙]\s+\*{3,}', text) or
        re.search(r'\*{3,}', text)
    )
    
    # 4. Deve ter estrutura consistente: emoji + nome + metadados
    has_consistent_structure = bool(re.search(
        r'[🔥🍝🍣🍔🍕🌮🥙]\s+\*\*[^*]+\*\*\s*\n\s*[⭐💰📍🎯]', 
        text, 
        re.MULTILINE
    ))
    
    return has_separators and has_bold_names and not has_artifacts and has_consistent_structure


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
        # Erros de português e textos incompletos
        r'\bNo entanto,\s+posso\s+sugerir\b',
        r'\bposso\s+sugerir\s+algumas\s+alternativas\s+próximas\b',
        r'\bSe\s+você\s+estiver\s+procurando\s+por\s+algo\s+semelhante\b',
        r'\beu\s+recomendaria\s+o\s+de\s+ou\s+a\b',
        r'\brecomendaria\s+o\s+de\s+ou\s+a\b',
        r'\brecomendaria\s+o\s+de\b',
        r'\brecomendaria\s+a\s+de\b',
        r'\brecomendaria\s+o\s+de\s+ou\b',
        # Textos incompletos/gramaticalmente incorretos
        r'\b\.\s*Se\s+você\s+estiver\s+procurando[^.]*\.\s*',
        r'\b\.\s*eu\s+recomendaria\s+o\s+de[^.]*\.\s*',
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
    
    # Remover repetições de restaurantes mencionados
    restaurant_mentions = {}
    restaurant_pattern = r'\*\*([^*]+)\*\*'  # Padrão para **Nome do Restaurante**
    
    def replace_duplicate(match):
        name = match.group(1).strip()
        name_lower = name.lower()
        if name_lower not in restaurant_mentions:
            restaurant_mentions[name_lower] = name
            return match.group(0)  # Manter primeira menção
        return ''  # Remover duplicatas
    
    # Remover menções duplicadas de restaurantes
    answer = re.sub(restaurant_pattern, replace_duplicate, answer)
    
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
    
    # Preservar separadores visuais (━━━) antes de limpar espaços
    # Dividir resposta em partes (separadores e conteúdo)
    separator_pattern = r'(━{10,})'  # Padrão para separadores
    parts = re.split(separator_pattern, answer)
    preserved_parts = []
    
    for i, part in enumerate(parts):
        if re.match(separator_pattern, part):
            # É um separador, preservar
            preserved_parts.append(part)
        else:
            # É conteúdo, limpar espaços
            cleaned_part = re.sub(r'\s+', ' ', part)
            cleaned_part = re.sub(r'\s+([.,!?])', r'\1', cleaned_part)
            cleaned_part = re.sub(r'([.,!?])\s*\1+', r'\1', cleaned_part)
            preserved_parts.append(cleaned_part)
    
    answer = ''.join(preserved_parts).strip()
    
    # Limitar tamanho da resposta (máximo 500 caracteres para ser conciso)
    # Mas preservar separadores se possível
    if len(answer) > 500:
        # Encontrar último ponto antes de 500 caracteres
        last_period = answer.rfind('.', 0, 500)
        if last_period > 300:  # Se encontrou ponto razoável
            answer = answer[:last_period + 1]
        else:
            # Se não encontrou, cortar em 500 e adicionar "..."
            answer = answer[:497] + "..."
    
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
    
    FASE 3: Implementa cache de respostas para perguntas comuns.
    
    Args:
        question: Pergunta do usuário
        rag_service: Instância do RAGService
        user_id: ID do usuário (opcional)
        db: Sessão do banco de dados (opcional)
        audio_url: URL do áudio (opcional)
    
    Returns:
        Dicionário com resposta, metadados e validação
    """
    # CRÍTICO: Detectar interações sociais (cumprimentos, agradecimentos) ANTES de buscar RAG
    # Se for cumprimento, retornar resposta simples sem buscar documentos
    social_response = detect_social_interaction(question)
    if social_response:
        logger.info(f"Interação social detectada: '{question}' → resposta direta")
        return {
            "answer": social_response,
            "audio_url": None,
            "sources": [],
            "validation": {
                "confidence_score": 1.0,
                "error": False,
                "error_message": None
            }
        }
    
    # FASE 3: Verificar cache antes de processar
    cache = get_response_cache()
    if should_cache_query(question):
        cached_response = cache.get(question, user_id=user_id)
        if cached_response:
            logger.info(f"Resposta retornada do CACHE para: '{question[:50]}...'")
            return cached_response
    
    # Criar chain
    chain = create_chef_chain(rag_service, user_id, db)
    
    # Decidir qual tipo de busca usar
    question_lower = question.lower()
    
    # Usar Hybrid Search se:
    # 1. Pergunta menciona "restaurante" ou "restaurantes"
    # 2. Pergunta contém palavras que podem ser nomes de restaurantes (palavras com mais de 3 letras)
    # 3. Pergunta pede algo específico (ex: "McDonald's", "pizza", "italiano")
    # FASE 2: Expansão de Query com Sinônimos
    expanded_question = question
    if should_expand_query(question):
        expanded_question = expand_query_with_synonyms(question, max_expansions=3)
        logger.info(f"Query expandida: '{question}' → '{expanded_question}'")
    
    use_hybrid = (
        'restaurante' in question_lower or 
        'restaurantes' in question_lower or
        'disponíveis' in question_lower or
        any(len(word) > 3 for word in question_lower.split())  # Possível nome de restaurante
    )
    
    # FASE 2: Aumentado k de 8 para 15 para melhor recuperação de contexto
    # CORREÇÃO: Filtrar e priorizar por correspondência semântica rigorosa
    try:
        if use_hybrid:
            # Usar busca híbrida (exata + semântica) com query expandida
            logger.info(f"Usando busca híbrida para: '{expanded_question[:100]}...'")
            source_documents = rag_service.hybrid_search(expanded_question, k=20, exact_weight=0.7, semantic_weight=0.3)  # Mais peso para busca exata
        else:
            # Usar apenas busca semântica com query expandida
            logger.info(f"Usando busca semântica para: '{expanded_question[:100]}...'")
            source_documents = rag_service.similarity_search(expanded_question, k=20)
        
        # Guardar documentos originais antes do filtro (para fallback se necessário)
        original_docs_before_filter = source_documents.copy() if source_documents else []
        
        # FILTRO CRÍTICO: Validar correspondência semântica rigorosa
        question_lower = question.lower()
        filtered_documents = []
        
        # Palavras-chave específicas da pergunta
        # Filtrar stopwords mais agressivamente
        stopwords = {'quero', 'queria', 'gostaria', 'preciso', 'um', 'uma', 'uns', 'umas', 'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'nas', 'nos', 'para', 'com', 'sem', 'por', 'sobre'}
        question_keywords = set()
        for word in question_lower.split():
            # Ignorar stopwords e palavras muito curtas
            if len(word) > 3 and word not in stopwords:
                question_keywords.add(word)
        
        # Mapeamento de palavras-chave para tags relevantes
        # CORREÇÃO: Separar tags específicas (obrigatórias) de tags genéricas (opcionais)
        keyword_to_specific_tags = {
            'churrasco': ['churrasco', 'rodízio', 'picanha', 'churrascaria', 'carne grelhada', 'espetinho'],
            'pizza': ['pizza', 'massa'],
            'sushi': ['sushi', 'sashimi', 'temaki'],
            'hamburguer': ['hamburguer', 'burger', 'hamburgueria'],
            'feijoada': ['feijoada'],
            'risoto': ['risoto'],
            'açaí': ['açaí', 'acai', 'açai', 'sorvete', 'gelato'],
            'acai': ['açaí', 'acai', 'açai', 'sorvete', 'gelato'],
            'açai': ['açaí', 'acai', 'açai', 'sorvete', 'gelato'],
        }
        
        # Tags genéricas (culinárias) - só aceitar se correspondência direta
        keyword_to_cuisine_tags = {
            'italiana': ['italiana'],
            'japonesa': ['japonesa'],
            'brasileira': ['brasileira'],
            'mexicana': ['mexicana'],
            'chinesa': ['chinesa'],
        }
        
        # Identificar se a query é específica (prato) ou genérica (culinária)
        is_specific_query = any(kw in keyword_to_specific_tags for kw in question_keywords)
        is_cuisine_query = any(kw in keyword_to_cuisine_tags for kw in question_keywords)
        
        # Expandir palavras-chave com tags relevantes
        specific_tags = set()
        cuisine_tags = set()
        
        for keyword in question_keywords:
            if keyword in keyword_to_specific_tags:
                specific_tags.update(keyword_to_specific_tags[keyword])
            if keyword in keyword_to_cuisine_tags:
                cuisine_tags.update(keyword_to_cuisine_tags[keyword])
            # Adicionar palavra original apenas se for relevante (não stopword genérica)
            # CORREÇÃO: Não adicionar palavras genéricas como "gourmet", "bom", "melhor" que podem causar matches incorretos
            generic_words = {'gourmet', 'bom', 'melhor', 'melhores', 'ótimo', 'otimo', 'excelente', 'top', 'show'}
            if keyword not in ['quero', 'queria', 'gostaria', 'preciso'] and keyword not in generic_words:
                # Só adicionar se não estiver no mapeamento (para evitar duplicatas)
                if keyword not in keyword_to_specific_tags and keyword not in keyword_to_cuisine_tags:
                    specific_tags.add(keyword)
        
        logger.debug(f"Query específica: {is_specific_query}, Query culinária: {is_cuisine_query}")
        logger.debug(f"Tags específicas para '{question}': {specific_tags}")
        logger.debug(f"Tags culinárias para '{question}': {cuisine_tags}")
        
        # Filtrar documentos por correspondência de tags (FILTRO RIGOROSO)
        for doc in source_documents:
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            
            if metadata.get('type') == 'restaurant':
                # Verificar tags do restaurante
                keywords = metadata.get('keywords', '').lower()
                cuisine = metadata.get('cuisine_type', '').lower()
                name = metadata.get('name', '').lower()
                description = (metadata.get('description', '') or '').lower()
                
                # Verificar correspondência
                has_match = False
                match_reason = []
                
                # PRIORIDADE 1: Verificar keywords (mais específico)
                if keywords:
                    # Melhorar parsing de keywords (pode ter vírgula ou espaço)
                    doc_tags = set([t.strip() for t in keywords.replace(',', ' ').split() if len(t.strip()) > 2])
                    keyword_match = specific_tags & doc_tags
                    if keyword_match:
                        has_match = True
                        match_reason.append(f"keywords: {keyword_match}")
                    
                    # MELHORIA: Também verificar correspondência parcial (ex: "churrasco" em "churrascaria")
                    # CORREÇÃO: Ser mais restritivo - apenas tags principais, não palavras genéricas
                    if not has_match and is_specific_query:
                        # Apenas verificar tags principais do mapeamento, não palavras genéricas como "gourmet"
                        main_tags = set()
                        for kw in question_keywords:
                            if kw in keyword_to_specific_tags:
                                main_tags.update(keyword_to_specific_tags[kw])
                        
                        for tag in main_tags:  # Apenas tags principais
                            if any(tag in kw or kw in tag for kw in doc_tags):
                                has_match = True
                                match_reason.append(f"keywords parcial: {tag}")
                                break
                
                # PRIORIDADE 2: Verificar nome (para casos específicos como "Churrascaria X")
                # CORREÇÃO: Usar apenas tags principais do mapeamento, não palavras genéricas
                if name and not has_match:
                    # Apenas tags principais do mapeamento
                    main_tags = set()
                    for kw in question_keywords:
                        if kw in keyword_to_specific_tags:
                            main_tags.update(keyword_to_specific_tags[kw])
                    
                    name_match = [tag for tag in main_tags if tag in name]
                    if name_match:
                        has_match = True
                        match_reason.append(f"nome: {name_match}")
                
                # PRIORIDADE 3: Verificar descrição (se contém tags específicas)
                # CORREÇÃO: Usar apenas tags principais do mapeamento
                if description and is_specific_query and not has_match:
                    # Apenas tags principais do mapeamento
                    main_tags = set()
                    for kw in question_keywords:
                        if kw in keyword_to_specific_tags:
                            main_tags.update(keyword_to_specific_tags[kw])
                    
                    desc_match = [tag for tag in main_tags if tag in description]
                    if desc_match:
                        has_match = True
                        match_reason.append(f"descrição: {desc_match}")
                
                # PRIORIDADE 4: Verificar tipo de culinária (APENAS se correspondência direta)
                # CORREÇÃO CRÍTICA: Se query é específica (churrasco), NÃO aceitar apenas por culinária genérica
                if cuisine:
                    # Se é query de culinária (ex: "italiana"), aceitar correspondência direta
                    if is_cuisine_query and cuisine in cuisine_tags:
                        has_match = True
                        match_reason.append(f"culinária direta: {cuisine}")
                    # Se é query específica (ex: "churrasco"), NÃO aceitar apenas por "brasileira"
                    # Só aceitar se também tiver keywords ou nome correspondente
                    elif is_specific_query:
                        # Não aceitar apenas por culinária genérica
                        pass
                    # Se não é nem específica nem culinária, aceitar correspondência parcial
                    elif not is_specific_query and not is_cuisine_query:
                        if any(tag in cuisine for tag in specific_tags):
                            has_match = True
                            match_reason.append(f"culinária parcial: {cuisine}")
                
                if has_match:
                    filtered_documents.append(doc)
                    logger.debug(f"✅ {metadata.get('name')} - Match: {', '.join(match_reason)}")
                else:
                    logger.debug(f"❌ {metadata.get('name')} - Sem correspondência (tags: {keywords}, culinária: {cuisine})")
            else:
                # Documentos não-restaurante sempre incluir (conhecimento estático)
                filtered_documents.append(doc)
        
        # Limitar a 10 documentos mais relevantes após filtro
        source_documents = filtered_documents[:10]
        
        logger.info(f"Documentos encontrados: {len(source_documents)} (após filtro semântico de {len(filtered_documents)} candidatos)")
        
        # MELHORIA: Se filtro muito restritivo não encontrou nada, usar busca mais ampla
        if len(source_documents) == 0 and len(original_docs_before_filter) > 0:
            logger.warning(f"Nenhum documento com correspondência semântica encontrado para: '{question}'")
            logger.info("Tentando busca mais ampla (sem filtro semântico rigoroso)...")
            
            # Fallback: usar documentos originais sem filtro muito restritivo
            # Aplicar apenas filtro básico por culinária se for query de culinária
            if is_cuisine_query and cuisine_tags:
                fallback_docs = []
                for doc in original_docs_before_filter[:20]:  # Usar mais documentos
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                    if metadata.get('type') == 'restaurant':
                        cuisine = metadata.get('cuisine_type', '').lower()
                        if cuisine in cuisine_tags:
                            fallback_docs.append(doc)
                    else:
                        fallback_docs.append(doc)
                
                if len(fallback_docs) > 0:
                    source_documents = fallback_docs[:10]
                    logger.info(f"Fallback encontrou {len(source_documents)} documentos com culinária correspondente")
            elif not is_specific_query:
                # Se não é query específica, usar documentos originais (menos restritivo)
                # MAS: apenas se não houver palavras-chave específicas na pergunta
                # CORREÇÃO: Não usar fallback genérico se a pergunta menciona prato específico não mapeado
                has_unmapped_specific_keywords = any(
                    kw in question_lower for kw in ['açaí', 'acai', 'açai', 'sorvete', 'gelato', 
                                                     'tapioca', 'coxinha', 'pastel', 'empada', 
                                                     'brigadeiro', 'beijinho', 'quindim']
                )
                if not has_unmapped_specific_keywords:
                    source_documents = original_docs_before_filter[:10]
                    logger.info(f"Fallback usando {len(source_documents)} documentos originais (query não específica)")
                else:
                    # Query menciona prato específico não mapeado - não usar fallback genérico
                    source_documents = []
                    logger.info(f"Query específica não mapeada detectada - não usando fallback genérico")
        
        if len(source_documents) == 0:
            logger.warning(f"Nenhum documento encontrado após filtro e fallback para: '{question}'")
            logger.info("Continuando sem documentos - LLM usará conhecimento geral")
        
    except Exception as e:
        import traceback
        logger.error(f"Erro na busca RAG: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Continuar com lista vazia - LLM pode usar conhecimento geral
        source_documents = []
    
    # Verificar se há contexto suficiente
    restaurant_docs = [doc for doc in source_documents 
                      if (doc.metadata if hasattr(doc, 'metadata') else {}).get('type') == 'restaurant']
    
    # Verificar se a pergunta é sobre recomendações ou sugestões
    is_recommendation_request = any(keyword in question_lower for keyword in [
        'recomend', 'suger', 'sugest', 'indic', 'indicar', 'qual', 'quais',
        'melhor', 'melhores', 'top', 'favorito', 'favoritos'
    ])
    
    # CORREÇÃO CRÍTICA: Se é query específica (prato específico) e não encontrou restaurantes relevantes,
    # retornar mensagem clara ao invés de deixar LLM inventar recomendações não relacionadas
    # Verificar se é query específica (prato específico como "açaí", "churrasco", etc.)
    specific_dish_keywords = [
        'açaí', 'acai', 'açai', 'churrasco', 'picanha', 'pizza', 'sushi', 'hamburguer',
        'feijoada', 'risoto', 'sorvete', 'gelato', 'tapioca', 'coxinha', 'pastel',
        'sopa', 'sopas'
    ]
    is_specific_dish_query = any(kw in question_lower for kw in specific_dish_keywords)
    
    if len(restaurant_docs) == 0:
        if is_specific_dish_query:
            # Query específica sem match - retornar mensagem clara
            dish_name = next((kw for kw in specific_dish_keywords if kw in question_lower), "isso")
            logger.warning(
                f"Query específica '{question}' não encontrou restaurantes relevantes. "
                "Retornando mensagem clara ao invés de deixar LLM inventar."
            )
            return {
                "answer": (
                    f"Olá! Infelizmente não encontrei restaurantes que sirvam {dish_name} na minha base de dados no momento.\n\n"
                    f"Se você souber de algum lugar que serve {dish_name}, posso ajudar com outras informações sobre restaurantes e comida!\n\n"
                    "Quer que eu busque outras opções?"
                ),
                "audio_url": None,
                "sources": [],
                "validation": {
                    "confidence_score": 0.0,
                    "error": False,
                    "error_message": None
                }
            }
        else:
            # Query não específica - continuar normalmente
            logger.info(
                f"Nenhum documento de restaurante encontrado para pergunta: {question[:100]}... "
                f"Total de documentos: {len(source_documents)}. Continuando com chain (pode usar recomendações ou conhecimento geral)."
            )
    
    # Criar callback de monitoramento
    monitoring_callback = LLMMonitoringCallback(user_id=user_id, question=question)
    
    # Executar chain com callback de monitoramento
    try:
        logger.info(f"Invocando chain LLM para pergunta: '{question[:100]}...'")
        logger.info(f"Chain criada: {type(chain).__name__}")
        logger.info(f"RAG Service vector_store inicializado: {rag_service.vector_store is not None}")
        
        try:
            # Testar se chain está funcionando antes de invocar
            logger.debug("Testando chain antes de invocar...")
            answer = chain.invoke(question, config={"callbacks": [monitoring_callback]})
            
            if not answer or len(answer.strip()) == 0:
                logger.warning("Resposta do LLM está vazia!")
                raise ValueError("Resposta do LLM está vazia")
            
            logger.info(f"Resposta do LLM gerada com sucesso ({len(answer)} caracteres)")
            logger.debug(f"Primeiros 200 caracteres da resposta: {answer[:200]}...")
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error("=" * 60)
            logger.error("❌ ERRO AO INVOCAR CHAIN LLM")
            logger.error("=" * 60)
            logger.error(f"Tipo de erro: {type(e).__name__}")
            logger.error(f"Mensagem: {str(e)}")
            logger.error(f"Pergunta: {question}")
            logger.error(f"Traceback completo:\n{error_traceback}")
            logger.error("=" * 60)
            raise  # Re-raise para ser capturado pelo handler em chat.py
    except Exception as e:
        # Em caso de erro, registrar no callback
        try:
            monitoring_callback.on_llm_error(e)
        except:
            pass  # Não falhar se callback também falhar
        raise
    
    # Obter métricas do callback (passar resposta para cálculo correto de tamanho)
    metrics = monitoring_callback.get_metrics(response_text=answer)
    
    # Registrar métricas (salvar no banco e log)
    try:
        log_llm_metrics(metrics, db=db, save_to_db=True)
    except Exception as e:
        # Não falhar se houver erro ao salvar métricas
        # Usar logger global, não redefinir
        logger.warning(f"Erro ao salvar métricas LLM: {e}")
    
    # Obter nome do usuário para limpeza
    user_name_for_cleaning = None
    if user_id and db:
        user = crud.get_user(db, user_id)
        if user:
            user_name_for_cleaning = user.name
    
    # PILAR 1: Limpeza de artefatos de markdown (primeiro passo)
    cleaned_answer = clean_markdown_artifacts(answer)
    
    # NOVO: Limpar metadados técnicos que podem vazar do contexto RAG
    cleaned_answer = clean_technical_metadata(cleaned_answer)
    
    # Limpar resposta removendo frases proibidas e repetições (preservar separadores)
    cleaned_answer = clean_answer(cleaned_answer, user_name=user_name_for_cleaning, question=question)
    
    # Corrigir referências vagas a restaurantes ("Eles têm" sem mencionar o restaurante)
    cleaned_answer = fix_vague_restaurant_references(cleaned_answer, source_documents)
    
    # PILAR 2: Validação estrutural estrita e lógica invertida ("na dúvida, reformate")
    # Pós-processamento: Aplicar formatação visual se o LLM não seguiu as instruções
    # (Solução para limitação de modelos menores como Llama 3.1 8B)
    try:
        from app.core.format_response import apply_visual_formatting, extract_restaurant_mentions
        
        # Verificar se há restaurantes nos documentos (sempre aplicar formatação se houver)
        restaurant_docs = [doc for doc in source_documents 
                          if (doc.metadata if hasattr(doc, 'metadata') else {}).get('type') == 'restaurant']
        
        # Verificar se há restaurantes mencionados na resposta
        restaurant_mentions = extract_restaurant_mentions(cleaned_answer, source_documents)
        
        # LÓGICA INVERTIDA: Na dúvida, reformate
        # SEMPRE aplicar formatação visual se:
        # 1. Há restaurantes nos documentos E/OU mencionados na resposta
        # 2. OU a resposta não é estruturalmente válida
        should_format = (
            len(restaurant_docs) > 0 or 
            len(restaurant_mentions) > 0 or
            not is_structurally_valid(cleaned_answer)
        )
        
        if should_format:
            logger.info(f"Aplicando pós-processamento: {len(restaurant_docs)} restaurantes encontrados, {len(restaurant_mentions)} mencionados")
            answer = apply_visual_formatting(cleaned_answer, source_documents, question)
        else:
            answer = cleaned_answer
        
        # NOVO: Limpar metadados técnicos da resposta final (mesmo após pós-processamento)
        answer = clean_technical_metadata(answer)
        
        # Limpeza final de artefatos que possam ter sobrado
        answer = clean_markdown_artifacts(answer)
    except Exception as e:
        import traceback
        logger.warning(f"Erro ao aplicar formatação visual: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        # Continuar com resposta limpa se houver erro
        answer = clean_technical_metadata(cleaned_answer)
        answer = clean_markdown_artifacts(answer)
    
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
    
    # Frases vagas e genéricas a remover
    vague_phrases = [
        r'\bpodem ser uma boa escolha\b',
        r'\bpode ser uma boa opção\b',
        r'\bessas opções podem\b',
        r'\bqualquer uma dessas opções\b',
        r'\bessas são apenas algumas\b',
        r'\bvocê pode considerar\b',
        r'\bvocê pode gostar\b',
    ]
    
    # Remover frases vagas
    for phrase in vague_phrases:
        answer = re.sub(phrase, '', answer, flags=re.IGNORECASE)
    
    has_food_content = any(keyword in answer_lower for keyword in food_keywords_in_answer)
    has_out_of_scope_content = any(indicator in answer_lower for indicator in out_of_scope_indicators)
    
    # Se detectar conteúdo fora do escopo na resposta E não houver conteúdo sobre comida, substituir
    if has_out_of_scope_content and not has_food_content:
        answer = (
            "Desculpe, eu só ajudo com restaurantes e comida. "
            "Como posso ajudá-lo a encontrar um restaurante ou prato hoje?"
        )
    
    # VALIDAÇÃO CRÍTICA: Verificar se restaurantes mencionados correspondem à pergunta
    # Extrair restaurantes mencionados na resposta
    mentioned_restaurants = extract_restaurant_names_from_text(answer)
    
    if mentioned_restaurants and question:
        # Verificar correspondência semântica
        question_lower = question.lower()
        invalid_restaurants = []
        
        # Mapeamento de palavras-chave para tags (mesmo do filtro RAG)
        keyword_to_tags = {
            'churrasco': ['churrasco', 'rodízio', 'picanha', 'churrascaria'],
            'pizza': ['pizza', 'massa', 'italiana'],
            'sushi': ['sushi', 'japonesa', 'sashimi'],
            'hamburguer': ['hamburguer', 'burger', 'hamburgueria'],
        }
        
        # Identificar tags relevantes da pergunta
        relevant_tags = set()
        for keyword, tags in keyword_to_tags.items():
            if keyword in question_lower:
                relevant_tags.update(tags)
        
        # Validar cada restaurante mencionado
        for restaurant_name in mentioned_restaurants:
            # Buscar restaurante no contexto
            restaurant_doc = None
            for doc in source_documents:
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                if metadata.get('name', '').lower() == restaurant_name.lower():
                    restaurant_doc = doc
                    break
            
            if restaurant_doc:
                metadata = restaurant_doc.metadata if hasattr(restaurant_doc, 'metadata') else {}
                keywords = metadata.get('keywords', '').lower()
                cuisine = metadata.get('cuisine_type', '').lower()
                
                # Verificar se tem correspondência semântica
                has_match = False
                if keywords and relevant_tags:
                    doc_tags = set(keywords.split(', '))
                    if relevant_tags & doc_tags:
                        has_match = True
                
                if not has_match and relevant_tags:
                    invalid_restaurants.append(restaurant_name)
                    logger.warning(f"⚠️  Restaurante '{restaurant_name}' mencionado mas sem correspondência semântica com '{question}' (tags: {keywords})")
        
        # Remover recomendações inválidas da resposta
        if invalid_restaurants:
            for invalid_name in invalid_restaurants:
                # Remover sentença que menciona restaurante inválido
                pattern = rf'[^.!?]*\b{re.escape(invalid_name)}\b[^.!?]*[.!?]'
                answer = re.sub(pattern, '', answer, flags=re.IGNORECASE)
                logger.info(f"🗑️  Removida recomendação inválida: {invalid_name}")
            
            # Limpar espaços duplos
            answer = re.sub(r'\s+', ' ', answer).strip()
    
    # Validar resposta contra o contexto e banco de dados
    validation = None
    try:
        validation = validate_answer_against_context(answer, source_documents, db=db)
        
        # Se detectar alucinação potencial, tomar ação mais rigorosa
        if validation.get("has_potential_hallucination", False):
            invalid_count = len(validation.get("invalid_mentions", []))
            valid_count = len(validation.get("valid_mentions", []))
            total_mentioned = len(validation.get("mentioned_restaurants", []))
            
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
    except Exception as e:
        import traceback
        logger.warning(f"Erro ao validar resposta contra contexto: {type(e).__name__}: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        # Continuar com validação vazia se houver erro
        validation = {
            "confidence_score": 0.0,
            "has_potential_hallucination": False,
            "mentioned_restaurants": [],
            "valid_mentions": [],
            "invalid_mentions": []
        }
    
    # Adicionar ao histórico
    if user_id:
        try:
            add_to_conversation_history(user_id, question, answer, db=db, audio_url=audio_url)
        except Exception as e:
            import traceback
            logger.warning(f"Erro ao adicionar ao histórico: {type(e).__name__}: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            # Não falhar se houver erro ao salvar histórico
    
    # Adicionar call-to-action se houver restaurantes recomendados
    # REMOVIDO: Seção "Próximos Passos" não deve aparecer para o usuário
    # if mentioned_restaurants and len(mentioned_restaurants) > 0:
    #     # Verificar se já não há call-to-action na resposta
    #     if 'próximos passos' not in answer.lower() and 'cardápio' not in answer.lower():
    #         answer += "\n\n📱 **Próximos Passos:**\n"
    #         answer += "   Digite 'cardápio [nome]' ou 'preços [nome]' para mais detalhes."
    
    # Construir resposta final
    try:
        response = {
            "answer": answer,
            "source_documents": [
                {
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                }
                for doc in source_documents
            ],
            "validation": validation or {
                "confidence_score": 0.0,
                "has_potential_hallucination": False,
                "mentioned_restaurants": [],
                "valid_mentions": [],
                "invalid_mentions": []
            }
        }
    except Exception as e:
        import traceback
        logger.error(f"Erro ao construir resposta final: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Retornar resposta mínima se houver erro
        response = {
            "answer": answer,
            "source_documents": [],
            "validation": {
                "confidence_score": 0.0,
                "has_potential_hallucination": False,
                "mentioned_restaurants": [],
                "valid_mentions": [],
                "invalid_mentions": []
            }
        }
    
    # FASE 3: Cachear resposta se apropriado
    try:
        if should_cache_query(question):
            cache = get_response_cache()
            cache.set(question, response, user_id=user_id)
    except Exception as e:
        import traceback
        logger.warning(f"Erro ao cachear resposta: {type(e).__name__}: {str(e)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        # Não falhar se houver erro ao cachear
    
    # Log final para debug
    logger.info(f"Resposta final gerada com sucesso: {len(response.get('answer', ''))} caracteres")
    logger.debug(f"Estrutura da resposta: answer={bool(response.get('answer'))}, sources={len(response.get('source_documents', []))}, validation={bool(response.get('validation'))}")
    
    return response


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
    
    # Perguntas sobre identidade/nome do agente (VERIFICAR PRIMEIRO)
    identity_keywords = [
        "qual seu nome", "qual é seu nome", "qual o seu nome",
        "quem é você", "quem voce", "quem voce e",
        "você é", "voce e", "você é quem", "voce e quem",
        "como você se chama", "como voce se chama",
        "me diga seu nome", "me diga o seu nome",
        "what's your name", "who are you", "what are you"
    ]
    
    # Verificar perguntas sobre identidade (PRIORIDADE: antes de tudo)
    for identity_kw in identity_keywords:
        if identity_kw in message_lower:
            responses = [
                "Sou o Chef Virtual! Quer que eu recomende algo?",
                "Sou o Chef Virtual do TasteMatch. Em que posso ajudar?",
                "Sou o Chef Virtual! Posso ajudar com restaurantes e comida. O que você procura?",
                "Sou o Chef Virtual! Quer que eu recomende algum restaurante?",
                "Sou o Chef Virtual do TasteMatch. Como posso ajudar você hoje?"
            ]
            return random.choice(responses)
    
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
    
    # Verificar saudações simples (incluindo "tudo bem?")
    greeting_count = sum(1 for word in words if any(kw in word for kw in greeting_keywords))
    # Incluir "tudo bem?" mesmo com interrogação (é saudação, não pergunta real)
    is_greeting_question = any(kw in message_lower for kw in ["tudo bem", "tudobem", "td bem", "tdbem"])
    
    if (greeting_count > 0 and len(words) <= 3) or is_greeting_question:  # Saudações curtas ou "tudo bem?"
        # Verificar se não há pergunta real junto (exceto "tudo bem?")
        question_indicators = ["qual", "quais", "onde", "como", "quando", "quanto"]
        has_real_question = any(ind in message_lower for ind in question_indicators)
        
        # "tudo bem?" é saudação, não pergunta real
        if not has_real_question or is_greeting_question:
            # Respostas simples e diretas para cumprimentos
            # NÃO mencionar restaurantes ou comida, apenas cumprimentar e perguntar como ajudar
            responses = [
                "Olá! Em que posso ajudar?",
                "Oi! Como posso ajudar?",
                "Olá! Em que posso ajudar hoje?",
                "Oi! Em que posso ajudar com restaurantes e comida?",
                "Olá! Como posso ajudar?"
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
    
    # CORREÇÃO: Validação menos restritiva
    # Permitir perguntas sobre comida/restaurantes mesmo sem palavras-chave explícitas
    # O LLM pode lidar melhor com perguntas genéricas e redirecionar quando necessário
    # Apenas rejeitar se for claramente fora do escopo (já verificado acima)
    
    # Verificar se a pergunta não está vazia
    if not question.strip():
        return False, "Por favor, faça uma pergunta sobre restaurantes, comida ou alimentação."
    
    # Verificar tamanho máximo
    if len(question) > 1000:
        return False, "Sua pergunta é muito longa. Por favor, seja mais conciso."
    
    # Se chegou aqui e não foi rejeitada por palavras inapropriadas ou fora do escopo,
    # permitir a pergunta (mesmo que não tenha palavras-chave explícitas de comida)
    # O LLM será responsável por responder adequadamente ou redirecionar
    return True, None

