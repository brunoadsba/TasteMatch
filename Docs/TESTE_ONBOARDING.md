# Teste do Onboarding Gamificado

## ✅ Verificações Realizadas

### Backend
- [x] Imports funcionam corretamente
- [x] `onboarding_service.py` compila sem erros
- [x] `onboarding.py` (endpoint) compila sem erros
- [x] `onboarding.py` (modelos) compila sem erros
- [x] Router registrado no `main.py`
- [x] Integração com `recommender.py` implementada

### Frontend
- [x] Sem erros de lint
- [x] `Onboarding.tsx` compila
- [x] Rota `/onboarding` registrada no `App.tsx`
- [x] Redirecionamento após cadastro implementado
- [x] Tipos TypeScript definidos
- [x] Método `completeOnboarding()` no cliente API

---

## 🧪 Testes Manuais Necessários

### Teste 1: Fluxo Completo de Cadastro → Onboarding → Dashboard

**Passos:**
1. Acessar `/login`
2. Clicar em "Criar conta"
3. Preencher formulário de cadastro
4. Verificar redirecionamento para `/onboarding`
5. Selecionar 1-3 culinárias
6. Avançar para etapa de preço
7. Selecionar faixa de preço
8. Avançar para etapa de restrições (opcional)
9. Clicar em "Finalizar"
10. Verificar redirecionamento para `/dashboard`
11. Verificar se recomendações aparecem (devem usar vetor sintético)

**Resultado Esperado:**
- ✅ Redirecionamento automático para onboarding após cadastro
- ✅ Onboarding completo em 3 etapas
- ✅ Toast de sucesso após completar
- ✅ Dashboard mostra recomendações personalizadas (não apenas populares)

---

### Teste 2: Pular Onboarding

**Passos:**
1. Acessar `/login`
2. Criar nova conta
3. Na primeira etapa do onboarding, clicar em "Pular por enquanto"
4. Verificar redirecionamento para `/dashboard`

**Resultado Esperado:**
- ✅ Redirecionamento para dashboard
- ✅ Dashboard mostra restaurantes populares (fallback)

---

### Teste 3: Validação de Formulário

**Passos:**
1. Acessar `/onboarding`
2. Tentar avançar sem selecionar culinária
3. Selecionar 1 culinária e avançar
4. Tentar avançar sem selecionar preço
5. Selecionar preço e avançar
6. Finalizar (restrições são opcionais)

**Resultado Esperado:**
- ✅ Botão "Próximo" desabilitado se não houver seleção
- ✅ Toast de erro ao tentar avançar sem seleção
- ✅ Validação funciona em todas as etapas

---

### Teste 4: API Endpoint

**Passos:**
1. Fazer login
2. Fazer POST para `/api/onboarding/complete` com:
   ```json
   {
     "selected_cuisines": ["italiana", "japonesa"],
     "price_preference": "medium",
     "dietary_restrictions": ["vegan"]
   }
   ```
3. Verificar resposta de sucesso
4. Verificar se `preference_embedding` foi salvo no banco

**Resultado Esperado:**
- ✅ Endpoint retorna `success: true`
- ✅ `has_synthetic_vector: true`
- ✅ Vetor sintético salvo em `user_preferences`

---

### Teste 5: Recomendações com Vetor Sintético

**Passos:**
1. Completar onboarding com culinárias específicas (ex: "italiana", "japonesa")
2. Acessar `/dashboard`
3. Verificar recomendações do Chef
4. Verificar se restaurantes recomendados são das culinárias selecionadas

**Resultado Esperado:**
- ✅ Recomendações aparecem mesmo sem pedidos
- ✅ Restaurantes recomendados são relevantes às culinárias escolhidas
- ✅ Não são apenas "populares" genéricos

---

## 🔍 Verificações Técnicas

### Backend: Lógica de Integração

**Arquivo:** `backend/app/core/recommender.py`

**Fluxo Esperado:**
1. `generate_recommendations()` verifica `user_embedding` do cache
2. Se `user_embedding` existe (pode ser sintético), usa para recomendações
3. Se não há `user_embedding` E não há pedidos, retorna populares
4. Se há pedidos mas não há `user_embedding`, calcula novo baseado em pedidos

**Código Relevante:**
```python
# Linha 271-285: Verifica cache (inclui vetor sintético)
user_embedding = None
if not refresh:
    preferences = get_user_preferences(db, user_id=user_id)
    if preferences and preferences.preference_embedding:
        user_embedding = json.loads(preferences.preference_embedding)

# Linha 283-285: Cold start apenas se não há embedding E não há pedidos
if not orders and user_embedding is None:
    return get_popular_restaurants(...)
```

**✅ Lógica Correta:** O vetor sintético do onboarding é tratado igual ao embedding calculado de pedidos.

---

### Frontend: Fluxo de Navegação

**Arquivo:** `frontend/src/hooks/useAuth.ts`

**Fluxo Esperado:**
1. Usuário cria conta
2. `register()` redireciona para `/onboarding`
3. Usuário completa onboarding
4. `Onboarding.tsx` redireciona para `/dashboard`

**Código Relevante:**
```typescript
// useAuth.ts linha 67
navigate('/onboarding');

// Onboarding.tsx linha 177
navigate('/dashboard');
```

**✅ Fluxo Correto:** Redirecionamento automático após cadastro.

---

## 🐛 Possíveis Problemas

### Problema 1: Tipos de Culinária Não Correspondem

**Sintoma:** Vetor sintético não é gerado ou recomendações não são relevantes.

**Causa:** Tipos de culinária no frontend não correspondem aos do banco.

**Solução:** Verificar `normalize_cuisine_type()` em `onboarding_service.py` e ajustar mapeamento.

---

### Problema 2: Endpoint Não Encontrado

**Sintoma:** Erro 404 ao chamar `/api/onboarding/complete`.

**Causa:** Router não registrado ou prefixo incorreto.

**Solução:** Verificar `main.py` linha 141: `app.include_router(onboarding.router)`

---

### Problema 3: Vetor Sintético Não Usado

**Sintoma:** Recomendações ainda são "populares" mesmo após onboarding.

**Causa:** Lógica de verificação de `user_embedding` não está funcionando.

**Solução:** Verificar logs do backend e confirmar que `preference_embedding` foi salvo.

---

## 📝 Checklist de Deploy

Antes de fazer deploy, verificar:

- [ ] Backend compila sem erros
- [ ] Frontend compila sem erros
- [ ] Testes manuais passaram
- [ ] Endpoint `/api/onboarding/complete` funciona
- [ ] Vetor sintético é gerado e salvo
- [ ] Recomendações usam vetor sintético
- [ ] Redirecionamento funciona corretamente

---

## 🎯 Próximos Passos

1. **Testar localmente** o fluxo completo
2. **Verificar logs** do backend durante onboarding
3. **Confirmar** que recomendações são personalizadas
4. **Ajustar** tipos de culinária se necessário
5. **Deploy** após validação

