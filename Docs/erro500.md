# Erro 500 no Endpoint `/api/chat/` - Requer Ajuda

> **Status:** ⚠️ **PENDENTE** - Tentativas de solução implementadas mas erro persiste  
> **Data:** 29 de Novembro de 2025  
> **Ambiente:** Desenvolvimento Local  
> **Prioridade:** 🔴 Alta

---

## 📋 Resumo Executivo

### Problema Principal
O endpoint `/api/chat/` está retornando **erro 500 (Internal Server Error** quando tenta gerar respostas usando o LangChain com ChatGroq.

### Erro Específico
```
TypeError: Completions.create() got an unexpected keyword argument 'reasoning_format'
```

### Impacto
- Endpoint de chat completamente inoperante
- Usuários não conseguem usar o Chef Virtual
- Erro ocorre em todas as requisições ao endpoint

---

## 🐛 Erro Detalhado

### Mensagem de Erro Completa
```
TypeError: Completions.create() got an unexpected keyword argument 'reasoning_format'
```

### Traceback Completo (dos logs do backend)
```
Traceback (most recent call last):
  File "/home/brunoadsba/ifood/tastematch/backend/app/api/routes/chat.py", line 202, in chat
    response = get_chef_response(
               ^^^^^^^^^^^^^^^^^^
  File "/home/brunoadsba/ifood/tastematch/backend/app/core/chef_chat.py", line 1000, in get_chef_response
    answer = chain.invoke(question, config={"callbacks": [monitoring_callback]})
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brunoadsba/ifood/tastematch/venv/lib/python3.11/site-packages/langchain_core/runnables/base.py", line 3046, in invoke
    input_ = context.run(step.invoke, input_, config)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brunoadsba/ifood/tastematch/venv/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 395, in invoke
    self.generate_prompt(
  File "/home/brunoadsba/ifood/tastematch/venv/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 980, in generate_prompt
    return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/brunoadsba/ifood/tastematch/venv/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 799, in generate
    self._generate_with_cache(
  File "/home/brunoadsba/ifood/tastematch/venv/lib/python3.11/site-packages/langchain_core/language_models/chat_models.py", line 1045, in _generate_with_cache
    result = self._generate(
             ^^^^^^^^
  File "/home/brunoadsba/ifood/tastematch/venv/lib/python3.11/site-packages/langchain_groq/chat_models.py", line 504, in _generate
    response = self.client.create(messages=message_dicts, **params)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Completions.create() got an unexpected keyword argument 'reasoning_format'
```

### Quando Ocorre
- Toda vez que o endpoint `/api/chat/` recebe uma requisição válida
- Após autenticação bem-sucedida
- Após validação da pergunta
- Durante a execução do chain LangChain para gerar resposta

---

## 🔧 Contexto do Ambiente

### Versões de Dependências Críticas
```txt
langchain==0.3.27
langchain-core==0.3.72
langchain-groq==0.3.3
groq==0.4.1
pydantic==2.7.4
pydantic-settings==2.12.0
```

### Configurações Relevantes
- **Modelo LLM:** `llama-3.1-8b-instant`
- **Ambiente:** Desenvolvimento local
- **Python:** 3.11
- **Backend:** FastAPI 0.104.1
- **GROQ_API_KEY:** Configurada e validada

### Ambiente
- **Local:** `http://localhost:8000`
- **Database:** PostgreSQL local (Docker) na porta 5432
- **Extensão pgvector:** Instalada e funcionando

---

## ✅ Tentativas de Solução Já Implementadas

### 1. Wrapper `ChatGroqFiltered` (Status: ⚠️ NÃO RESOLVIDO)

**Localização:** `backend/app/core/chef_chat.py` (linhas 26-45)

**Implementação:**
```python
class ChatGroqFiltered(ChatGroq):
    """
    Wrapper do ChatGroq que filtra parâmetros não suportados como 'reasoning_format'.
    """
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> Any:
        """Override para filtrar parâmetros não suportados."""
        # Remover parâmetros de reasoning que não são suportados
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['reasoning_format', 'reasoning_effort']}
        return super()._generate(messages, stop=stop, run_manager=run_manager, **filtered_kwargs)
```

**Uso:**
```python
llm = ChatGroqFiltered(
    groq_api_key=settings.GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.5
)
```

**Problema:** O wrapper foi criado mas o erro persiste. O parâmetro `reasoning_format` pode estar sendo adicionado em outro lugar do fluxo, ou o override não está interceptando corretamente.

### 2. Handler Global de Exceções (Status: ✅ IMPLEMENTADO)

**Localização:** `backend/app/main.py` (linhas 72-104)

**Função:** Captura todas as exceções não tratadas e loga com traceback completo.

### 3. Logging Melhorado (Status: ✅ IMPLEMENTADO)

**Localização:** `backend/app/api/routes/chat.py`

**Função:** Logging detalhado com traceback completo para facilitar debug.

---

## 📝 Informações Técnicas

### Arquivos Envolvidos
1. `backend/app/api/routes/chat.py` - Endpoint que recebe a requisição
2. `backend/app/core/chef_chat.py` - Lógica do Chef Virtual e criação do LLM
3. `backend/app/core/llm_monitoring.py` - Callback de monitoramento
4. `venv/lib/python3.11/site-packages/langchain_groq/chat_models.py:504` - Onde o erro ocorre

### Stack Trace Completo
O erro ocorre na seguinte sequência:
1. `chat()` endpoint recebe requisição POST
2. Valida pergunta e obtém RAG service
3. Chama `get_chef_response()` 
4. Cria chain LangChain com `create_chef_chain()`
5. Executa `chain.invoke()` com callback
6. LangChain chama `ChatGroq._generate()`
7. `langchain_groq` tenta passar `reasoning_format` para API Groq
8. **ERRO:** API Groq rejeita parâmetro não suportado

### Onde o Parâmetro Está Sendo Adicionado

O parâmetro `reasoning_format` está sendo adicionado em algum lugar do fluxo LangChain, possivelmente:
- No `langchain_groq` baseado em alguma configuração do modelo
- No `langchain-core` como parâmetro padrão
- Em alguma configuração do chain que não estamos vendo

---

## ❓ Perguntas para o Dev/IA que Vai Ajudar

1. **O parâmetro `reasoning_format` está sendo adicionado onde?**
   - Está vindo do `langchain-groq` internamente?
   - Está sendo adicionado pelo `langchain-core`?
   - Como identificar a origem exata?

2. **O wrapper `ChatGroqFiltered` não está funcionando. Por quê?**
   - O override do `_generate()` está correto?
   - O parâmetro está sendo adicionado depois do `_generate()`?
   - Existe outro método que preciso sobrescrever?

3. **Como interceptar o parâmetro antes que chegue na API Groq?**
   - Existe um método melhor que `_generate()`?
   - Preciso criar um wrapper no cliente Groq também?
   - Há configuração que desabilita esses parâmetros?

4. **Existe alternativa melhor?**
   - Atualizar versão do `langchain-groq`?
   - Mudar de modelo LLM?
   - Usar outra biblioteca de integração com Groq?

5. **O erro pode estar relacionado a versões das dependências?**
   - As versões atuais são compatíveis?
   - Existe incompatibilidade conhecida?

---

## 🔍 Análise do Código

### Criação do ChatGroq

**Localização:** `backend/app/core/chef_chat.py:339-343`

```python
llm = ChatGroqFiltered(
    groq_api_key=settings.GROQ_API_KEY,
    model="llama-3.1-8b-instant",
    temperature=0.5
)
```

### Execução do Chain

**Localização:** `backend/app/core/chef_chat.py:1000`

```python
answer = chain.invoke(question, config={"callbacks": [monitoring_callback]})
```

### Chain Criado

**Localização:** `backend/app/core/chef_chat.py:338-600+`

A chain é criada usando LCEL (LangChain Expression Language) e envolve:
- RAG retrieval
- Prompt template
- LLM (ChatGroqFiltered)
- Output parser

---

## 🧪 Como Reproduzir o Erro

### Pré-requisitos
1. PostgreSQL local rodando na porta 5432
2. Backend iniciado com `DATABASE_URL` local
3. `GROQ_API_KEY` configurada no `.env`
4. Usuário autenticado

### Passos
1. Iniciar backend:
```bash
cd /home/brunoadsba/ifood/tastematch/backend
export DATABASE_URL="postgresql://tastematch:tastematch_dev@localhost:5432/tastematch"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. Fazer requisição POST para `/api/chat/`:
```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer <TOKEN>" \
  -F "message=quero um restaurante italiano"
```

3. Verificar logs do backend - erro aparecerá após ~3-5 segundos

### Logs Esperados
```
ERROR app.core.llm_monitoring - Erro no LLM: Completions.create() got an unexpected keyword argument 'reasoning_format'
ERROR app.api.routes.chat - Erro ao gerar resposta do Chef: Completions.create() got an unexpected keyword argument 'reasoning_format'
[Traceback completo...]
ERROR app.main - POST /api/chat/ - 500 [endpoint=/api/chat/, duration=4181.02ms]
```

---

## 📚 Referências e Contexto Adicional

### Documentação Relacionada
- `Docs/DEBUG_ERRO_500_CHAT.md` - Primeira investigação
- `Docs/ANALISE_ERRO_500_CHAT.md` - Análise baseada em lições aprendidas
- `Docs/SOLUCAO_ERRO_500_CHAT_REASONING_FORMAT.md` - Tentativa de solução

### Lições Aprendidas Relevantes
- Conflitos de dependências foram resolvidos anteriormente
- Configuração explícita é melhor que detecção automática
- Logging estruturado facilita debug

---

## 🎯 Próximos Passos Sugeridos

1. Investigar onde `reasoning_format` está sendo adicionado no fluxo LangChain
2. Verificar se há configuração no `langchain-groq` que adiciona esse parâmetro
3. Tentar interceptar em outro nível (cliente Groq, configuração do chain, etc.)
4. Considerar atualização ou downgrade de versões se necessário
5. Verificar se há issues conhecidos no repositório `langchain-groq`

---

## 📞 Informações de Contato / Contexto

- **Projeto:** TasteMatch - Agente de Recomendação Inteligente
- **Ambiente Atual:** Desenvolvimento Local
- **Deploy em Produção:** Funciona (usa Supabase, pode ter comportamento diferente)
- **Última Modificação:** 29/11/2025 17:13
- **Status:** 🔴 **REQUER AJUDA URGENTE**

---

**Nota:** Este documento foi criado para facilitar a colaboração com outros desenvolvedores ou IAs. Todas as informações relevantes estão incluídas para diagnóstico rápido.

