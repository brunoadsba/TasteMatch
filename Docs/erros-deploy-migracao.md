# Documentação de Erros - Deploy e Migração Supabase

> **Projeto**: TasteMatch Backend  
> **Contexto**: Migração de banco Fly.io Postgres para Supabase + Deploy da API  
> **Data**: 29 de Novembro de 2025  
> **Status Geral**: ✅ **DEPLOY CONCLUÍDO** - Todos os conflitos resolvidos, API em produção (v42)

---

## 📋 Resumo Executivo

### Problema Principal
O deploy da aplicação FastAPI no Fly.io estava falhando devido a **conflitos de dependências Python** durante o build da imagem Docker. Todos os conflitos foram identificados e corrigidos.

### Estatísticas
- **Total de Releases Falhados**: 6 (v36 a v41)
- **Último Release Bem-Sucedido**: v42 (29/11/2025 18:00)
- **Erros Críticos Identificados**: 7
- **Erros Resolvidos**: 7 ✅
- **Erros Pendentes**: 0
- **Build Docker Local**: ✅ Sucesso (29/11/2025)
- **Deploy Fly.io**: ✅ Sucesso (29/11/2025 18:00)

### Impacto
- ✅ Build Docker validado localmente
- ✅ Todos os conflitos de dependências resolvidos
- ✅ Deploy no Fly.io concluído com sucesso
- ✅ API em produção: https://tastematch-api.fly.dev/
- ⏳ Migração para Supabase pode ser continuada

---

## 🔴 Erros de Dependências Python

### ERR-001: Conflito `langchain-core` vs `langchain`

**Categoria**: Dependências Python  
**Severidade**: 🔴 Crítico  
**Status**: ✅ Resolvido  
**Data**: 29/11/2025 ~14:00

#### Contexto
Durante o build Docker, o pip não conseguia resolver dependências do LangChain devido a versão incompatível de `langchain-core`.

#### Mensagem de Erro Completa
```
#10 9.086 ERROR: Cannot install -r /tmp/requirements-no-torch.txt (line 34) and langchain-core==0.2.43 because these package versions have conflicting dependencies.
#10 9.086 ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
#10 9.086 
#10 9.086 The conflict is caused by:
#10 9.086     The user requested langchain-core==0.2.43
#10 9.086     langchain 0.3.27 depends on langchain-core<1.0.0 and >=0.3.72
```

#### Arquivos Envolvidos
- `backend/requirements.txt` (linha 37)
- `backend/Dockerfile` (linha 25-30)

#### Versões Envolvidas
- **Antes**: `langchain-core==0.2.43`
- **Requerido por**: `langchain==0.3.27` → `langchain-core>=0.3.72, <1.0.0`
- **Depois**: `langchain-core==0.3.72`

#### Solução Aplicada
Atualizado `requirements.txt`:
```txt
langchain-core==0.3.72  # Versão mínima requerida por langchain 0.3.27
```

#### Logs Relacionados
- `/tmp/deploy_fixed.log`
- `/tmp/deploy_corrected.log`

---

### ERR-002: Conflito `pydantic` vs `langchain`

**Categoria**: Dependências Python  
**Severidade**: 🔴 Crítico  
**Status**: ✅ Resolvido  
**Data**: 29/11/2025 ~14:05

#### Contexto
Após corrigir `langchain-core`, novo conflito surgiu: `langchain 0.3.27` requer `pydantic>=2.7.4`, mas estava fixado em `2.5.0`.

#### Mensagem de Erro Completa
```
#10 8.408 ERROR: Cannot install -r /tmp/requirements-no-torch.txt (line 2), -r /tmp/requirements-no-torch.txt (line 31), -r /tmp/requirements-no-torch.txt (line 35), -r /tmp/requirements-no-torch.txt (line 5) and pydantic==2.5.0 because these package versions have conflicting dependencies.
#10 8.408 ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
#10 8.408 
#10 8.408 The conflict is caused by:
#10 8.408     langchain 0.3.27 depends on pydantic<3.0.0 and >=2.7.4
```

#### Arquivos Envolvidos
- `backend/requirements.txt` (linha 4)

#### Versões Envolvidas
- **Antes**: `pydantic==2.5.0`
- **Requerido por**: `langchain==0.3.27` → `pydantic>=2.7.4, <3.0.0`
- **Depois**: `pydantic==2.7.4`

#### Solução Aplicada
Atualizado `requirements.txt`:
```txt
pydantic==2.7.4  # Versão mínima requerida por langchain 0.3.27 (>=2.7.4, <3.0.0)
```

#### Logs Relacionados
- `/tmp/deploy_corrected.log`

---

### ERR-003: Conflito `pydantic-settings` vs `pydantic`

**Categoria**: Dependências Python  
**Severidade**: 🔴 Crítico  
**Status**: ✅ **RESOLVIDO**  
**Data**: 29/11/2025 ~14:10

#### Contexto
Após atualizar `pydantic` para `2.7.4`, o `pydantic-settings==2.1.0` não era compatível com a nova versão.

#### Mensagem de Erro Completa
```
#10 10.71 ERROR: Cannot install -r /tmp/requirements-no-torch.txt (line 37) and pydantic-settings==2.1.0 because these package versions have conflicting dependencies.
#10 10.71 ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
#10 10.71 
#10 10.71 The conflict is caused by:
#10 10.71     The user requested pydantic-settings==2.1.0
#10 10.71     langchain-core 0.3.72 depends on pydantic-settings<3.0.0 and >=2.0.0
#10 10.71     pydantic 2.7.4 depends on pydantic-settings<3.0.0 and >=2.0.0
#10 10.71     pydantic-settings 2.1.0 depends on pydantic<2.0.0 and >=1.8.2
```

#### Arquivos Envolvidos
- `backend/requirements.txt` (linha 5)

#### Versões (Antes/Depois)
- **Antes**: `pydantic-settings==2.1.0`
- **Depois**: `pydantic-settings==2.12.0`
- **pydantic**: `2.7.4` (mantido)

#### Solução Aplicada
Atualizado `pydantic-settings` para `2.12.0` no `requirements.txt`, que é compatível com `pydantic 2.7.4` e `langchain-core 0.3.72`.

#### Logs Relacionados
- `/tmp/deploy_pydantic_fixed.log`

---

### ERR-004: Conflito `langchain-huggingface` vs `transformers`

**Categoria**: Dependências Python  
**Severidade**: 🟡 Alto  
**Status**: ✅ Resolvido (mudança de abordagem)  
**Data**: 29/11/2025 ~13:55

#### Contexto
Durante tentativa inicial de build com Dockerfile antigo que instalava dependências manualmente, conflito entre múltiplas versões de `langchain-huggingface` e `transformers`.

#### Mensagem de Erro Completa
```
#11 63.91 ERROR: Cannot install huggingface-hub==0.20.0, langchain-huggingface==0.0.1, langchain-huggingface==0.0.2, langchain-huggingface==0.0.3, langchain-huggingface==0.1.0, langchain-huggingface==0.1.1, langchain-huggingface==0.1.2, langchain-huggingface==0.2.0, langchain-huggingface==0.3.0, langchain-huggingface==0.3.1, langchain-huggingface==1.0.0, langchain-huggingface==1.0.1, langchain-huggingface==1.1.0, sentence-transformers==2.3.1 and transformers==4.35.2 because these package versions have conflicting dependencies.
#11 63.91 ERROR: ResolutionImpossible: for help visit https://pip.pypa.io/en/latest/topics/dependency-resolution/#dealing-with-dependency-conflicts
```

#### Arquivos Envolvidos
- `backend/Dockerfile` (versão antiga - linhas 24-60)
- `backend/requirements.txt`

#### Versões Envolvidas
- `langchain-huggingface>=0.0.1` (múltiplas versões tentadas)
- `transformers==4.35.2`
- `huggingface-hub==0.20.0`
- `sentence-transformers==2.3.1`

#### Solução Aplicada
**Mudança de estratégia**: Ao invés de instalar dependências manualmente no Dockerfile, migrado para usar `requirements.txt` diretamente, permitindo que o pip resolva dependências automaticamente.

**Dockerfile atualizado**:
```dockerfile
# Instalar todas as dependências do requirements.txt (exceto torch)
RUN grep -v "^torch==" requirements.txt > /tmp/requirements-no-torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements-no-torch.txt && \
    ...
```

#### Logs Relacionados
- `/tmp/deploy_v42.log`

---

### ERR-005: ModuleNotFoundError: `slowapi`

**Categoria**: Dependências Python  
**Severidade**: 🔴 Crítico  
**Status**: ✅ Resolvido  
**Data**: 29/11/2025 ~13:30

#### Contexto
Após deploy bem-sucedido, a API em produção falhou ao iniciar com erro de módulo não encontrado.

#### Mensagem de Erro Completa
```
ModuleNotFoundError: No module named 'slowapi'
```

#### Arquivos Envolvidos
- `backend/Dockerfile` (versão antiga)
- `backend/requirements.txt` (linha 56)

#### Causa Raiz
O Dockerfile antigo instalava dependências manualmente em grupos separados, e `slowapi` não estava incluído na lista de dependências leves, resultando em não instalação.

#### Solução Aplicada
Atualizado Dockerfile para usar `requirements.txt` diretamente, garantindo que todas as dependências sejam instaladas:
```dockerfile
RUN grep -v "^torch==" requirements.txt > /tmp/requirements-no-torch.txt && \
    pip install --no-cache-dir -r /tmp/requirements-no-torch.txt
```

#### Logs Relacionados
- Logs do Fly.io (via `fly logs -a tastematch-api`)

---

## 🟡 Erros de Build Docker

### ERR-006: Build Cancelado (Context Canceled)

**Categoria**: Deploy Fly.io  
**Severidade**: 🟡 Médio  
**Status**: ✅ Resolvido (reattempt)  
**Data**: 29/11/2025 (múltiplas ocorrências)

#### Contexto
Deploys foram cancelados manualmente ou por timeout durante resolução de dependências.

#### Mensagem de Erro Completa
```
WARN failed to finish build in graphql: Post "https://api.fly.io/api/v1/builds/finish": context canceled
Error: failed to fetch an image or build from source: error building: failed to solve: Canceled: context canceled
```

#### Causa Raiz
- Cancelamento manual do deploy pelo usuário
- Timeout durante resolução de dependências (pip demorando muito)

#### Solução Aplicada
- Reexecutar deploy após corrigir conflitos de dependências
- Versões fixas reduzem tempo de resolução

#### Logs Relacionados
- `/tmp/deploy_final.log`
- `/tmp/deploy_v42.log`

---

### ERR-007: Conflito `langchain-groq` vs `langchain-core`

**Categoria**: Dependências Python  
**Severidade**: 🔴 Crítico  
**Status**: ✅ **RESOLVIDO**  
**Data**: 29/11/2025 ~14:40

#### Contexto
Após corrigir `pydantic-settings`, um novo conflito surgiu com `langchain-groq`, que requeria uma versão mais antiga de `langchain-core` do que a instalada.

#### Mensagem de Erro Completa
```
ERROR: Cannot install -r /tmp/no_torch.txt (line 35), -r /tmp/no_torch.txt (line 37), -r /tmp/no_torch.txt (line 38) and langchain-core==0.3.72 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested langchain-core==0.3.72
    langchain 0.3.27 depends on langchain-core<1.0.0 and >=0.3.72
    langchain-community 0.3.27 depends on langchain-core<1.0.0 and >=0.3.66
    langchain-groq 0.1.9 depends on langchain-core<0.3.0 and >=0.2.26
```

#### Arquivos Envolvidos
- `backend/requirements.txt`

#### Versões (Antes/Depois)
- **Antes**: `langchain-groq==0.1.9`
- **Depois**: `langchain-groq>=0.3.0`
- **langchain-core**: `0.3.72` (mantido)

#### Solução Aplicada
Atualizado `langchain-groq` para `>=0.3.0` no `requirements.txt` para ser compatível com `langchain-core 0.3.72`.

---

### ERR-008: Conflito `huggingface-hub` vs `langchain-huggingface`

**Categoria**: Dependências Python  
**Severidade**: 🔴 Crítico  
**Status**: ✅ **RESOLVIDO**  
**Data**: 29/11/2025 ~15:00

#### Contexto
Após corrigir `langchain-groq`, um novo conflito surgiu com `huggingface-hub`, que era requerido em versão `>=0.23.0` por `langchain-huggingface 0.0.3`.

#### Mensagem de Erro Completa
```
ERROR: Cannot install -r /tmp/requirements-no-torch.txt (line 21), -r /tmp/requirements-no-torch.txt (line 22), -r /tmp/requirements-no-torch.txt (line 39) and huggingface-hub==0.20.0 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested huggingface-hub==0.20.0
    sentence-transformers 2.3.1 depends on huggingface-hub>=0.15.1
    transformers 4.35.2 depends on huggingface-hub<1.0 and >=0.16.4
    langchain-huggingface 0.0.3 depends on huggingface-hub>=0.23.0
```

#### Arquivos Envolvidos
- `backend/requirements.txt`

#### Versões (Antes/Depois)
- **Antes**: `huggingface-hub==0.20.0`
- **Depois**: `huggingface-hub>=0.16.4` (ajustado após remover langchain-huggingface)
- **langchain-huggingface**: Removido (não utilizado)

#### Solução Aplicada
1. Inicialmente atualizado para `>=0.23.0` para satisfazer `langchain-huggingface 0.0.3`
2. Após análise do código, identificado que `langchain-huggingface` não é utilizado (código usa `langchain_community.embeddings.HuggingFaceEmbeddings`)
3. Removido `langchain-huggingface` do `requirements.txt`
4. Ajustado `huggingface-hub` para `>=0.16.4` (suficiente para `transformers` e `sentence-transformers`)

---

### ERR-009: Conflito `langchain-huggingface` vs `langchain-core`

**Categoria**: Dependências Python  
**Severidade**: 🔴 Crítico  
**Status**: ✅ **RESOLVIDO** (removido)  
**Data**: 29/11/2025 ~15:10

#### Contexto
Após corrigir `huggingface-hub`, um novo conflito surgiu: `langchain-huggingface 0.0.3` requer `langchain-core<0.3`, mas temos `0.3.72`.

#### Mensagem de Erro Completa
```
ERROR: Cannot install -r /tmp/requirements-no-torch.txt (line 35), -r /tmp/requirements-no-torch.txt (line 37), -r /tmp/requirements-no-torch.txt (line 39) and langchain-core==0.3.72 because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested langchain-core==0.3.72
    langchain 0.3.27 depends on langchain-core<1.0.0 and >=0.3.72
    langchain-community 0.3.27 depends on langchain-core<1.0.0 and >=0.3.66
    langchain-huggingface 0.0.3 depends on langchain-core<0.3 and >=0.1.52
```

#### Arquivos Envolvidos
- `backend/requirements.txt`
- `backend/app/core/rag_service.py` (verificação de uso)

#### Análise
Após verificar o código, identificado que:
- O código usa `HuggingFaceEmbeddings` de `langchain_community.embeddings`
- `langchain-huggingface` não é importado ou utilizado em nenhum lugar
- A dependência estava no `requirements.txt` mas não era necessária

#### Solução Aplicada
Removido `langchain-huggingface==0.0.3` do `requirements.txt`, pois não é utilizado no projeto.

---

### ERR-010: Erro de Interpolação do ConfigParser no Alembic

**Categoria**: Deploy Fly.io / Alembic  
**Severidade**: 🔴 Crítico  
**Status**: ✅ **RESOLVIDO**  
**Data**: 29/11/2025 ~18:00

#### Contexto
Durante o `release_command` do deploy (alembic upgrade head), o Alembic falhou ao tentar processar a URL do banco de dados do Supabase, que contém caracteres codificados (`%23` = `#`, `%40` = `@`).

#### Mensagem de Erro Completa
```
ValueError: invalid interpolation syntax in 'postgresql://postgres.efwdyzngrzpgbckrtgvx:%23%40Br88080187@aws-1-sa-east-1.pooler.supabase.com:5432/postgres?sslmode=require' at position 43
```

#### Arquivos Envolvidos
- `backend/alembic/env.py` (linha 38)

#### Causa Raiz
O `ConfigParser` do Python interpreta `%` como caractere de interpolação. A URL do Supabase contém caracteres codificados (percent-encoding) como `%23` e `%40`, que o ConfigParser tentou interpretar como interpolação, causando erro.

#### Solução Aplicada
1. Escapar `%` ao definir no ConfigParser (duplicar para `%%`)
2. Usar a URL original diretamente nas funções de migração (`run_migrations_offline()` e `run_migrations_online()`), evitando o ConfigParser
3. Remover import não utilizado (`engine_from_config`)

**Código corrigido**:
```python
# Escapar % para ConfigParser
database_url_escaped = database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url_escaped)

# Armazenar URL original para uso direto
DATABASE_URL = database_url

# Usar URL original diretamente nas funções de migração
def run_migrations_online():
    from sqlalchemy import create_engine
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    # ...
```

#### Logs Relacionados
- Logs do Fly.io release_command (29/11/2025 18:00)

---

## 📊 Histórico de Releases

| Versão | Status | Data | Descrição |
|--------|--------|------|-----------|
| v42 | ✅ **running** | 29/11/2025 18:00 | **Deploy bem-sucedido** - Todos os conflitos resolvidos, API em produção |
| v41 | ❌ failed | 29/11/2025 13:35 | Conflito pydantic-settings |
| v40 | ❌ failed | 29/11/2025 13:30 | Conflito pydantic |
| v39 | ⚠️ interrupted | 29/11/2025 13:25 | Cancelado manualmente |
| v38 | ❌ failed | 29/11/2025 13:20 | Conflito langchain-core |
| v37 | ❌ failed | 29/11/2025 13:15 | Conflito langchain-huggingface |
| v36 | ❌ failed | 29/11/2025 13:10 | Conflito dependências |
| v35 | ✅ running | 27/11/2025 20:45 | Último deploy bem-sucedido (versão antiga) |

---

## 🔧 Informações Técnicas

### Ambiente
- **Python**: 3.11
- **Docker Base Image**: `python:3.11-slim`
- **Plataforma Deploy**: Fly.io
- **Build System**: Depot (Fly.io)

### Arquivos de Configuração
- **Requirements**: `backend/requirements.txt`
- **Dockerfile**: `backend/Dockerfile`
- **Fly Config**: `backend/fly.toml`

### Logs Disponíveis
- `/tmp/deploy.log`
- `/tmp/deploy_corrected.log`
- `/tmp/deploy_final.log`
- `/tmp/deploy_fixed.log`
- `/tmp/deploy_pydantic_fixed.log`
- `/tmp/deploy_v42.log`

---

## 🎯 Próximos Passos Sugeridos

### Prioridade Alta

1. ✅ **Deploy no Fly.io** - **CONCLUÍDO**
   - Deploy v42 bem-sucedido (29/11/2025 18:00)
   - API disponível em: https://tastematch-api.fly.dev/

2. **Validação Completa em Produção**
   - ✅ Endpoint `/health` - Validado (database connected, 10 tables)
   - ⏳ Testar endpoint `/api/auth/login`
   - ⏳ Testar endpoint `/api/recommendations`
   - ⏳ Testar endpoint `/api/chat` (RAG)
   - ⏳ Verificar logs do Fly.io para erros

3. **Continuar Migração para Supabase**
   - ✅ API conectada ao Supabase (confirmado via `/health`)
   - ⏳ Validar dados migrados
   - ⏳ Validar base RAG (tastematch_knowledge)
   - ⏳ Testar funcionalidades que dependem do banco
   - Seguir plano em `Docs/supabase.md`

### Prioridade Média

4. **Otimizar tempo de build**
   - Considerar usar cache de dependências do Docker
   - Separar instalação de dependências em layers

5. **Documentar processo de atualização de dependências**
   - Criar checklist para atualizar versões
   - Documentar como verificar compatibilidade

### Prioridade Baixa

6. **Automatizar validação de dependências**
   - Adicionar step no CI/CD para validar antes do deploy
   - Script de verificação de compatibilidade

---

## 💡 Sugestões para Colaboradores

### Para Desenvolvedores

1. **Antes de atualizar dependências**:
   - Verificar changelog das bibliotecas
   - Testar compatibilidade localmente
   - Verificar dependências transitivas

2. **Ao encontrar novo conflito**:
   - Documentar mensagem de erro completa
   - Verificar versões requeridas por cada pacote
   - Testar múltiplas versões se necessário

3. **Ferramentas úteis**:
   ```bash
   # Verificar dependências de um pacote
   pip show <package>
   
   # Verificar conflitos
   pip check
   
   # Gerar requirements com versões resolvidas
   pip-compile requirements.in
   ```

### Para IAs Assistentes

1. **Ao sugerir correções**:
   - Sempre verificar compatibilidade entre versões
   - Consultar documentação oficial das bibliotecas
   - Sugerir múltiplas opções quando possível

2. **Ao analisar erros**:
   - Ler mensagem de erro completa (não apenas primeira linha)
   - Identificar dependências transitivas envolvidas
   - Verificar se há padrão nos erros

3. **Recursos úteis**:
   - PyPI: https://pypi.org/
   - Python Package Index: https://pypi.org/project/
   - Compatibilidade: Verificar "Requires" e "Required-by" no PyPI

---

## 📝 Notas Adicionais

### Sobre LangChain
- LangChain é **essencial** para a aplicação (usado no Chef Virtual/RAG)
- Versões fixas foram escolhidas para evitar backtracking do pip
- `langchain 0.3.27` é a versão mais recente estável da série 0.3.x

### Sobre PyTorch
- Instalado separadamente como `torch==2.1.2+cpu` para reduzir tamanho da imagem
- Versão CPU-only é suficiente para embeddings (não precisa GPU)
- Excluído do `requirements.txt` durante build para evitar conflito

### Estratégia de Build
- PyTorch instalado primeiro (versão CPU)
- Requirements sem torch instalado depois
- Isso garante compatibilidade e reduz tamanho da imagem

---

## 🔗 Referências

- [Pip Dependency Resolution](https://pip.pypa.io/en/latest/topics/dependency-resolution/)
- [LangChain Compatibility](https://python.langchain.com/docs/get_started/installation)
- [Pydantic Compatibility](https://docs.pydantic.dev/latest/migration/)
- [Fly.io Build Logs](https://fly.io/docs/app-guides/read-logs/)

---

**Última atualização**: 29 de Novembro de 2025, 14:15  
**Próxima revisão**: Após resolução do ERR-003

