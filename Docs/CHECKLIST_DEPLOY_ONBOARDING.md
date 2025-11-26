# Checklist de Deploy - Onboarding Gamificado

## ✅ Pré-Deploy: Verificações

### 1. Backend ✅
- [x] Backend compila sem erros
- [x] Endpoint `/api/onboarding/complete` implementado
- [x] Router de onboarding registrado no `main.py`
- [x] Import de onboarding no `__init__.py` dos routes
- [x] CORS configurado para Netlify

### 2. Frontend ✅
- [x] Frontend compila sem erros
- [x] Página de onboarding implementada
- [x] Rota `/onboarding` registrada no `App.tsx`
- [x] Redirecionamento após cadastro funcionando
- [x] Atualização dinâmica de recomendações implementada

### 3. Variáveis de Ambiente

**Backend (Fly.io):**
- [x] `GROQ_API_KEY` - Já configurada
- [x] `JWT_SECRET_KEY` - Já configurada
- [x] `SECRET_KEY` - Já configurada
- [x] `DATABASE_URL` - Já configurada
- [ ] **Nenhuma nova variável necessária** ✅

**Frontend (Netlify):**
- [x] `VITE_API_URL` - Já configurada (se necessário)
- [ ] **Nenhuma nova variável necessária** ✅

---

## 🚀 Deploy

### Backend (Fly.io)

**Comando:**
```bash
cd backend
flyctl deploy --remote-only
```

**Verificações após deploy:**
- [ ] Health check: `https://tastematch-api.fly.dev/health`
- [ ] Swagger: `https://tastematch-api.fly.dev/docs`
- [ ] Endpoint onboarding: `https://tastematch-api.fly.dev/api/onboarding/complete` (requer auth)

**Teste rápido:**
```bash
# Fazer login e testar endpoint
curl -X POST https://tastematch-api.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@example.com","password":"123456"}'

# Usar token retornado para testar onboarding
curl -X POST https://tastematch-api.fly.dev/api/onboarding/complete \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"selected_cuisines":["italiana","japonesa"],"price_preference":"medium"}'
```

### Frontend (Netlify)

**Deploy automático via Git:**
- Push para branch principal → Deploy automático

**Ou deploy manual:**
```bash
cd frontend
npm run build
npx netlify deploy --prod --dir=dist
```

**Verificações após deploy:**
- [ ] Site carrega: `https://tastematch.netlify.app`
- [ ] Página de login funciona
- [ ] Cadastro redireciona para onboarding
- [ ] Onboarding funciona em 3 etapas
- [ ] Dashboard mostra recomendações após onboarding

---

## 🧪 Testes Pós-Deploy

### Teste 1: Fluxo Completo
1. Acessar `https://tastematch.netlify.app`
2. Criar conta nova
3. Completar onboarding
4. Verificar recomendações no dashboard

### Teste 2: Endpoint API
1. Fazer login via Swagger
2. Testar `POST /api/onboarding/complete`
3. Verificar resposta de sucesso
4. Verificar se vetor sintético foi salvo

### Teste 3: Recomendações
1. Após onboarding, verificar recomendações
2. Confirmar que são personalizadas (não apenas populares)
3. Verificar similarity scores

---

## 📝 Notas Importantes

### Backend
- ✅ Nenhuma migration necessária (onboarding usa tabela existente `user_preferences`)
- ✅ Nenhuma nova dependência necessária
- ✅ Endpoint já está registrado

### Frontend
- ✅ Nenhuma nova dependência necessária
- ✅ Build deve incluir página de onboarding automaticamente

---

## ✅ Checklist Final

- [ ] Backend deployado e funcionando
- [ ] Frontend deployado e funcionando
- [ ] Endpoint de onboarding acessível
- [ ] Fluxo completo testado em produção
- [ ] Recomendações funcionando com vetor sintético

---

**Última atualização:** 26/11/2025

