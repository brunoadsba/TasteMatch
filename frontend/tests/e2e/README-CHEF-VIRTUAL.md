# Testes E2E - Chef Virtual

## Visão Geral

Este arquivo contém testes end-to-end (E2E) para o Chef Virtual usando Playwright.

## Arquivo de Testes

- `chef-virtual.spec.ts` - Testes principais do Chef Virtual

## Como Executar

### Todos os testes do Chef Virtual
```bash
npm run test:e2e:chef
```

### Com interface gráfica (UI Mode)
```bash
npm run test:e2e:chef:ui
```

### Apenas mobile
```bash
npm run test:e2e:chef:mobile
```

### Apenas desktop
```bash
npm run test:e2e:chef:desktop
```

## Testes Implementados

### 1. **Exibição do Botão**
- ✅ Verifica se botão "Chef Virtual" está visível no Dashboard
- ✅ Verifica se botão tem ícone de chef

### 2. **Abertura do Chat**
- ✅ Verifica se modal de chat abre ao clicar no botão
- ✅ Verifica se elementos do chat estão presentes

### 3. **Fluxo de Texto**
- ✅ Envia mensagem de texto
- ✅ Verifica se mensagem do usuário aparece
- ✅ Verifica se resposta do assistente aparece
- ✅ Verifica se resposta contém informações relevantes

### 4. **Interações Sociais**
- ✅ Testa saudações ("Olá")
- ✅ Testa agradecimentos ("Obrigado")
- ✅ Verifica respostas naturais

### 5. **Estados de Loading**
- ✅ Verifica indicadores de processamento
- ✅ Verifica que loading desaparece após resposta

### 6. **Tratamento de Erros**
- ✅ Testa exibição de erro em falha de API
- ✅ Testa rate limiting (429)

### 7. **Fechamento do Modal**
- ✅ Verifica se modal fecha corretamente

### 8. **Responsividade**
- ✅ Testa em dispositivos mobile (375x667)
- ✅ Testa em desktop (1920x1080)
- ✅ Verifica que modal se adapta ao tamanho da tela

### 9. **Guardrails**
- ✅ Testa bloqueio de perguntas fora do escopo
- ✅ Verifica mensagem apropriada

### 10. **Recomendações**
- ✅ Verifica se recomendações aparecem nas respostas

### 11. **Markdown**
- ✅ Verifica se markdown é renderizado corretamente
- ✅ Verifica que asteriscos não aparecem visíveis

### 12. **Rodapé Fixo**
- ✅ Verifica se disclaimer está visível

## Pré-requisitos

1. **Backend rodando**
   ```bash
   cd tastematch/backend
   uvicorn app.main:app --reload --port 8000
   ```

2. **Frontend rodando**
   ```bash
   cd tastematch/frontend
   npm run dev
   ```

3. **Banco de dados configurado**
   - PostgreSQL com extensão `vector`
   - Tabelas criadas (migrations aplicadas)
   - Dados de teste (opcional, mas recomendado)

4. **Usuário de teste**
   - Criar usuário de teste ou usar credenciais existentes
   - Ajustar credenciais no helper `ensureLoggedIn()` se necessário

## Configuração

### Credenciais de Teste

Se necessário, ajustar credenciais no arquivo `chef-virtual.spec.ts`:

```typescript
async function ensureLoggedIn(page: any) {
  // ...
  await emailInput.fill('test@example.com'); // Ajustar
  await passwordInput.fill('test123'); // Ajustar
  // ...
}
```

### Timeouts

Os testes usam timeouts padrão do Playwright. Para ajustar:

```typescript
await expect(element).toBeVisible({ timeout: 10000 }); // 10 segundos
```

## Estrutura dos Testes

### Helpers

- `isLoggedIn()` - Verifica se usuário está logado
- `ensureLoggedIn()` - Garante que usuário está logado
- `openChefVirtual()` - Abre o chat do Chef Virtual

### Padrões

- Todos os testes verificam se está logado antes de continuar
- Testes pulam automaticamente se pré-requisitos não forem atendidos
- Timeouts generosos para aguardar respostas do LLM

## Notas Importantes

1. **Dependência do Backend**: Testes requerem backend rodando e funcional
2. **Dependência do LLM**: Respostas podem variar, testes são flexíveis
3. **Dados de Teste**: Recomendado ter dados de teste no banco
4. **Rate Limiting**: Testes podem ser afetados por rate limiting (30 req/min)

## Troubleshooting

### Teste falha com "Element not visible"
- Verificar se backend está rodando
- Verificar se frontend está rodando
- Aumentar timeout se necessário

### Teste falha com "Not logged in"
- Ajustar credenciais no helper `ensureLoggedIn()`
- Verificar se usuário de teste existe no banco

### Teste falha com "Chat not opened"
- Verificar se botão do Chef Virtual está visível
- Verificar se há erros no console do navegador

### Respostas não aparecem
- Verificar logs do backend
- Verificar se API Groq está funcionando
- Aumentar timeout de aguardo de resposta

## Próximos Testes (Opcional)

- [ ] Testes de gravação de áudio (requer permissões de microfone)
- [ ] Testes de reprodução de áudio
- [ ] Testes de histórico de conversas com múltiplas mensagens
- [ ] Testes de integração com recomendações específicas
- [ ] Testes de performance (tempo de resposta)

## Relatórios

Após executar testes, ver relatório:

```bash
npm run test:e2e:report
```

Isso abrirá o relatório HTML com screenshots e vídeos de falhas.

