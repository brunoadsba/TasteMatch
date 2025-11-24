# Guia de Teste no Swagger - TasteMatch API

## 🔗 Acessar Swagger UI

1. Certifique-se de que o servidor está rodando:
   ```bash
   cd /home/brunoadsba/ifood/tastematch/backend
   python -m uvicorn app.main:app --reload
   ```

2. Acesse no navegador:
   ```
   http://localhost:8000/docs
   ```

---

## 📋 Ordem Recomendada de Testes

### 1. **Autenticação** (obrigatório para endpoints protegidos)

#### 1.1 Registrar novo usuário
- **Endpoint:** `POST /auth/register`
- **Request Body:**
  ```json
  {
    "email": "teste_swagger@example.com",
    "name": "Usuário Teste Swagger",
    "password": "senha123"
  }
  ```
- **O que esperar:** Status 201, resposta com `user` e `token`
- **Copie o `token` recebido!**

#### 1.2 Fazer login
- **Endpoint:** `POST /auth/login`
- **Request Body:**
  ```json
  {
    "email": "teste_swagger@example.com",
    "password": "senha123"
  }
  ```
- **O que esperar:** Status 200, resposta com `user` e `token`

#### 1.3 Autorizar no Swagger
1. Clique no botão **"Authorize"** (🔒) no topo da página
2. Cole o token JWT no campo "Value"
3. Clique em **"Authorize"**
4. Clique em **"Close"**

Agora todos os endpoints protegidos estarão acessíveis!

---

### 2. **Endpoints de Usuário**

#### 2.1 Obter informações do usuário
- **Endpoint:** `GET /api/users/me`
- **Autenticação:** ✅ Necessária
- **O que esperar:** 
  - Status 200
  - Informações do usuário autenticado (id, email, name, created_at)

#### 2.2 Obter preferências do usuário
- **Endpoint:** `GET /api/users/me/preferences`
- **Autenticação:** ✅ Necessária
- **O que esperar:**
  - Status 200
  - Preferências baseadas no histórico de pedidos:
    - `favorite_cuisines`: Lista de culinárias favoritas (top 3)
    - `total_orders`: Total de pedidos
    - `average_order_value`: Ticket médio

---

### 3. **Endpoints de Restaurantes**

#### 3.1 Listar restaurantes (sem filtros)
- **Endpoint:** `GET /api/restaurants`
- **Autenticação:** ❌ Não necessária
- **Parâmetros opcionais:**
  - `page`: 1 (padrão)
  - `limit`: 20 (padrão, máximo 100)
- **O que esperar:**
  - Status 200
  - Lista de restaurantes paginada
  - `total`: Total de restaurantes

#### 3.2 Listar restaurantes com filtros
- **Endpoint:** `GET /api/restaurants`
- **Parâmetros:**
  - `cuisine_type`: "italiana" (ou "japonesa", "brasileira", etc.)
  - `min_rating`: 4.0
  - `page`: 1
  - `limit`: 10
- **O que esperar:** Apenas restaurantes que correspondem aos filtros

#### 3.3 Obter detalhes de um restaurante
- **Endpoint:** `GET /api/restaurants/{restaurant_id}`
- **Parâmetro:** `restaurant_id`: 1 (ou qualquer ID válido)
- **O que esperar:**
  - Status 200: Detalhes completos do restaurante
  - Status 404: Se restaurante não existir

**💡 Dica:** Use o ID retornado na listagem de restaurantes!

---

### 4. **Endpoints de Pedidos**

#### 4.1 Listar pedidos do usuário
- **Endpoint:** `GET /api/orders`
- **Autenticação:** ✅ Necessária
- **Parâmetros opcionais:**
  - `limit`: 20 (padrão)
  - `offset`: 0 (padrão)
- **O que esperar:**
  - Status 200
  - Lista de pedidos do usuário autenticado
  - Cada pedido inclui: id, restaurant_name, order_date, total_amount, items, rating

#### 4.2 Criar novo pedido
- **Endpoint:** `POST /api/orders`
- **Autenticação:** ✅ Necessária
- **Request Body:**
  ```json
  {
    "restaurant_id": 1,
    "order_date": "2025-01-27T12:00:00Z",
    "total_amount": 45.90,
    "items": [
      {
        "name": "Pizza Margherita",
        "quantity": 1,
        "price": 45.90
      }
    ],
    "rating": 5
  }
  ```
- **O que esperar:**
  - Status 201: Pedido criado com sucesso
  - Status 400: Se restaurante não existir
- **Após criar:** O pedido aparecerá na listagem de pedidos!

---

## 🧪 Testes de Validação

### Teste de Erros Esperados

1. **Email duplicado no registro:**
   - `POST /auth/register` com email já existente
   - Deve retornar 400 Bad Request

2. **Credenciais inválidas:**
   - `POST /auth/login` com senha errada
   - Deve retornar 401 Unauthorized

3. **Acesso sem autenticação:**
   - `GET /api/users/me` sem token
   - Deve retornar 401 Unauthorized

4. **Restaurante não encontrado:**
   - `GET /api/restaurants/99999`
   - Deve retornar 404 Not Found

5. **Pedido com restaurante inválido:**
   - `POST /api/orders` com `restaurant_id` inexistente
   - Deve retornar 400 Bad Request

---

## 📊 Fluxo Completo Recomendado

1. ✅ **Registrar** novo usuário (`POST /auth/register`)
2. ✅ **Fazer login** (`POST /auth/login`)
3. ✅ **Autorizar** no Swagger (botão Authorize)
4. ✅ **Obter informações** do usuário (`GET /api/users/me`)
5. ✅ **Listar restaurantes** (`GET /api/restaurants`)
6. ✅ **Ver detalhes** de um restaurante (`GET /api/restaurants/{id}`)
7. ✅ **Criar pedido** (`POST /api/orders`)
8. ✅ **Listar pedidos** (`GET /api/orders`)
9. ✅ **Ver preferências** atualizadas (`GET /api/users/me/preferences`)

---

## 💡 Dicas Úteis

- **Formato de Data:** Use ISO 8601: `2025-01-27T12:00:00Z`
- **Ratings:** Deve ser entre 1 e 5 (inteiro)
- **Total Amount:** Use formato decimal: `45.90`
- **Items:** Array de objetos com `name`, `quantity`, `price`
- **Pagination:** Use `limit` e `offset` para navegar resultados grandes

---

## 🐛 Troubleshooting

### Erro 401 Unauthorized
- **Solução:** Certifique-se de que:
  1. Fez login e copiou o token
  2. Clicou em "Authorize" e colou o token
  3. Token não expirou (padrão: 24 horas)

### Erro 422 Validation Error
- **Solução:** Verifique:
  - Formato dos dados (tipo correto)
  - Campos obrigatórios preenchidos
  - Valores dentro dos limites (ex: rating 1-5)

### Servidor não responde
- **Solução:**
  ```bash
  # Verificar se servidor está rodando
  curl http://localhost:8000/health
  
  # Se não estiver, iniciar:
  cd backend
  python -m uvicorn app.main:app --reload
  ```

---

**Boa sorte com os testes! 🚀**

