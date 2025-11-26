# 🧪 Guia de Teste Local

**Data:** 25/11/2025  
**Objetivo:** Testar correções antes do deploy

---

## ✅ Pré-requisitos

- ✅ Backend: Python com uvicorn instalado
- ✅ Frontend: Node.js e npm instalados
- ✅ Banco de dados: SQLite (tastematch.db)

---

## 🚀 Passo a Passo

### **1. Iniciar Backend (Terminal 1)**

```bash
cd /home/brunoadsba/ifood/tastematch/backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verificar:**
- Backend rodando em: http://localhost:8000
- Health check: http://localhost:8000/health
- Docs: http://localhost:8000/docs

### **2. Iniciar Frontend (Terminal 2)**

```bash
cd /home/brunoadsba/ifood/tastematch/frontend
npm run dev
```

**Verificar:**
- Frontend rodando em: http://localhost:5173 (ou porta exibida)
- Conectado ao backend em: http://localhost:8000

---

## 🧪 Checklist de Testes

### **1. Correção: Inconsistência de Pedidos**

**Cenário A: Apenas pedidos reais (sem simulados)**
- [ ] Não deve mostrar "Aprendendo..."
- [ ] Deve mostrar "Cold Start"
- [ ] Não deve mostrar contador de pedidos simulados

**Cenário B: Com pedidos simulados**
- [ ] Deve mostrar "Aprendendo..." quando < 5 simulados
- [ ] Contador de simulados deve estar correto
- [ ] Detalhes da análise devem corresponder ao contador

**Cenário C: Sem pedidos**
- [ ] Deve mostrar "Cold Start"
- [ ] Mensagem padrão de perfil em construção

### **2. Correção: "Powered by LLM"**

- [ ] Badge "Powered by LLM" NÃO deve aparecer
- [ ] Apenas título "Análise de Perfil e Sugestão" deve aparecer

### **3. Traduções**

- [ ] Terminal: "Terminal de Raciocínio da IA" (não "AI Reasoning Terminal")
- [ ] Logs: "[INGESTÃO DE DADOS]", "[INFERÊNCIA]", "[SUCESSO]"
- [ ] Todos os textos em português

### **4. Textos de Recomendação**

- [ ] "restaurante de comida brasileira" (não "restaurante de brasileira")
- [ ] Formatação correta para todos os tipos de culinária

---

## 🔍 Pontos de Atenção

1. **Cache do navegador:** Se algo não atualizar, fazer hard refresh (Ctrl+Shift+R)
2. **Variáveis de ambiente:** Backend deve estar acessível em localhost:8000
3. **Banco de dados:** Verificar se há dados de teste no banco

---

## 📝 Observações

- Backend usa SQLite local
- Frontend se conecta automaticamente ao backend em localhost:8000
- Modo reload ativo nos dois serviços (mudanças refletem automaticamente)

---

**Status:** 🟢 Pronto para testes

