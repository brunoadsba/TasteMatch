# Como Executar os Testes

## Resumo

Foram criados **54 testes automatizados** cobrindo:
- ✅ Testes unitários de segurança (bcrypt, JWT)
- ✅ Testes unitários de embeddings
- ✅ Testes unitários de recomendações
- ✅ Testes de integração de autenticação
- ✅ Testes de integração de recomendações

## Executar Todos os Testes

```bash
cd backend
source ../venv/bin/activate
pytest tests/ -v
```

## Executar Testes Específicos

```bash
# Testes unitários apenas
pytest tests/test_security.py tests/test_embeddings.py tests/test_recommender.py -v

# Testes de integração apenas
pytest tests/test_integration_*.py -v

# Teste específico
pytest tests/test_security.py::TestPasswordHashing::test_verify_password_correct -v
```

## Resultado Esperado

```
========================= test session starts =========================
collected 54 items

tests/test_security.py ......................... [ 35%]
tests/test_embeddings.py ........            [ 48%]
tests/test_recommender.py ..........         [ 66%]
tests/test_integration_auth.py ..........    [ 85%]
tests/test_integration_recommendations.py ..... [100%]

======================== 54 passed in XX.XXs =========================
```

## Fixtures Disponíveis

As fixtures estão configuradas em `conftest.py` e incluem:
- Banco de dados em memória para isolamento de testes
- Usuários, restaurantes e pedidos de teste
- Cliente FastAPI configurado
- Tokens JWT de autenticação

## Notas

- Testes usam banco SQLite em memória (isolamento total)
- Testes de insights com LLM são marcados como `@pytest.mark.skip` se `GROQ_API_KEY` não estiver disponível
- Cada teste cria seus próprios dados (não há compartilhamento de estado)

