# Setup para Desenvolvimento Local

> **Data:** 29/11/2025  
> **Objetivo:** Configurar ambiente local para desenvolvimento

---

## 🎯 Problemas Identificados

1. **Erro de CORS**: Frontend bloqueado ao acessar backend
2. **Erro de Banco**: Tentando conectar ao Supabase de produção (inacessível)

---

## 📋 Solução Passo a Passo

### **Passo 1: Iniciar PostgreSQL Local**

```bash
cd /home/brunoadsba/ifood/tastematch

# Iniciar PostgreSQL via Docker Compose
docker-compose up -d postgres

# Verificar se está rodando
docker-compose ps
```

O PostgreSQL estará disponível em:
- **Host:** `localhost`
- **Porta:** `5432`
- **Usuário:** `tastematch`
- **Senha:** `tastematch_dev`
- **Banco:** `tastematch`

---

### **Passo 2: Configurar Variáveis de Ambiente**

Crie ou edite o arquivo `.env` na raiz do projeto:

```bash
cd /home/brunoadsba/ifood/tastematch
nano .env  # ou use seu editor preferido
```

Configure as seguintes variáveis:

```env
# Ambiente
ENVIRONMENT=development
DEBUG=true

# Banco de Dados Local
DATABASE_URL=postgresql://tastematch:tastematch_dev@localhost:5432/tastematch

# IMPORTANTE: Não usar Supabase em desenvolvimento local
# Remova ou comente DB_PROVIDER=supabase se existir
# DB_PROVIDER=

# Chaves Secretas (desenvolvimento)
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production

# Groq API (necessário para Chef Virtual)
GROQ_API_KEY=sua-groq-api-key-aqui

# Frontend URL (para CORS)
FRONTEND_URL=http://127.0.0.1:5173
```

---

### **Passo 3: Rodar Migrações no Banco Local**

```bash
cd /home/brunoadsba/ifood/tastematch/backend

# Ativar ambiente virtual (se necessário)
source ../venv/bin/activate

# Rodar migrações
alembic upgrade head
```

**Nota:** Se houver erro de extensão pgvector, execute:

```bash
# Conectar ao banco
docker-compose exec postgres psql -U tastematch -d tastematch

# Dentro do psql:
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

---

### **Passo 4: Verificar CORS**

O CORS já está configurado em `backend/app/main.py` para:
- `http://127.0.0.1:5173` ✅
- `http://localhost:5173` ✅

Se ainda houver problemas de CORS, reinicie o backend:

```bash
cd /home/brunoadsba/ifood/tastematch/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### **Passo 5: Popular Banco com Dados (Opcional)**

Para ter dados de teste localmente:

```bash
cd /home/brunoadsba/ifood/tastematch/backend

# Usar script de seed se existir
# python scripts/seed.py

# Ou importar dados manualmente
```

---

## 🔍 Verificação

### **1. Verificar Banco de Dados**

```bash
# Conectar ao PostgreSQL
docker-compose exec postgres psql -U tastematch -d tastematch

# Listar tabelas
\dt

# Sair
\q
```

### **2. Verificar Backend**

```bash
# Testar health check
curl http://localhost:8000/health

# Deve retornar:
# {
#   "status": "healthy",
#   "database": "connected (X tables)",
#   ...
# }
```

### **3. Verificar CORS**

No navegador, abra o console e verifique se não há erros de CORS.

---

## 🚨 Troubleshooting

### **Erro: "Network is unreachable"**

**Causa:** Tentando conectar ao Supabase de produção.

**Solução:**
1. Certifique-se que `DATABASE_URL` aponta para `localhost:5432`
2. Remova ou comente `DB_PROVIDER=supabase` no `.env`

---

### **Erro: "CORS policy"**

**Causa:** Backend não está permitindo origem do frontend.

**Solução:**
1. Verifique que o backend está rodando na porta 8000
2. Verifique que o frontend está rodando na porta 5173
3. Reinicie o backend após alterar configurações

---

### **Erro: "extension 'vector' does not exist"**

**Causa:** Extensão pgvector não está instalada no PostgreSQL local.

**Solução:**

```bash
# O docker-compose.yml já usa a imagem pgvector/pgvector:pg16
# Mas se ainda houver erro, reinstale:

docker-compose down
docker-compose up -d postgres

# Aguarde alguns segundos e conecte novamente:
docker-compose exec postgres psql -U tastematch -d tastematch -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

### **Erro: "Port 5432 already in use"**

**Causa:** Outro PostgreSQL está usando a porta 5432.

**Solução:**

```bash
# Verificar qual processo está usando a porta
sudo lsof -i :5432

# Parar o processo ou mudar a porta no docker-compose.yml
```

---

## 📝 Resumo de Comandos

```bash
# 1. Iniciar PostgreSQL
docker-compose up -d postgres

# 2. Configurar .env (editar manualmente)
# DATABASE_URL=postgresql://tastematch:tastematch_dev@localhost:5432/tastematch

# 3. Rodar migrações
cd backend && alembic upgrade head

# 4. Iniciar backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Iniciar frontend (em outro terminal)
cd frontend && npm run dev
```

---

## ✅ Checklist

- [ ] PostgreSQL rodando via Docker Compose
- [ ] `.env` configurado com `DATABASE_URL` local
- [ ] `DB_PROVIDER` não está definido como "supabase"
- [ ] Migrações executadas (`alembic upgrade head`)
- [ ] Backend rodando na porta 8000
- [ ] Frontend rodando na porta 5173
- [ ] Health check retorna "healthy"
- [ ] Sem erros de CORS no console

---

**Última atualização:** 30/11/2025

