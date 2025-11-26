# Investigação - Onboarding Não Funcionando

**Data:** 26/11/2025  
**Problema:** Endpoint `/api/onboarding/complete` retorna 404 Not Found

---

## 🔍 Diagnóstico

### Problema Identificado

O endpoint de onboarding **não está aparecendo no OpenAPI** do backend em produção, indicando que o router não está sendo registrado corretamente.

**Sintomas:**
- ❌ `curl https://tastematch-api.fly.dev/api/onboarding/complete` retorna `{"detail":"Not Found"}`
- ❌ Endpoint não aparece em `https://tastematch-api.fly.dev/openapi.json`
- ❌ Endpoint não aparece no Swagger (`/docs`)

### Causa Raiz

**Hipótese Principal:** O deploy do backend foi feito **ANTES** do código de onboarding ser commitado, então o código não estava incluído na imagem Docker.

**Evidências:**
1. ✅ Arquivos existem localmente:
   - `backend/app/api/routes/onboarding.py`
   - `backend/app/core/onboarding_service.py`
   - `backend/app/models/onboarding.py`
2. ✅ Router está registrado no `main.py`:
   ```python
   from app.api.routes import auth, users, restaurants, orders, recommendations, onboarding
   app.include_router(onboarding.router)
   ```
3. ✅ Import funciona localmente
4. ❌ Endpoint não aparece no OpenAPI em produção

---

## 🔧 Solução Aplicada

### 1. Novo Deploy do Backend

Executado novo deploy do backend para incluir o código de onboarding:

```bash
cd backend
flyctl deploy --remote-only
```

**Status:** ⏳ Deploy em andamento

### 2. Verificações Pós-Deploy

Após o deploy, verificar:

1. **Health Check:**
   ```bash
   curl https://tastematch-api.fly.dev/health
   ```

2. **OpenAPI:**
   ```bash
   curl https://tastematch-api.fly.dev/openapi.json | grep -i onboarding
   ```

3. **Swagger:**
   - Acessar: `https://tastematch-api.fly.dev/docs`
   - Verificar se endpoint `/api/onboarding/complete` aparece

4. **Teste Direto:**
   ```bash
   curl -X POST https://tastematch-api.fly.dev/api/onboarding/complete \
     -H "Content-Type: application/json" \
     -d '{}'
   ```
   - **Esperado:** Erro de autenticação (401/422), não 404
   - **Se 404:** Router ainda não registrado

---

## 📋 Checklist de Verificação

### Backend
- [x] Arquivos existem localmente
- [x] Router registrado no `main.py`
- [x] Import funciona localmente
- [ ] Novo deploy executado
- [ ] Endpoint aparece no OpenAPI
- [ ] Endpoint aparece no Swagger
- [ ] Teste de endpoint funciona (com autenticação)

### Frontend
- [x] Código commitado
- [x] Push para repositório
- [ ] Build do Netlify concluído
- [ ] Página de onboarding acessível
- [ ] Chamada de API funciona

---

## 🎯 Próximos Passos

1. **Aguardar conclusão do deploy** (2-5 minutos)
2. **Verificar endpoint no OpenAPI**
3. **Testar endpoint com autenticação**
4. **Verificar frontend** (se build do Netlify concluído)
5. **Testar fluxo completo** em produção

---

## 📝 Notas

- O deploy anterior pode não ter incluído o código de onboarding
- Novo deploy deve resolver o problema
- Se problema persistir, verificar logs do Fly.io para erros de importação

---

**Última atualização:** 26/11/2025  
**Status:** ⏳ Aguardando conclusão do deploy

