# Execução de Migration - Status

**Data:** 25/11/2025  
**Status:** ⚠️ **AGUARDANDO DEPLOY**

---

## 🔍 Situação Atual

### **Estado da Migration:**
- ✅ Migration criada localmente: `a1b2c3d4e5f6_add_is_simulation_to_orders.py`
- ❌ Migration **não está** no servidor Fly.io ainda
- ✅ Migration atual no servidor: `5d0cda723f59` (head)

### **O Que Aconteceu:**
1. Tentativa de execução: `alembic upgrade head`
2. Resultado: Migration não encontrada no servidor
3. Motivo: Arquivo ainda está apenas localmente (não foi feito deploy)

---

## 📋 Próximos Passos Necessários

### **Opção 1: Deploy + Migration (Recomendado)**

**Passo 1:** Fazer deploy do código para Fly.io
```bash
cd tastematch/backend
fly deploy -a tastematch-api --no-cache
```

**Passo 2:** Executar migration após deploy
```bash
fly ssh console -a tastematch-api -C "alembic upgrade head"
```

**Vantagens:**
- ✅ Deploy e migration em sequência lógica
- ✅ Código e migration ficam sincronizados
- ✅ Backend atualizado com novos endpoints

---

### **Opção 2: Apenas Upload da Migration (Alternativa)**

**Passo 1:** Upload manual da migration via SSH
```bash
fly ssh sftp shell -a tastematch-api
put alembic/versions/a1b2c3d4e5f6_add_is_simulation_to_orders.py /app/alembic/versions/
```

**Passo 2:** Executar migration
```bash
fly ssh console -a tastematch-api -C "alembic upgrade head"
```

**Desvantagens:**
- ⚠️ Migration fica desconectada do código
- ⚠️ Próximo deploy pode sobrescrever
- ⚠️ Não é workflow profissional

---

## ✅ Recomendação Profissional

**Fazer deploy completo primeiro, depois executar migration.**

### **Workflow Recomendado:**

1. **Deploy do Backend**
   - Inclui migration no código
   - Inclui novos endpoints
   - Inclui modelos atualizados

2. **Executar Migration**
   - Aplica mudança no banco
   - Valida estrutura

3. **Validar Funcionamento**
   - Testar endpoints
   - Verificar campo no banco

---

## 🔧 Comandos para Executar

### **1. Deploy do Backend:**
```bash
cd /home/brunoadsba/ifood/tastematch/backend
fly deploy -a tastematch-api --no-cache
```

### **2. Executar Migration:**
```bash
fly ssh console -a tastematch-api -C "alembic upgrade head"
```

### **3. Validar Migration:**
```bash
fly ssh console -a tastematch-api -C "alembic current"
# Deve mostrar: a1b2c3d4e5f6 (head)

# Verificar coluna no banco:
fly ssh console -a tastematch-api -C "psql \$DATABASE_URL -c '\d orders'"
```

---

## ⚠️ Nota Importante

A migration **não pode ser executada** sem antes fazer deploy do código porque:
1. O arquivo de migration não existe no servidor
2. O código do backend precisa estar atualizado
3. Os novos endpoints precisam estar deployados

---

## 📊 Checklist

- [ ] Fazer deploy do backend
- [ ] Executar migration no servidor
- [ ] Validar migration aplicada
- [ ] Testar endpoint DELETE /api/orders/simulation
- [ ] Testar endpoint POST /api/orders com is_simulation

---

**Próximo Passo:** Fazer deploy do backend primeiro.

**Última atualização:** 25/11/2025

