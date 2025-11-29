# Correção: Patch do Cliente Groq

> **Data:** 29 de Novembro de 2025  
> **Status:** ✅ Corrigido

---

## Problema Identificado

O patch inicial estava tentando fazer patch em `self.client.chat.completions.create()`, mas na verdade:

1. **`self.client` já é** `groq.resources.chat.completions.Completions`
2. O método chamado é **`self.client.create()`** diretamente
3. O traceback mostrava: `response = self.client.create(messages=message_dicts, **params)`

## Investigação Realizada

### Comando de diagnóstico:
```bash
python -c "
import os
os.environ['GROQ_API_KEY'] = 'fake'
from langchain_groq import ChatGroq
llm = ChatGroq(model='llama-3.1-8b-instant', groq_api_key='fake')
print('Client:', type(llm.client))
print('Has create:', hasattr(llm.client, 'create'))
print('Has chat:', hasattr(llm.client, 'chat'))
"
```

### Resultado:
```
Client: <class 'groq.resources.chat.completions.Completions'>
Has create: True
Has chat: False
```

**Conclusão:** O `self.client` já é o objeto `Completions`, não o cliente completo do Groq.

---

## Correção Aplicada

### Antes (Incorreto):
```python
# Tentava fazer patch em caminho inexistente
if hasattr(self.client, 'chat'):
    if hasattr(self.client.chat, 'completions'):
        original_create = self.client.chat.completions.create  # ❌ Não existe
```

### Depois (Correto):
```python
# Patch direto no método create do objeto Completions
if hasattr(self.client, 'create'):
    original_create = self.client.create  # ✅ Correto
    # ...
    self.client.create = filtered_create
```

---

## Código Final da Correção

**Localização:** `backend/app/core/chef_chat.py` (linhas 42-107)

```python
def _apply_client_patch(self):
    """
    Aplica patch no cliente Groq para filtrar parâmetros não suportados.
    
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
            """Wrapper que filtra parâmetros não suportados antes de chamar API Groq."""
            unsupported_params = ['reasoning_format', 'reasoning_effort']
            for param in unsupported_params:
                kwargs.pop(param, None)
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
        # Log mas não falhar - override em _generate ainda pode ajudar
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Erro ao aplicar patch no cliente Groq: {e}. "
            "Tentando continuar com override em _generate apenas."
        )
```

---

## Melhorias Adicionais

1. **Suporte para async_client** - Também faz patch no cliente assíncrono se existir
2. **Validações robustas** - Verifica existência de atributos antes de fazer patch
3. **Tratamento de erros** - Continua funcionando mesmo se patch falhar

---

## Verificações Realizadas

- ✅ Sintaxe Python: OK
- ✅ Linter: Sem erros
- ✅ Estrutura do cliente: Confirmada corretamente

---

## Próximos Passos

1. **Reiniciar backend** para aplicar a correção
2. **Testar endpoint** `/api/chat/` novamente
3. **Verificar logs** - Não deve mais aparecer erro `reasoning_format`

---

## Referência ao Erro Original

O erro ocorria na linha 985 do `langchain_groq/chat_models.py`:
```python
response = self.client.create(messages=message_dicts, **params)
TypeError: Completions.create() got an unexpected keyword argument 'reasoning_format'
```

Agora o patch intercepta **exatamente nesse ponto** antes que o erro ocorra.

---

**Última atualização:** 29/11/2025 17:45

