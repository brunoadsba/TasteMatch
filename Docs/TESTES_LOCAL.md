# Guia de Testes Locais - Otimizações de Memória

## 🎯 Objetivo

Validar todas as otimizações de memória **localmente** antes de commitar e fazer deploy.

## ✅ Por que testar localmente primeiro?

1. **Detecta erros antes do deploy** - Economiza tempo e evita rollbacks
2. **Valida funcionalidade** - Garante que nada quebrou
3. **Confirma otimizações** - Verifica que as mudanças funcionam
4. **Profissionalismo** - Boa prática de desenvolvimento

## 📋 Checklist de Testes

### 1. Testes Básicos (Já Concluídos ✅)

- [x] Imports funcionam
- [x] Sintaxe Python correta
- [x] Pool de conexões configurado
- [x] Cache criado

### 2. Testes Funcionais (Fazer Agora ⏳)

#### 2.1 Iniciar Backend

```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Verificar:**
- [ ] Backend inicia sem erros
- [ ] Nenhum erro de import
- [ ] Pool de conexões inicializado (verificar logs)

#### 2.2 Health Check

```bash
curl http://localhost:8000/health
```

**Esperado:**
```json
{"status": "healthy"}
```

#### 2.3 Testar Endpoint de Restaurantes

```bash
curl http://localhost:8000/api/restaurants?limit=5
```

**Verificar:**
- [ ] Retorna dados (mesmo sem autenticação, se permitido)
- [ ] Headers incluem `Cache-Control` (se autenticado)
- [ ] Resposta rápida

#### 2.4 Verificar Cache

```bash
# Primeira requisição (cache miss)
time curl http://localhost:8000/api/restaurants?limit=10

# Segunda requisição (cache hit - deve ser mais rápida)
time curl http://localhost:8000/api/restaurants?limit=10
```

**Verificar:**
- [ ] Segunda requisição é mais rápida
- [ ] Cache funciona corretamente

#### 2.5 Verificar Logs do Backend

**Procurar por:**
- [ ] Pool de conexões: `pool_size=4`
- [ ] Queries usando `get_restaurants_metadata` (não `get_restaurants`)
- [ ] Cache hits/misses nos logs (se implementado logging)

### 3. Testes de Integração (Com Frontend)

#### 3.1 Iniciar Frontend

```bash
cd frontend
npm run dev
```

#### 3.2 Testar Login

1. Acessar `http://localhost:5173`
2. Fazer login
3. Verificar se autenticação funciona

**Verificar:**
- [ ] Login bem-sucedido
- [ ] Token salvo
- [ ] Redirecionamento correto

#### 3.3 Testar Recomendações

1. Acessar página de recomendações
2. Solicitar recomendações
3. Verificar resposta

**Verificar:**
- [ ] Recomendações são geradas
- [ ] Resposta rápida (< 2 segundos)
- [ ] Dados corretos

#### 3.4 Testar Lista de Pedidos

1. Acessar página de pedidos
2. Verificar carregamento

**Verificar:**
- [ ] Pedidos carregam corretamente
- [ ] Usa `selectinload` (verificar logs do backend)
- [ ] Sem N+1 queries (apenas 2 queries: orders + restaurants)

### 4. Testes de Performance (Opcional)

#### 4.1 Monitorar Memória

```bash
# No terminal do backend, verificar uso de memória
# (depende do sistema operacional)
```

**Verificar:**
- [ ] Uso de memória razoável (< 500MB em desenvolvimento)
- [ ] Sem vazamentos de memória

#### 4.2 Testar Múltiplas Requisições

```bash
# Fazer 10 requisições simultâneas
for i in {1..10}; do
  curl http://localhost:8000/api/restaurants?limit=5 &
done
wait
```

**Verificar:**
- [ ] Todas as requisições completam
- [ ] Pool de conexões não excede limite
- [ ] Sem erros de conexão

## 🚨 Problemas Comuns e Soluções

### Erro: "Module not found"
**Solução:** Verificar se está no ambiente virtual e dependências instaladas

### Erro: "Connection refused"
**Solução:** Verificar se backend está rodando na porta 8000

### Erro: "Pool timeout"
**Solução:** Verificar se banco de dados está acessível

### Cache não funciona
**Solução:** Verificar se `get_cached_restaurants_metadata` está sendo chamado

## ✅ Critérios de Sucesso

Antes de commitar e fazer deploy, garantir:

1. ✅ Backend inicia sem erros
2. ✅ Health check responde
3. ✅ Endpoints funcionam corretamente
4. ✅ Cache funciona (segunda requisição mais rápida)
5. ✅ Login funciona no frontend
6. ✅ Recomendações funcionam
7. ✅ Pedidos carregam sem N+1 queries
8. ✅ Logs mostram queries otimizadas

## 📝 Após Testes Bem-Sucedidos

1. **Commit das mudanças:**
   ```bash
   git add .
   git commit -m "feat: otimizações de memória - pool, cache, queries"
   ```

2. **Push para branch:**
   ```bash
   git push origin feature/otimizacao-memoria
   ```

3. **Deploy:**
   ```bash
   # Backend
   cd backend
   fly deploy

   # Frontend (se necessário)
   cd frontend
   netlify deploy --prod
   ```

## 🔍 Scripts Auxiliares

### Executar Testes Automatizados

```bash
cd backend/scripts
./test_otimizacoes.sh
```

### Verificar Logs do Backend

```bash
# No terminal onde o backend está rodando
# Procurar por:
# - "pool_size"
# - "get_restaurants_metadata"
# - "cache"
```

## 📚 Referências

- [Plano de Implementação](./memoria-config-implementacao.md)
- [Documentação de Otimizações](./memoria-config.md)

