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
8. **Atualizar documentação junto com código** - Não deixar para depois
9. **Tooltips devem ser concisos** - Menos é mais
10. **Padronizar cálculos de display** - Consistência melhora UX
11. **Importar routers explicitamente** - Verificar sempre
12. **Validar tipos de dados entre frontend e backend** - Alinhar sempre

---

**Última atualização:** 26/11/2025  
**Projeto:** TasteMatch - Agente de Recomendação Inteligente  
**Fase:** 13 - Onboarding Gamificado + Correção de CORS ✅

