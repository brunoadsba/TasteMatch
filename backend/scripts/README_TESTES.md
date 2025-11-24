# Scripts de Teste - TasteMatch

## Scripts Disponíveis

### `test_auth_endpoints.py`

Script automatizado para testar todos os endpoints de autenticação.

#### Uso

**1. Certifique-se de que o servidor está rodando:**
```bash
cd /home/brunoadsba/ifood/tastematch/backend
python -m uvicorn app.main:app --reload
```

**2. Em outro terminal, execute o script:**
```bash
cd /home/brunoadsba/ifood/tastematch/backend
python scripts/test_auth_endpoints.py
```

**3. Para testar em outra URL:**
```bash
python scripts/test_auth_endpoints.py --url http://localhost:8000
```

#### O que o script testa:

- ✅ Verificação se o servidor está rodando (`/health`)
- ✅ Registro de novo usuário (`POST /auth/register`)
- ✅ Registro com email duplicado (deve falhar)
- ✅ Login com credenciais válidas (`POST /auth/login`)
- ✅ Login com email inválido (deve falhar)
- ✅ Login com senha incorreta (deve falhar)
- ✅ Validação do formato do token JWT
- ✅ Preparação para testar rotas protegidas (quando implementadas)

#### Saída do Script

O script mostra:
- ✅ Testes que passaram
- ❌ Testes que falharam
- ⚠️  Avisos e informações
- 📊 Resumo final com taxa de sucesso

#### Exemplo de Saída

```
============================================================
          TESTES DE AUTENTICAÇÃO - TASTEMATCH
============================================================

🧪 Verificando se servidor está rodando...
  ✅ Servidor respondendo: healthy
  ℹ️  Banco de dados: connected (5 tables)

🧪 Testando POST /auth/register (novo usuário)
  ✅ Usuário registrado: teste_20250127_120000@example.com (ID: 6)
  ℹ️  Token recebido: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

[... mais testes ...]

============================================================
                    RESUMO DOS TESTES
============================================================

Total de testes: 8
✅ Passou: 8
❌ Falhou: 0

Taxa de sucesso: 100.0%
```

#### Exit Code

- `0`: Todos os testes passaram
- `1`: Algum teste falhou

Útil para CI/CD e automação.

