# Análise Investigativa: Por que `is_simulation` não estava renderizando no frontend

## 🔍 Problema Identificado

O painel `LLMInsightPanel` estava mostrando "Aprendendo..." mesmo quando havia 0 pedidos simulados, exibindo inconsistências como:
- "4 pedido(s) total" 
- "0 pedido(s) simulado(s) processado(s)"
- Status "Aprendendo..." quando deveria ser "Cold Start"

## 🔎 Causa Raiz

### Backend: Campo `is_simulation` não estava sendo retornado pela API

**Localização do bug:**
- Arquivo: `backend/app/api/routes/orders.py`
- Endpoint: `GET /api/orders` (listagem de pedidos)
- Linha: ~78 (na construção do `order_dict`)

**Problema:**
O campo `is_simulation` do modelo `Order` existe no banco de dados e estava sendo salvo corretamente, mas **não estava sendo incluído** na resposta JSON da API.

### Impacto

1. **Frontend recebia pedidos sem o campo `is_simulation`:**
   ```json
   {
     "id": 1,
     "restaurant_id": 5,
     "order_date": "2025-11-25T19:02:00Z",
     "total_amount": 28.90,
     "rating": 5,
     // ❌ Faltava: "is_simulation": false
   }
   ```

2. **Filtro no frontend falhava:**
   ```typescript
   // ❌ order.is_simulation === true sempre retornava false
   // porque order.is_simulation era undefined
   const simulatedOrders = orders.filter(order => order.is_simulation === true);
   ```

3. **Lógica de exibição quebrava:**
   - `simulatedCount` sempre era 0 (mesmo tendo pedidos simulados)
   - Mas havia inconsistência na lógica que mostrava "Aprendendo..." quando não deveria

## ✅ Correção Aplicada

### 1. Adicionado `is_simulation` na listagem de pedidos
```python
# backend/app/api/routes/orders.py - linha ~78
order_dict = {
    # ... outros campos ...
    "is_simulation": order.is_simulation,  # ✅ ADICIONADO
    "created_at": order.created_at.isoformat() + "Z"
}
```

### 2. Adicionado `is_simulation` na criação de pedidos
```python
# backend/app/api/routes/orders.py - linha ~133
order_dict = {
    # ... outros campos ...
    "is_simulation": db_order.is_simulation,  # ✅ ADICIONADO
    "created_at": db_order.created_at
}
```

## 🔍 Verificações Adicionais

### Frontend
- ✅ Lógica de filtro está correta (`order.is_simulation === true`)
- ✅ Condicional para `cold_start` está correta (`simulatedCount === 0`)
- ✅ Código já estava implementado corretamente

### Backend
- ✅ Modelo `Order` tem o campo `is_simulation` (linha 63 de models.py)
- ✅ Migration já foi aplicada (`is_simulation` existe no banco)
- ✅ Campo está sendo salvo corretamente no `create_order` (crud.py)
- ❌ **Campo não estava sendo retornado na API** → CORRIGIDO

## 📋 Próximos Passos

1. ✅ Backend corrigido
2. ⏳ Reiniciar servidor backend para aplicar mudanças
3. ⏳ Testar no frontend após reiniciar backend
4. ⏳ Verificar se cache do navegador precisa ser limpo

## 🎯 Resultado Esperado

Após a correção:
- Pedidos retornarão com `is_simulation: true` ou `is_simulation: false`
- Frontend conseguirá filtrar corretamente
- Painel mostrará:
  - **Cold Start** quando `simulatedCount === 0`
  - **Aprendendo...** quando `simulatedCount > 0 && < 5`
  - **Personalizado** quando `simulatedCount >= 5`
