# TasteMatch - Guia de Deploy em Produção

> **Última atualização:** 2025-01-27  
> **Status:** Fase 12 - Deploy e Produção

---

## 📋 Pré-requisitos

### Contas Necessárias
- [x] Conta no [Fly.io](https://fly.io) (gratuita)
- [x] Conta no [Netlify](https://netlify.com) (gratuita)
- [x] GROQ_API_KEY válida

### Ferramentas Necessárias
- Fly CLI instalado
- Netlify CLI instalado (opcional)
- Git configurado

---

## 🔧 Parte 1: Preparação

### 1.1 Gerar Chaves Secretas

```bash
# Gerar SECRET_KEY seguro
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Gerar JWT_SECRET_KEY seguro
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"
```

**IMPORTANTE:** Guarde essas chaves em local seguro! Elas serão usadas nos secrets do Fly.io.

### 1.2 Validar Configurações

As seguintes validações são feitas automaticamente ao iniciar em produção:
- ✅ `DEBUG=False`
- ✅ `SECRET_KEY` alterada
- ✅ `JWT_SECRET_KEY` alterada
- ✅ PostgreSQL (não SQLite) em uso

---

## 🚀 Parte 2: Deploy Backend (Fly.io)

### 2.1 Instalar Fly CLI

```bash
# Linux/Mac
curl -L https://fly.io/install.sh | sh

# Verificar instalação
fly version
```

### 2.2 Fazer Login no Fly.io

```bash
fly auth login
```

### 2.3 Criar Aplicação no Fly.io

```bash
cd backend

# Inicializar aplicação (ou usar fly.toml existente)
fly launch
# Ou criar manualmente:
# fly apps create tastematch-api --region gru
```

**Configurações:**
- App name: `tastematch-api`
- Region: `gru` (São Paulo, Brasil)

### 2.4 Configurar PostgreSQL

**Opção A: Fly.io Postgres (Recomendado)**

```bash
# Criar banco PostgreSQL
fly postgres create --name tastematch-db --region gru

# Anexar ao app
fly postgres attach tastematch-db -a tastematch-api

# Habilitar extensão pgvector
fly postgres connect -a tastematch-db
# Dentro do psql:
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

**Opção B: Serviço Externo (Neon, Supabase, etc.)**

Copiar `DATABASE_URL` do serviço e configurar como secret (ver passo 2.5).

### 2.5 Configurar Secrets

```bash
# Configurar todas as variáveis de ambiente como secrets
fly secrets set \
  ENVIRONMENT=production \
  DEBUG=False \
  SECRET_KEY=<sua-secret-key-gerada> \
  JWT_SECRET_KEY=<sua-jwt-secret-key-gerada> \
  GROQ_API_KEY=<sua-groq-api-key> \
  -a tastematch-api

# Se usando PostgreSQL externo:
fly secrets set DATABASE_URL=<postgresql-url> -a tastematch-api

# Se usando Fly Postgres, DATABASE_URL é configurado automaticamente
```

### 2.6 Fazer Deploy

```bash
cd backend
fly deploy
```

### 2.7 Executar Migrations

```bash
# Opção 1: Via SSH
fly ssh console -a tastematch-api
cd /app
alembic upgrade head
exit

# Opção 2: Localmente apontando para produção
# Configurar DATABASE_URL temporariamente e executar:
# alembic upgrade head
```

### 2.8 Validar Deploy

```bash
# Verificar status
fly status -a tastematch-api

# Ver logs
fly logs -a tastematch-api

# Testar health check
curl https://tastematch-api.fly.dev/health
```

**URLs:**
- API: `https://tastematch-api.fly.dev`
- Docs: `https://tastematch-api.fly.dev/docs`
- Health: `https://tastematch-api.fly.dev/health`

---

## 🌐 Parte 3: Deploy Frontend (Netlify)

### 3.1 Instalar Netlify CLI (Opcional)

```bash
npm install -g netlify-cli
netlify login
```

**Nota:** Pode usar a interface web do Netlify também.

### 3.2 Configurar Build

O arquivo `netlify.toml` já está configurado na raiz do projeto.

**Configurações:**
- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/dist`

### 3.3 Deploy via CLI

```bash
cd frontend

# Deploy de preview
netlify deploy

# Deploy em produção
netlify deploy --prod
```

### 3.4 Deploy via Interface Web

1. Acessar [Netlify Dashboard](https://app.netlify.com)
2. Clicar em "Add new site" → "Import an existing project"
3. Conectar repositório Git
4. Configurar:
   - **Base directory:** (deixar vazio)
   - **Build command:** `cd frontend && npm install && npm run build`
   - **Publish directory:** `frontend/dist`

### 3.5 Configurar Variáveis de Ambiente

No Netlify Dashboard:
1. Ir em Site settings → Environment variables
2. Adicionar:
   - `VITE_API_URL`: `https://tastematch-api.fly.dev`
   - `NODE_VERSION`: `18` (opcional)

### 3.6 Validar Deploy

Acessar a URL do Netlify (ex: `https://tastematch.netlify.app`) e testar:
- ✅ Página carrega
- ✅ Login funciona
- ✅ Recomendações carregam

---

## 🔗 Parte 4: Configuração CORS

### 4.1 Atualizar CORS no Backend

Após obter a URL do frontend em produção, adicionar ao backend:

```bash
# Configurar FRONTEND_URL como secret
fly secrets set FRONTEND_URL=https://tastematch.netlify.app -a tastematch-api

# Ou atualizar diretamente no código (não recomendado)
```

O código em `backend/app/main.py` já suporta `FRONTEND_URL` via variável de ambiente.

### 4.2 Validar CORS

Testar requisições do frontend para o backend no console do navegador. Não deve haver erros de CORS.

---

## ✅ Parte 5: Validação Final

### 5.1 Testes Funcionais

**Backend:**
```bash
# Health check
curl https://tastematch-api.fly.dev/health

# Teste de autenticação
curl -X POST https://tastematch-api.fly.dev/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@example.com","password":"123456"}'

# Teste de recomendações (com token)
curl https://tastematch-api.fly.dev/api/recommendations \
  -H "Authorization: Bearer <token>"
```

**Frontend:**
- [ ] Login funciona
- [ ] Dashboard carrega recomendações
- [ ] Histórico de pedidos funciona
- [ ] Filtros funcionam

### 5.2 Monitoramento

**Fly.io:**
```bash
# Ver logs em tempo real
fly logs -a tastematch-api

# Ver métricas
fly dashboard -a tastematch-api
```

**Netlify:**
- Acessar dashboard para ver builds e logs

### 5.3 Troubleshooting

**Problemas Comuns:**

1. **Erro de CORS:**
   - Verificar `FRONTEND_URL` configurado no Fly.io
   - Verificar `allow_origins` no código

2. **Erro de banco de dados:**
   - Verificar `DATABASE_URL` configurado
   - Verificar migrations executadas

3. **Erro de GROQ_API_KEY:**
   - Verificar secret configurado
   - Verificar chave válida

4. **Build do frontend falha:**
   - Verificar Node version (usar 18+)
   - Verificar dependências instaladas

---

## 📊 URLs de Produção

Após o deploy completo:

- **Backend API:** `https://tastematch-api.fly.dev`
- **API Docs:** `https://tastematch-api.fly.dev/docs`
- **Health Check:** `https://tastematch-api.fly.dev/health`
- **Frontend:** `https://tastematch.netlify.app` (ou URL gerada pelo Netlify)

---

## 🔄 Atualizações Futuras

### Fazer Deploy de Atualizações

**Backend:**
```bash
cd backend
fly deploy
```

**Frontend:**
```bash
cd frontend
netlify deploy --prod
# Ou deixar deploy automático via Git
```

### Executar Novas Migrations

```bash
fly ssh console -a tastematch-api
cd /app
alembic upgrade head
exit
```

---

## 📝 Notas Importantes

1. **Segurança:**
   - Nunca commitar secrets no Git
   - Usar sempre HTTPS em produção
   - Validar configurações de produção

2. **Performance:**
   - Monitorar logs regularmente
   - Ajustar workers do uvicorn se necessário
   - Configurar CDN para frontend (Netlify já faz isso)

3. **Backup:**
   - Configurar backups automáticos do PostgreSQL
   - Fly Postgres tem backups automáticos

---

**Última atualização:** 2025-01-27  
**Próximos passos:** Validar todos os endpoints em produção e monitorar logs

