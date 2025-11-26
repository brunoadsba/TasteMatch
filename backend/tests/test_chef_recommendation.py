#!/usr/bin/env python3
"""
Script de teste para o endpoint Chef Recomenda.
Testa a implementação da Fase 1 do projeto Chef Recomenda.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"
AUTH_URL = BASE_URL  # Auth endpoints não usam /api prefix

def print_header(text):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"✅ {text}")

def print_error(text):
    """Imprime mensagem de erro."""
    print(f"❌ {text}")

def print_info(text):
    """Imprime informação."""
    print(f"ℹ️  {text}")

def test_health_check():
    """Testa se o backend está rodando."""
    print_header("1. Verificando se o backend está rodando...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Backend está rodando! Status: {data.get('status')}")
            print_info(f"Banco de dados: {data.get('database')}")
            return True
        else:
            print_error(f"Backend respondeu com status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Não foi possível conectar ao backend. Certifique-se de que o servidor está rodando:")
        print_info("  cd tastematch/backend && python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print_error(f"Erro ao verificar backend: {str(e)}")
        return False

def login_or_register(email="test@example.com", password="test123", name="Usuário Teste"):
    """Faz login ou registra um novo usuário."""
    print_header("2. Autenticando usuário...")
    
    # Tentar login primeiro
    try:
        response = requests.post(
            f"{AUTH_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            print_success(f"Login realizado com sucesso!")
            print_info(f"Usuário: {user.get('name')} ({user.get('email')})")
            print_info(f"User ID: {user.get('id')}")
            return token, user.get("id")
    except Exception as e:
        print_info(f"Login falhou, tentando registrar novo usuário: {str(e)}")
    
    # Tentar registrar se login falhou
    try:
        response = requests.post(
            f"{AUTH_URL}/auth/register",
            json={
                "email": email,
                "password": password,
                "name": name
            },
            timeout=5
        )
        
        if response.status_code == 201:
            data = response.json()
            token = data.get("token")
            user = data.get("user")
            print_success(f"Usuário registrado com sucesso!")
            print_info(f"Usuário: {user.get('name')} ({user.get('email')})")
            print_info(f"User ID: {user.get('id')}")
            return token, user.get("id")
        else:
            print_error(f"Registro falhou com status {response.status_code}")
            print_error(response.text)
            return None, None
    except Exception as e:
        print_error(f"Erro ao registrar usuário: {str(e)}")
        return None, None

def test_chef_recommendation(token):
    """Testa o endpoint Chef Recomenda."""
    print_header("3. Testando endpoint Chef Recomenda...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print_info("Fazendo requisição para /api/recommendations/chef-choice...")
        response = requests.get(
            f"{API_URL}/recommendations/chef-choice",
            headers=headers,
            timeout=30  # Pode demorar um pouco devido ao LLM
        )
        
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Recomendação do Chef obtida com sucesso!")
            print("\n📋 DETALHES DA RECOMENDAÇÃO:")
            print("-" * 60)
            
            restaurant = data.get("restaurant", {})
            print(f"🏪 Restaurante: {restaurant.get('name')}")
            print(f"🍽️  Tipo de Culinária: {restaurant.get('cuisine_type')}")
            print(f"⭐ Avaliação: {restaurant.get('rating')}/5.0")
            print(f"💰 Faixa de Preço: {restaurant.get('price_range', 'N/A')}")
            
            print(f"\n📊 SCORES:")
            print(f"   Similaridade: {data.get('similarity_score', 0):.2%}")
            print(f"   Confiança: {data.get('confidence', 0):.2%}")
            
            reasoning = data.get("reasoning", [])
            if reasoning:
                print(f"\n💡 RAZÕES DA ESCOLHA:")
                for i, reason in enumerate(reasoning, 1):
                    print(f"   {i}. {reason}")
            
            explanation = data.get("explanation", "")
            if explanation:
                print(f"\n👨‍🍳 EXPLICAÇÃO DO CHEF:")
                print(f"   {explanation}")
            
            print(f"\n🕒 Gerado em: {data.get('generated_at', 'N/A')}")
            print("-" * 60)
            
            return True
        else:
            print_error(f"Erro ao obter recomendação: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Timeout ao aguardar resposta do servidor (pode ser devido ao LLM)")
        return False
    except Exception as e:
        print_error(f"Erro ao testar endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_chef_recommendation_with_refresh(token):
    """Testa o endpoint Chef Recomenda com refresh."""
    print_header("4. Testando endpoint Chef Recomenda com refresh...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print_info("Fazendo requisição com ?refresh=true...")
        response = requests.get(
            f"{API_URL}/recommendations/chef-choice?refresh=true",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print_success("Recomendação recalculada com sucesso!")
            data = response.json()
            restaurant = data.get("restaurant", {})
            print_info(f"Restaurante recomendado: {restaurant.get('name')}")
            return True
        else:
            print_error(f"Erro: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Erro: {str(e)}")
        return False

def main():
    """Função principal de teste."""
    print("\n" + "🧪 TESTE DO ENDPOINT CHEF RECOMENDA".center(60))
    print("=" * 60)
    
    # 1. Verificar backend
    if not test_health_check():
        sys.exit(1)
    
    # 2. Autenticar
    token, user_id = login_or_register()
    if not token:
        print_error("Não foi possível autenticar. Abortando testes.")
        sys.exit(1)
    
    # 3. Testar endpoint
    success = test_chef_recommendation(token)
    
    # 4. Testar com refresh
    if success:
        test_chef_recommendation_with_refresh(token)
    
    # Resumo final
    print_header("RESUMO DOS TESTES")
    if success:
        print_success("✅ Todos os testes principais passaram!")
        print_info("O endpoint Chef Recomenda está funcionando corretamente.")
    else:
        print_error("❌ Alguns testes falharam.")
        print_info("Verifique os logs acima para mais detalhes.")
    
    print("\n")

if __name__ == "__main__":
    main()

