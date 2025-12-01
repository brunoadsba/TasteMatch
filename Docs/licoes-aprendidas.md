# 📚 Lições Aprendidas - TasteMatch

> **Contexto:** Este documento compila os principais aprendizados, erros e soluções encontrados durante o desenvolvimento e deploy do projeto TasteMatch. Útil para desenvolvedores e IAs futuras.

---

## 🚀 Deploy e Produção

### Problema: Driver PostgreSQL não encontrado

**Erro:**
```
sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres
```

**Causa:** Faltava o driver `psycopg2` no Dockerfile. O SQLAlchemy precisa dele para conectar ao PostgreSQL.

**Solução:**
1. Adicionar `psycopg2-binary==2.9.9` no Dockerfile e requirements.txt
2. Instalar dependência do sistema: `libpq-dev` (necessária mesmo para versão binary)
3. Ordem importante: instalar dependências do sistema ANTES de instalar psycopg2

**Lição:** Sempre verificar dependências de sistema para drivers de banco de dados em containers Docker.

---

### Problema: URL do banco em formato incorreto

**Erro:**
```
sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres
```

**Causa:** Fly.io retorna `DATABASE_URL` com formato `postgres://`, mas SQLAlchemy 2.0 requer `postgresql://`.

**Solução:**
1. Normalizar a URL antes de usar:
```python
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
```
2. Aplicar em dois lugares: `base.py` (engine do SQLAlchemy) e `alembic/env.py` (migrations)

**Lição:** Sempre normalizar URLs de banco de dados que podem vir de diferentes fontes. Verificar compatibilidade entre versões.

---

### Problema: Migration inicial vazia

**Erro:** Migration executada mas nenhuma tabela criada no banco.

**Causa:** Migration foi gerada com `alembic revision --autogenerate` mas estava vazia (só tinha `pass`).

**Solução:** Preencher manualmente a migration com `op.create_table()` para cada modelo. Ou regenerar a migration se os modelos estiverem importados corretamente no `env.py`.

**Lição:** Sempre validar migrations após gerar. Verificar se realmente criam as estruturas esperadas. Testar em ambiente isolado antes de produção.

---

### Problema: Health check falhando no deploy

**Erro:** Deploy concluído mas aplicação não responde ao health check.

**Causa:** Aplicação não estava iniciando porque faltavam secrets críticos (como DATABASE_URL, SECRET_KEY).

**Solução:** Configurar todos os secrets necessários ANTES do primeiro deploy. Se configurar após, a aplicação reinicia automaticamente mas pode falhar se ainda faltar algum.

**Lição:** Criar checklist de secrets obrigatórios antes do deploy. Validar que todos estão configurados.

---

## 🔧 Configuração e Ambiente

### Lição: CORS dinâmico é essencial

**Aprendizado:** Configurar CORS para aceitar `FRONTEND_URL` de variável de ambiente permite mudar o frontend sem redeploy do backend.

**Implementação:**
```python
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    cors_origins.append(frontend_url)
```

**Lição:** Sempre deixar configurações flexíveis via variáveis de ambiente, especialmente para URLs que mudam entre ambientes.

---

### Lição: Variáveis de ambiente do Vite precisam de rebuild

**Problema:** Configurar `VITE_API_URL` no Netlify mas o frontend ainda usa valor antigo.

**Causa:** Variáveis do Vite são injetadas no momento do BUILD, não em runtime.

**Solução:** Sempre fazer novo deploy após alterar variáveis de ambiente que começam com `VITE_`.

**Lição:** Entender que variáveis de build precisam de rebuild completo. Documentar isso claramente.

---

## 🐍 Python e FastAPI

### Lição: Validar configurações de produção no startup

**Aprendizado:** Implementar validação automática ao iniciar em produção previne erros comuns.

**Exemplo:**
```python
if settings.is_production:
    settings.validate_production_settings()
    # Valida: DEBUG=False, SECRET_KEY alterada, PostgreSQL (não SQLite)
```

**Lição:** Fail fast em produção é melhor que falhar silenciosamente. Validações automáticas são essenciais.

---

### Lição: Logging estruturado facilita debug em produção

**Aprendizado:** Usar logging estruturado (JSON em produção, legível em desenvolvimento) facilita muito o debug.

**Benefícios:**
- Facilita busca em logs
- Permite análise estruturada
- Melhora observabilidade

**Lição:** Investir em logging estruturado desde o início. Vale muito a pena em produção.

---

## 🐳 Docker

### Lição: Otimizar Dockerfile para reduzir tamanho da imagem

**Problema:** Imagem muito grande (2GB+) causando timeout durante deploy.

**Solução:**
1. Usar PyTorch CPU-only ao invés de completo (reduz de ~2GB para ~500MB)
2. Instalar em etapas e limpar cache entre elas
3. Usar `.dockerignore` para excluir arquivos desnecessários

**Lição:** Sempre otimizar Dockerfiles. Tamanho da imagem impacta velocidade de deploy e custos.

---

### Lição: Ordem de instalação importa no Docker

**Aprendizado:** Instalar dependências pesadas separadamente e limpar cache reduz tamanho final.

**Exemplo:**
```dockerfile
# PyTorch CPU-only primeiro (mais leve)
RUN pip install torch==2.1.2+cpu --index-url ...

# Depois dependências leves
RUN pip install fastapi uvicorn ...

# Por último ML pesado
RUN pip install sentence-transformers ...
```

**Lição:** Ordenar instalações do mais leve para o mais pesado. Limpar entre etapas.

---

## 🌐 Frontend e Deploy

### Lição: Testar build local antes de deploy

**Aprendizado:** Sempre rodar `npm run build` localmente antes de fazer deploy em produção.

**Benefícios:**
- Descobre erros de build antes
- Valida que tudo compila
- Economiza tempo

**Lição:** Build local é barato. Deploy falhando é caro (tempo + frustração).

---

### Lição: Preview deploy antes de produção

**Aprendizado:** Netlify permite deploy de preview (`netlify deploy` sem `--prod`).

**Benefícios:**
- Testa sem afetar produção
- Valida configurações
- Pode compartilhar para revisão

**Lição:** Sempre usar preview antes de produção, especialmente em projetos novos.

---

## 🔐 Segurança

### Lição: Gerar secrets seguros programaticamente

**Aprendizado:** Usar Python para gerar secrets ao invés de criar manualmente.

```python
import secrets
secret_key = secrets.token_urlsafe(32)
```

**Lição:** Nunca usar valores padrão ou previsíveis. Sempre gerar aleatoriamente.

---

### Lição: Validar secrets em produção

**Aprendizado:** Código deve validar que secrets não estão com valores padrão.

**Exemplo:**
```python
if self.SECRET_KEY == "change-this-secret-key-in-production-please":
    raise ValueError("SECRET_KEY deve ser alterada em produção!")
```

**Lição:** Validações automáticas previnem erros humanos comuns.

---

## 📊 Banco de Dados

### Lição: Migrations vazias precisam ser detectadas

**Problema:** Migration criada mas não gera nenhum SQL.

**Solução:** Sempre verificar conteúdo da migration antes de aplicar. Testar em ambiente isolado.

**Lição:** Não confiar cegamente em autogenerate. Sempre revisar o que será executado.

---

### Lição: Normalizar URLs de conexão

**Aprendizado:** Diferentes serviços podem retornar URLs em formatos diferentes (`postgres://` vs `postgresql://`).

**Lição:** Sempre normalizar URLs antes de usar. Criar função utilitária para isso.

---

## 🧪 Testes e Validação

### Lição: Script de validação de produção é essencial

**Aprendizado:** Criar script automatizado para validar endpoints em produção.

**Benefícios:**
- Valida tudo rapidamente
- Detecta problemas antes dos usuários
- Pode ser executado regularmente

**Lição:** Investir em validação automatizada paga muito em produção.

---

### Lição: Testar end-to-end após deploy

**Aprendizado:** Não basta backend e frontend funcionarem separadamente. Precisam funcionar juntos.

**Testes essenciais:**
- Login end-to-end (frontend → backend → banco)
- Requisições protegidas
- CORS funcionando
- Variáveis de ambiente corretas

**Lição:** Sempre testar fluxo completo após deploy.

---

## 📝 Documentação

### Lição: Documentar durante o processo, não depois

**Aprendizado:** Documentar enquanto desenvolve/deploy é muito mais fácil e preciso que depois.

**Benefícios:**
- Informações ainda estão frescas
- Detalhes importantes não são esquecidos
- Facilita troubleshooting futuro

**Lição:** Documentação é parte do processo, não etapa separada.

---

### Lição: Documentos separados para diferentes propósitos

**Aprendizado:** Ter documentos focados:
- `DEPLOY.md` - Guia passo a passo
- `RESUMO_DEPLOY_FINAL.md` - Resumo executivo
- `VALIDACAO_PRODUCAO.md` - Resultados de testes
- `LICOES_APRENDIDAS.md` - Este documento

**Lição:** Cada documento tem propósito específico. Não tentar colocar tudo em um só lugar.

---

## 🔄 Processo e Metodologia

### Lição: Um passo de cada vez é mais efetivo

**Aprendizado:** Fazer deploy passo a passo, validando cada etapa, é melhor que tentar tudo de uma vez.

**Benefícios:**
- Identifica problemas rapidamente
- Facilita aprendizado
- Reduz estresse

**Lição:** Deploy incremental com validação contínua > deploy completo sem validação.

---

### Lição: Checklist ajuda muito

**Aprendizado:** Ter checklist de validação evita esquecer passos importantes.

**Exemplo de checklist:**
- [ ] Build local funciona
- [ ] Variáveis de ambiente configuradas
- [ ] Secrets configurados
- [ ] Deploy executado
- [ ] Health check passando
- [ ] Endpoints validados
- [ ] Integração testada

**Lição:** Checklists são simples mas muito efetivos. Sempre usar.

---

## 🤖 IA e Automação

### Lição: IA é ferramenta, não substituto

**Contexto:** Este projeto foi desenvolvido com ajuda da IA (Cursor AI).

**Aprendizado:**
- IA acelera muito o desenvolvimento
- Mas ainda precisa de compreensão técnica para usar bem
- IA ajuda a resolver problemas, mas entendimento é essencial

**Lição:** Usar IA como assistente inteligente, não como oráculo. Sempre entender o que está sendo feito.

---

### Lição: IA ajuda a aprender fazendo

**Aprendizado:** Desenvolver com IA permite construir projetos complexos enquanto aprende.

**Benefícios:**
- Exposição a práticas modernas
- Resolução de problemas reais
- Aprendizado prático

**Lição:** Projetos reais > tutoriais. IA facilita projetos reais para aprendizes.

---

## 🎯 Resumo das Principais Lições

1. **Sempre normalizar URLs e dados de entrada** - Diferentes serviços podem retornar formatos diferentes
2. **Validar em produção no startup** - Fail fast é melhor que falhar silenciosamente
3. **Variáveis de build precisam de rebuild** - Entender ciclo de vida das variáveis
4. **Testar build local antes de deploy** - Economiza muito tempo
5. **Documentar durante o processo** - Não depois
6. **Um passo de cada vez** - Deploy incremental com validação
7. **Logging estruturado vale a pena** - Facilita muito debug em produção
8. **Checklists são simples mas efetivos** - Use sempre
9. **IA é ferramenta poderosa** - Mas precisa de compreensão técnica
10. **Otimizar Dockerfiles** - Tamanho importa para velocidade e custos

---

## 💡 Dicas para Próximos Projetos

### Antes de Começar
- [ ] Definir estrutura de pastas clara
- [ ] Configurar variáveis de ambiente desde o início
- [ ] Planejar como será o deploy

### Durante o Desenvolvimento
- [ ] Testar build localmente regularmente
- [ ] Documentar decisões importantes
- [ ] Validar configurações automaticamente

### Antes do Deploy
- [ ] Checklist completo de configurações
- [ ] Testar build local
- [ ] Validar todas as dependências

### Após o Deploy
- [ ] Validar endpoints automaticamente
- [ ] Testar end-to-end
- [ ] Documentar URLs e configurações
- [ ] Criar resumo do que foi feito

---

## 🔗 Referências Úteis

- [Fly.io Docs](https://fly.io/docs)
- [Netlify Docs](https://docs.netlify.com)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)

---

---

## 🎯 Onboarding e Cold Start

### Lição: Onboarding resolve cold start de forma elegante

**Aprendizado:** Implementar onboarding gamificado permite gerar vetor sintético de preferências antes do primeiro pedido, resolvendo o problema de cold start.

**Implementação:**
- Usuário seleciona 1-5 culinárias preferidas
- Sistema calcula centróide vetorial dos melhores restaurantes dessas culinárias
- Vetor sintético salvo em `user_preferences.preference_embedding`
- Recomendações personalizadas disponíveis desde o primeiro acesso

**Benefícios:**
- Melhor experiência do usuário (não precisa esperar histórico)
- Recomendações relevantes desde o início
- Reduz taxa de abandono de novos usuários

**Lição:** Cold start não precisa ser problema. Onboarding bem projetado resolve isso elegantemente.

---

### Lição: Alinhar limites entre frontend e backend

**Problema:** Frontend limitava seleção a 3 culinárias, backend aceitava até 5.

**Causa:** Desenvolvimento paralelo sem sincronização de regras de negócio.

**Solução:** 
1. Verificar backend primeiro (fonte de verdade)
2. Alinhar frontend com backend
3. Atualizar mensagens de UI para refletir limite correto

**Lição:** Sempre verificar backend como fonte de verdade para regras de negócio. Frontend deve seguir backend, não o contrário.

---

### Lição: Atualizar recomendações após onboarding

**Problema:** Após completar onboarding, recomendações não atualizavam automaticamente.

**Causa:** Navegação para dashboard não disparava refresh de dados.

**Solução:**
- Passar `state: { refreshRecommendations: true }` na navegação
- Dashboard detecta state e chama `refresh()` automaticamente
- Limpar state após uso para evitar refresh em navegações futuras

**Lição:** Fluxos de onboarding devem atualizar dados automaticamente. Usuário não deve precisar recarregar página manualmente.

---

## 🌐 Frontend e CORS

### Problema: Frontend em produção usando localhost

**Erro:**
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'https://tastematch.netlify.app' has been blocked by CORS policy
```

**Causa:** `API_BASE_URL` no frontend não detectava ambiente de produção corretamente.

**Solução:**
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? 'https://tastematch-api.fly.dev' : 'http://localhost:8000');
```

**Lição:** Sempre detectar ambiente automaticamente. Não confiar apenas em variáveis de ambiente que podem não estar configuradas.

---

### Lição: Testar CORS em produção é essencial

**Aprendizado:** CORS pode funcionar localmente mas falhar em produção se URLs não estiverem corretas.

**Validação:**
- Testar requisições do navegador em produção
- Verificar console do navegador para erros de CORS
- Validar que `API_BASE_URL` está correto em cada ambiente

**Lição:** Sempre testar integração frontend-backend em produção. CORS é um problema comum e fácil de detectar.

---

## 🔄 Deploy e Integração

### Lição: Deploy não garante que código está disponível

**Problema:** Deploy concluído mas endpoint não disponível.

**Causa:** 
- Deploy executado antes do commit do código
- Deploys interrompidos não completam
- Código local diferente do código deployado

**Solução:**
1. Verificar commits antes de deploy
2. Verificar logs do deploy para confirmar conclusão
3. Validar que código está no repositório antes de deployar
4. Forçar novo deploy se necessário

**Lição:** Deploy bem-sucedido não significa código atualizado. Sempre validar que código correto foi deployado.

---

### Lição: CLI deploy é mais confiável que automático

**Aprendizado:** Quando deploy automático não está configurado, usar CLI garante controle total.

**Benefícios:**
- Controle sobre quando deployar
- Visibilidade completa do processo
- Pode forçar deploy mesmo com código não commitado (se necessário)

**Lição:** CLI deploy dá mais controle e visibilidade. Use quando precisar de precisão.

---

### Problema: Deploy travado no Netlify

**Erro:** Deploy iniciado mas fica em "Deploy in progress" indefinidamente, sem concluir.

**Causa:**
- Deploy manual pode entrar em conflito com auto-deploy
- Branch de feature pode não estar configurada para auto-deploy
- Processo de build pode estar travado internamente
- CLI do Netlify pode não retornar output quando há problemas

**Solução:**
1. **Cancelar deploys travados** - No dashboard do Netlify, cancelar todos os deploys em progresso
2. **Verificar build local primeiro** - Sempre rodar `npm run build` localmente antes de deployar
3. **Fazer deploy direto** - Usar `netlify deploy --prod --dir=frontend/dist` com build já compilado
4. **Alternativa: Merge para main** - Se auto-deploy estiver configurado apenas para main, fazer merge e deixar o Netlify fazer deploy automaticamente

**Processo recomendado:**
```bash
# 1. Build local primeiro
cd frontend && npm run build

# 2. Verificar que build foi bem-sucedido
ls -la dist/

# 3. Deploy direto do diretório dist
cd .. && netlify deploy --prod --dir=frontend/dist
```

**Lição:** 
- Sempre cancelar deploys travados antes de tentar novo deploy
- Build local antes de deploy evita problemas
- Deploy direto de diretório compilado é mais confiável que deixar Netlify fazer build
- Dashboard do Netlify é mais confiável que CLI para ver status real

---

## 📝 Documentação

### Lição: Atualizar documentação após cada feature

**Aprendizado:** Documentação desatualizada causa confusão e perda de tempo.

**Processo:**
1. Atualizar README.md com novas funcionalidades
2. Atualizar SPEC.md com novos endpoints
3. Atualizar STATUS_PROJETO.md com sprints completos
4. Criar documentos específicos para problemas resolvidos

**Lição:** Documentação é parte do desenvolvimento, não etapa separada. Atualizar junto com código.

---

### Lição: Documentos específicos para problemas complexos

**Aprendizado:** Criar documentos focados para problemas complexos facilita troubleshooting futuro.

**Exemplos:**
- `CORRECAO_CORS.md` - Detalhes da correção de CORS
- `INVESTIGACAO_ONBOARDING.md` - Processo de investigação
- `SOLUCAO_ONBOARDING.md` - Solução implementada

**Lição:** Documentos específicos são mais úteis que tentar colocar tudo em um documento geral.

---

## 🎨 UX e Frontend

### Lição: Tooltips devem ser concisos

**Problema:** Tooltip do "Modo Demo" muito longo e confuso.

**Solução:** Reduzir para mensagem direta e objetiva:
- Antes: "Explore o TasteMatch sem criar conta. Simule pedidos e veja recomendações personalizadas baseadas em suas escolhas."
- Depois: "Explore o TasteMatch sem criar conta. Simule pedidos e veja recomendações personalizadas."

**Lição:** Tooltips devem ser informativos mas concisos. Menos é mais.

---

### Lição: Padronizar cálculos de display

**Problema:** Similaridade score mostrado de formas diferentes (`toFixed(0)` vs `Math.round()`).

**Causa:** Código desenvolvido em momentos diferentes sem padronização.

**Solução:** 
- Escolher um método (`Math.round()`)
- Aplicar consistentemente em todos os componentes
- Documentar padrão escolhido

**Lição:** Padronizar cálculos e formatação desde o início. Consistência melhora UX.

---

## 🔧 Backend e Integração

### Lição: Importar routers explicitamente

**Problema:** Endpoint de onboarding retornava 404 mesmo após deploy.

**Causa:** Router não estava sendo importado em `__init__.py`.

**Solução:**
```python
from . import auth, users, restaurants, orders, recommendations, onboarding
__all__ = ["auth", "users", "restaurants", "orders", "recommendations", "onboarding"]
```

**Lição:** Sempre verificar que novos routers estão importados e incluídos na lista de exports.

---

### Lição: Validar tipos de dados entre frontend e backend

**Problema:** Frontend oferecia culinárias que não existiam no banco.

**Causa:** Seed data do backend diferente das opções do frontend.

**Solução:**
1. Verificar seed data do backend primeiro
2. Alinhar opções do frontend com dados reais
3. Remover opções que não existem
4. Adicionar opções que faltam

**Lição:** Frontend deve refletir dados reais do backend. Sempre validar contra fonte de dados.

---

## 🎯 Resumo das Novas Lições

1. **Onboarding resolve cold start elegantemente** - Não precisa esperar histórico
2. **Alinhar limites entre frontend e backend** - Backend é fonte de verdade
3. **Atualizar dados após onboarding** - UX deve ser fluida
4. **Detectar ambiente automaticamente** - Não confiar apenas em variáveis
5. **Testar CORS em produção** - Problema comum e fácil de detectar
6. **Deploy não garante código atualizado** - Sempre validar
7. **CLI deploy é mais confiável** - Mais controle e visibilidade
8. **Cancelar deploys travados antes de novo deploy** - Evita conflitos
9. **Build local antes de deploy** - Economiza tempo e evita problemas
10. **Deploy direto de diretório compilado** - Mais confiável que build no Netlify
11. **Atualizar documentação junto com código** - Não deixar para depois
12. **Tooltips devem ser concisos** - Menos é mais
13. **Padronizar cálculos de display** - Consistência melhora UX
14. **Importar routers explicitamente** - Verificar sempre
15. **Validar tipos de dados entre frontend e backend** - Alinhar sempre

---

---

## 🎨 UX Mobile e Acessibilidade

### Problema: Menu mobile não fecha após ação

**Problema:** Usuário clica em "Ativar/Desativar Modo Demo" no menu mobile, mas o menu permanece aberto após a ação.

**Causa:** Menu mobile (Sheet) não estava sendo fechado programaticamente após mudança de estado.

**Solução:**
1. Expor função global `window.__closeMobileMenu()` no componente `MobileMenu`
2. Chamar função antes de atualizar estado no `Dashboard`
3. Adicionar redirecionamento e scroll para topo após ação
4. Usar `setTimeout` para garantir que menu fecha antes da navegação

**Implementação:**
```typescript
// MobileMenu.tsx
useEffect(() => {
  if (open) {
    (window as any).__closeMobileMenu = () => setOpen(false);
  }
}, [open]);

// Dashboard.tsx
const handleDemoModeToggle = () => {
  (window as any).__closeMobileMenu?.();
  setIsDemoMode(!isDemoMode);
  setTimeout(() => {
    navigate('/dashboard', { replace: true });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, 100);
};
```

**Lição:** Componentes de UI devem permitir controle programático. Sempre expor funções de controle quando necessário.

---

### Problema: Avisos de acessibilidade no console

**Erro:**
```
Warning: Missing `Description` or `aria-describedby={undefined}` for {DialogContent}
```

**Causa:** Radix UI Dialog (usado pelo Sheet) requer `DialogDescription` ou `aria-describedby` para acessibilidade.

**Solução:** Adicionar `SheetDescription` com classe `sr-only` (screen reader only):
```tsx
<SheetDescription className="sr-only">
  Menu de navegação mobile
</SheetDescription>
```

**Lição:** 
- Sempre verificar avisos de acessibilidade no console
- Componentes de diálogo precisam de descrição para leitores de tela
- Classe `sr-only` oculta visualmente mas mantém acessibilidade

---

---

## 🗄️ Migração para Supabase (29/11/2025)

### Problema: Conflitos de Dependências Python durante Deploy

**Contexto:** Durante a migração para Supabase, múltiplos conflitos de dependências Python impediram o deploy da API no Fly.io.

**Erros Encontrados:**
1. `langchain-core` vs `langchain` - versão incompatível
2. `pydantic` vs `langchain` - versão muito antiga
3. `pydantic-settings` vs `pydantic` - incompatibilidade
4. `langchain-groq` vs `langchain-core` - versão muito antiga
5. `huggingface-hub` vs `langchain-huggingface` - conflito de versões
6. `langchain-huggingface` vs `langchain-core` - incompatibilidade fundamental

**Solução Aplicada:**
1. **Abordagem incremental**: Resolver um conflito por vez, testando após cada correção
2. **Análise de dependências**: Verificar requisitos de cada biblioteca antes de atualizar
3. **Remoção de dependências não utilizadas**: Identificar e remover `langchain-huggingface` (não usado no código)
4. **Atualização estratégica**: Atualizar apenas o necessário, não tudo de uma vez

**Versões Finais:**
- `pydantic==2.7.4` (compatível com langchain 0.3.27)
- `pydantic-settings==2.12.0` (compatível com pydantic 2.7.4)
- `langchain-core==0.3.72` (requerido por langchain 0.3.27)
- `langchain-groq>=0.3.0` (compatível com langchain-core 0.3.72)
- `huggingface-hub>=0.16.4` (suficiente para transformers e sentence-transformers)
- `langchain-huggingface` removido (não utilizado)

**Lição:** 
- Resolver conflitos de dependências incrementalmente é mais seguro que atualizar tudo de uma vez
- Sempre verificar se dependências declaradas são realmente utilizadas no código
- Testar build local antes de deploy em produção
- Documentar cada correção para facilitar troubleshooting futuro

---

### Problema: Erro de Interpolação do ConfigParser no Alembic

**Erro:**
```
ValueError: invalid interpolation syntax in 'postgresql://...%23%40...' at position 43
```

**Causa:** O `ConfigParser` do Python interpreta `%` como caractere de interpolação. URLs do Supabase contêm caracteres codificados (percent-encoding) como `%23` (`#`) e `%40` (`@`).

**Solução:**
1. Escapar `%` ao definir no ConfigParser (duplicar para `%%`)
2. Usar URL original diretamente nas funções de migração, evitando o ConfigParser
3. Armazenar URL original em variável separada para uso direto

**Implementação:**
```python
# Escapar para ConfigParser
database_url_escaped = database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url_escaped)

# Armazenar URL original para uso direto
DATABASE_URL = database_url

# Usar URL original nas funções de migração
def run_migrations_online():
    from sqlalchemy import create_engine
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)
```

**Lição:** 
- ConfigParser do Python tem comportamento especial com `%` (interpolação)
- URLs com percent-encoding precisam ser tratadas cuidadosamente
- Usar valores originais diretamente quando possível, evitando processamento intermediário

---

### Problema: Embeddings Não Migrados

**Contexto:** Após migração do banco de dados para Supabase, os embeddings dos restaurantes não foram migrados (0 restaurantes com embeddings).

**Causa:** 
- Embeddings são gerados dinamicamente pelo código Python
- Não são parte do dump SQL do banco
- Precisam ser regenerados após migração

**Solução:**
1. Executar script de geração de embeddings: `python scripts/generate_embeddings.py`
2. Script processa 1 restaurante por vez para evitar problemas de memória
3. Validação após geração para confirmar sucesso

**Lição:**
- Embeddings gerados dinamicamente não são migrados automaticamente
- Sempre verificar dados derivados após migração
- Ter scripts de regeneração prontos para dados computados

---

### Lição: Configuração Explícita é Melhor que Implícita

**Aprendizado:** Usar variável de ambiente `DB_PROVIDER=supabase` em vez de detecção automática.

**Benefícios:**
- Configurações otimizadas aplicadas corretamente
- Facilita debugging (sabe exatamente qual provider está sendo usado)
- Segue princípios 12-factor app
- Evita detecção incorreta baseada em padrões de URL

**Implementação:**
```python
IS_SUPABASE = os.getenv("DB_PROVIDER", "").lower() == "supabase"

if IS_SUPABASE:
    pool_size = 20
    max_overflow = 0
    pool_recycle = 300
    connect_args = {"sslmode": "require", ...}
```

**Lição:** Configuração explícita via variáveis de ambiente é mais confiável e manutenível que detecção automática.

---

### Lição: Connection Pooling do Supabase Requer Configuração Especial

**Aprendizado:** Supabase usa PgBouncer em Transaction Mode, que requer configurações específicas.

**Configurações Importantes:**
- `max_overflow=0` - Evitar overflow agressivo em Transaction Mode
- `pool_recycle=300` - Reciclar conexões mais rápido (pooler gerencia isso)
- `pool_size=20` - Supabase aguenta mais conexões que Fly Postgres
- `sslmode=require` - SSL obrigatório no Supabase
- `keepalives` configurados - Manter conexões vivas

**Lição:** 
- Connection poolers (como PgBouncer) têm comportamentos específicos
- Transaction Mode não suporta prepared statements em alguns casos
- Sempre consultar documentação do provider para configurações otimizadas

---

### Lição: Testar Build Local Antes de Deploy

**Aprendizado:** Durante resolução de conflitos de dependências, testar build Docker localmente economizou muito tempo.

**Processo:**
```bash
# Build local
docker build -t tastematch-test .

# Validar dependências
docker run --rm tastematch-test pip check

# Testar imports críticos
docker run --rm tastematch-test python -c "import slowapi; import langchain; ..."
```

**Benefícios:**
- Detecta problemas antes do deploy
- Mais rápido que deploy no Fly.io
- Permite iteração rápida
- Economiza recursos do Fly.io

**Lição:** Sempre testar build local antes de deploy, especialmente quando há mudanças em dependências.

---

### Lição: Documentar Erros e Soluções Durante o Processo

**Aprendizado:** Criar documento estruturado de erros (`erros-deploy-migracao.md`) facilitou muito o troubleshooting.

**Estrutura do Documento:**
- Resumo executivo com estatísticas
- Cada erro com ID, categoria, severidade, status
- Mensagem de erro completa
- Versões antes/depois
- Solução aplicada
- Logs relacionados

**Benefícios:**
- Facilita colaboração (outros devs/IAs podem ajudar)
- Histórico completo para referência futura
- Identifica padrões de problemas
- Ajuda a priorizar correções

**Lição:** Documentar problemas e soluções durante o processo é muito mais eficiente que tentar lembrar depois.

---

### Resumo das Lições da Migração Supabase

1. **Resolver conflitos incrementalmente** - Um por vez é mais seguro
2. **Verificar dependências não utilizadas** - Remover o que não é usado
3. **Testar build local antes de deploy** - Economiza tempo e recursos
4. **Configuração explícita > detecção automática** - Mais confiável
5. **Connection poolers requerem configuração especial** - Consultar documentação
6. **Embeddings precisam ser regenerados** - Não são parte do dump SQL
7. **ConfigParser e percent-encoding não combinam** - Usar valores originais quando possível
8. **Documentar durante o processo** - Facilita troubleshooting e colaboração

---

## 🎤 Áudio e Chat

### Problema: Erro 500 no endpoint /api/chat/ - reasoning_format

**Erro:**
```
TypeError: Completions.create() got an unexpected keyword argument 'reasoning_format'
```

**Causa:** A versão `langchain-groq==0.3.3` tenta passar parâmetros de reasoning (`reasoning_format`, `reasoning_effort`) para modelos que não suportam (como `llama-3.1-8b-instant`). Esses parâmetros são para modelos de reasoning como DeepSeek R1.

**Solução:**
1. Criar wrapper `ChatGroqFiltered` que intercepta chamadas ao cliente Groq
2. Aplicar monkey patch no método `self.client.create()` (não em `self.client.chat.completions.create()`)
3. Filtrar parâmetros não suportados antes da requisição HTTP

**Implementação:**
```python
class ChatGroqFiltered(ChatGroq):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_client_patch()
    
    def _apply_client_patch(self):
        if hasattr(self.client, 'create'):
            original_create = self.client.create
            def filtered_create(*args, **kwargs):
                for param in ['reasoning_format', 'reasoning_effort']:
                    kwargs.pop(param, None)
                return original_create(*args, **kwargs)
            self.client.create = filtered_create
```

**Lição:** 
- Interceptar no último momento possível (cliente Groq) garante que parâmetros sejam removidos independente de onde foram adicionados
- `self.client` já é `groq.resources.chat.completions.Completions`, não o cliente completo
- Monkey patch no método correto é essencial

---

### Problema: 'Groq' object has no attribute 'audio'

**Erro:**
```
'Groq' object has no attribute 'audio'
Exception: Erro na API Groq ao transcrever áudio: 'Groq' object has no attribute 'audio'
```

**Causa:** Versão do `groq` SDK muito antiga (`0.4.1`) não tinha suporte para API de áudio (transcriptions). A versão mais recente é `0.36.0`.

**Solução:**
1. Atualizar `groq` de `0.4.1` para `0.36.0`
2. Verificar que a API de áudio está disponível: `client.audio.transcriptions`

**Verificação:**
```python
client = groq.Groq(api_key='...')
hasattr(client, 'audio')  # True na versão 0.36.0
client.audio.transcriptions  # Disponível
```

**Lição:** 
- Sempre verificar versões de SDKs quando APIs não estão disponíveis
- Usar `pip index versions <package>` para ver versões disponíveis
- Versões muito antigas podem não ter features mais recentes

---

### Problema: Caminho incorreto do endpoint de áudio

**Erro:** Arquivos de áudio não eram servidos corretamente.

**Causa:** O código gerava URLs como `/api/audio/{filename}`, mas o endpoint está registrado em `/api/chat/audio/{filename}` (router tem prefixo `/api/chat`).

**Solução:**
```python
# Antes (incorreto)
audio_url = f"/api/audio/{audio_filename}"

# Depois (correto)
audio_url = f"/api/chat/audio/{audio_filename}"
```

**Lição:** Sempre considerar o prefixo do router ao gerar URLs de endpoints.

---

### Problema: asyncio.run() dentro de endpoint async

**Erro:** Conflito ao usar `text_to_speech()` (síncrono) que internamente usa `asyncio.run()` dentro de endpoint async.

**Causa:** Endpoints async já rodam em loop de eventos. `asyncio.run()` tenta criar novo loop, causando conflito.

**Solução:** Usar versão assíncrona diretamente:
```python
# Antes (causa conflito)
audio_path = audio_service.text_to_speech(response["answer"])

# Depois (correto)
audio_path = await audio_service.text_to_speech_async(response["answer"])
```

**Lição:** 
- Nunca usar `asyncio.run()` dentro de código que já está em contexto async
- Sempre usar versões async diretamente quando disponíveis

---

### Resumo das Lições de Áudio e Chat

1. **Interceptar no último momento** - Monkey patch no cliente Groq garante remoção de parâmetros
2. **Verificar versões de SDK** - APIs podem não estar disponíveis em versões antigas
3. **Considerar prefixos de router** - URLs devem incluir prefixo completo do router
4. **Evitar asyncio.run() em contexto async** - Usar versões async diretamente
5. **Logging detalhado** - Facilita identificar problemas rapidamente

---

---

## 🎯 Chef Virtual - Melhorias de Inteligência e Formatação

### Problema: Filtro Semântico Muito Permissivo

**Contexto:** O sistema recomendava restaurantes irrelevantes (ex: "Casa do Pão de Queijo" para "hamburguer gourmet").

**Causa:**
- Palavras genéricas como "gourmet", "bom", "melhor" eram tratadas como tags
- Stopwords como "quero", "um", "uma" estavam sendo incluídas no processamento
- Correspondência parcial usava todas as palavras, não apenas tags principais
- Verificações de nome e descrição não eram restritivas o suficiente

**Solução:**
1. **Filtro de Stopwords Expandido:**
   ```python
   stopwords = {'quero', 'queria', 'gostaria', 'preciso', 'um', 'uma', 'uns', 'umas', 
                'o', 'a', 'os', 'as', 'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 
                'nas', 'nos', 'para', 'com', 'sem', 'por', 'sobre'}
   ```

2. **Remoção de Palavras Genéricas:**
   ```python
   generic_words = {'gourmet', 'bom', 'melhor', 'melhores', 'ótimo', 'otimo', 
                    'excelente', 'top', 'show'}
   # Não são mais tratadas como tags
   ```

3. **Correspondência Parcial Restritiva:**
   - Apenas tags principais do mapeamento (ex: 'hamburguer' → ['hamburguer', 'burger', 'hamburgueria'])
   - Não usa palavras genéricas para match parcial
   - Verificações de nome e descrição também usam apenas tags principais

**Lição:** 
- Filtros semânticos devem ser rigorosos para evitar recomendações incorretas
- Palavras genéricas não devem ser tratadas como tags específicas
- Sempre usar apenas tags principais do mapeamento para correspondência parcial

---

### Problema: Agente Continuava Conversas de Contextos Anteriores

**Contexto:** O agente respondia perguntas antigas do histórico ao invés de focar na pergunta atual.

**Causa:**
- Histórico muito extenso (10 mensagens) sem filtro
- Prompt não instruía explicitamente para focar apenas na pergunta atual
- Histórico era usado mesmo para cumprimentos simples

**Solução:**
1. **Limitação de Histórico:**
   - Reduzido de 10 para 4 mensagens (padrão)
   - Para perguntas sobre comida: apenas 2 mensagens (última interação)
   - Para cumprimentos: histórico vazio (0 mensagens)

2. **Filtro Inteligente de Histórico:**
   ```python
   # Detectar cumprimentos curtos
   short_greetings = ['oi', 'olá', 'ola', 'hey', 'hi', 'tudo bem', 'tudo bom']
   if is_short_greeting:
       return []  # Sem histórico para cumprimentos
   
   # Para perguntas sobre comida, incluir apenas última interação
   if i < 2:  # Apenas última pergunta + resposta
       relevant_messages.append(msg)
   ```

3. **Instruções Explícitas no Prompt:**
   - "⚠️ FOQUE APENAS NA PERGUNTA ATUAL"
   - "NÃO continue conversas anteriores do histórico"
   - "Histórico (apenas referência - IGNORE se não relevante)"

**Lição:**
- Histórico deve ser limitado e filtrado por relevância
- Instruções explícitas no prompt são essenciais para modelos menores
- Cumprimentos não devem usar histórico para evitar continuar conversas antigas

---

### Problema: Agente Gerava Recomendações para Cumprimentos

**Contexto:** Quando usuário enviava "oi" ou "tudo bem?", o agente gerava recomendações de restaurantes.

**Causa:**
- `detect_social_interaction()` não era chamada antes da busca RAG
- Busca RAG era executada mesmo para cumprimentos
- Respostas eram muito verbosas e mencionavam restaurantes

**Solução:**
1. **Chamada Antecipada de Detecção Social:**
   ```python
   # CRÍTICO: Detectar interações sociais ANTES de buscar RAG
   social_response = detect_social_interaction(question)
   if social_response:
       return {"answer": social_response, ...}  # Retorna imediatamente
   ```

2. **Respostas Simplificadas:**
   - "Olá! Em que posso ajudar?"
   - "Oi! Como posso ajudar?"
   - Não menciona restaurantes na resposta inicial

3. **Detecção de Perguntas sobre Identidade:**
   ```python
   identity_keywords = [
       "qual seu nome", "qual é seu nome", "quem é você",
       "como você se chama", "você é quem"
   ]
   # Resposta: "Sou o Chef Virtual! Quer que eu recomende algo?"
   ```

**Lição:**
- Detectar interações sociais antes de qualquer processamento pesado
- Respostas sociais devem ser simples e diretas
- Não gerar recomendações para interações que não pedem recomendações

---

### Problema: Formatação de Respostas com Artefatos e Texto Verboso

**Contexto:** Respostas continham texto introdutório verboso ("Churrasco é um prato delicioso..."), descrições duplicadas, emojis soltos e metadados técnicos.

**Causa:**
- LLM (llama-3.1-8b-instant) não seguia consistentemente instruções de formatação
- Pós-processamento não removia todos os artefatos
- Metadados técnicos do RAG vazavam para a resposta final

**Solução:**
1. **Limpeza Agressiva de Artefatos:**
   ```python
   # Remover texto introdutório verboso
   verbose_patterns = [
       r'(?i)^.*?churrasco\s+é\s+um\s+prato[^.!?]*!?\s*',
       r'(?i)^.*?posso\s+sugerir[^.]*\.\s*',
       r'📄\s+visitar[^.]*\.\s*',
   ]
   
   # Remover emojis soltos
   text = re.sub(r'^\s*[🔥🍝🍣🍔🍕🌮🥙🦞⭐]\s*$', '', text, flags=re.MULTILINE)
   ```

2. **Remoção Destrutiva de Descrições:**
   ```python
   # Remover descrições longas do LLM antes de inserir cards formatados
   pattern = rf"{name_var}\s+(é|é um|é uma|tem|oferece|clássico)[^.!?]*[.!?]?\s*[🔥⭐]*.*?(?=\n\n|━━|\d+\.\d+/\d+\.\d+|$)"
   cleaned_answer = re.sub(pattern, "", cleaned_answer)
   ```

3. **Limpeza de Metadados Técnicos:**
   ```python
   # Remover padrões técnicos que vazam do RAG
   technical_patterns = [
       r'Restaurante:\s*',
       r'Tipo de culinária:\s*',
       r'Tags e pratos relacionados:\s*',
   ]
   ```

4. **Pós-processamento Sempre Aplicado:**
   - Lógica invertida: "na dúvida, reformate"
   - Validação estrutural estrita
   - Se estrutura não é perfeita, aplica formatação visual

**Lição:**
- Modelos menores precisam de pós-processamento robusto
- Remoção destrutiva é necessária para garantir qualidade
- Metadados técnicos devem ser removidos antes e depois do pós-processamento
- Lógica invertida ("na dúvida, reformate") garante qualidade consistente

---

### Resumo das Lições do Chef Virtual

1. **Filtro semântico deve ser rigoroso** - Evitar palavras genéricas e usar apenas tags principais
2. **Histórico deve ser limitado e filtrado** - Focar apenas na pergunta atual
3. **Detectar interações sociais antes de RAG** - Não processar desnecessariamente
4. **Pós-processamento robusto é essencial** - Modelos menores precisam de ajuda
5. **Remoção destrutiva garante qualidade** - Remover antes de inserir conteúdo formatado
6. **Instruções explícitas no prompt** - Modelos menores precisam de orientação clara
7. **Lógica invertida para formatação** - "Na dúvida, reformate" garante consistência

---

**Última atualização:** 29/11/2025  
**Projeto:** TasteMatch - Agente de Recomendação Inteligente  
**Fase:** 17 - Melhorias de Inteligência e Formatação do Chef Virtual ✅

