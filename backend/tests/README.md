# Testes do TasteMatch

Estrutura de testes automatizados para o backend do TasteMatch.

## Estrutura

```
tests/
├── conftest.py                    # Fixtures compartilhadas
├── test_security.py              # Testes unitários de segurança (bcrypt, JWT)
├── test_embeddings.py            # Testes unitários de embeddings
├── test_recommender.py           # Testes unitários de recomendações
├── test_integration_auth.py      # Testes de integração de autenticação
└── test_integration_recommendations.py  # Testes de integração de recomendações
```

## Executando os Testes

### Todos os testes

```bash
cd backend
pytest
```

### Testes específicos

```bash
# Testes unitários apenas
pytest tests/test_security.py tests/test_embeddings.py tests/test_recommender.py

# Testes de integração apenas
pytest tests/test_integration_*.py

# Teste específico
pytest tests/test_security.py::TestPasswordHashing::test_verify_password_correct

# Com verbosidade
pytest -v

# Com output detalhado
pytest -v --tb=short
```

### Com cobertura

```bash
pytest --cov=app --cov-report=html
```

## Fixtures Disponíveis

- `test_db`: Banco de dados SQLite em memória para testes
- `client`: Cliente FastAPI para testes
- `test_user`: Usuário de teste
- `test_user_2`: Segundo usuário de teste
- `test_restaurant`: Restaurante de teste
- `test_restaurants`: Lista de restaurantes de teste
- `test_order`: Pedido de teste
- `auth_token`: Token JWT autenticado
- `authenticated_client`: Cliente com autenticação configurada

## Estrutura de Testes

### Testes Unitários

Testam componentes individuais isoladamente:
- **Security**: Hash de senhas, JWT
- **Embeddings**: Geração de embeddings
- **Recommender**: Lógica de recomendação

### Testes de Integração

Testam fluxos completos end-to-end:
- **Autenticação**: Registro, login, proteção de rotas
- **Recomendações**: Geração de recomendações via API

## Notas

- Os testes usam banco de dados SQLite em memória (isolamento por teste)
- Testes que requerem `GROQ_API_KEY` são marcados com `@pytest.mark.skip` se a API key não estiver disponível
- Cada teste cria seus próprios dados (não há dados compartilhados entre testes)

