"""
Script manual para testar o endpoint de onboarding.
Execute: python scripts/test_onboarding_endpoint.py
"""

import requests
import json
import sys
import os

# Adicionar path do backend
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

def test_onboarding_endpoint():
    """Testa o endpoint de onboarding."""
    print("🧪 Testando endpoint de onboarding...")
    print()
    
    # 1. Criar usuário de teste (ou usar existente)
    print("1. Fazendo login...")
    login_data = {
        "email": "joao@example.com",  # Usuário do seed
        "password": "123456"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Erro ao fazer login: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
        
        token = response.json()["token"]
        print(f"✅ Login realizado. Token obtido.")
        print()
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Backend não está rodando em http://localhost:8000")
        print("   Execute: cd backend && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Erro ao fazer login: {e}")
        return False
    
    # 2. Testar endpoint de onboarding
    print("2. Testando endpoint /api/onboarding/complete...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    onboarding_data = {
        "selected_cuisines": ["italiana", "japonesa"],
        "price_preference": "medium",
        "dietary_restrictions": ["vegan"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/onboarding/complete",
            json=onboarding_data,
            headers=headers
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Onboarding completado com sucesso!")
            print(f"   Success: {result.get('success')}")
            print(f"   Has Synthetic Vector: {result.get('has_synthetic_vector')}")
            print(f"   Message: {result.get('message')}")
            print()
            
            # 3. Verificar se recomendações usam vetor sintético
            print("3. Verificando recomendações...")
            recommendations_response = requests.get(
                f"{BASE_URL}/api/recommendations?limit=5",
                headers=headers
            )
            
            if recommendations_response.status_code == 200:
                recommendations = recommendations_response.json()
                print(f"✅ Recomendações obtidas: {len(recommendations.get('recommendations', []))} restaurantes")
                
                if len(recommendations.get('recommendations', [])) > 0:
                    print("   Primeira recomendação:")
                    first_rec = recommendations['recommendations'][0]
                    print(f"   - Restaurante: {first_rec['restaurant']['name']}")
                    print(f"   - Culinária: {first_rec['restaurant']['cuisine_type']}")
                    print(f"   - Similarity Score: {first_rec['similarity_score']:.4f}")
                else:
                    print("   ⚠️  Nenhuma recomendação retornada")
            else:
                print(f"   ⚠️  Erro ao obter recomendações: {recommendations_response.status_code}")
            
            return True
        else:
            print(f"❌ Erro ao completar onboarding: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar endpoint: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Teste Manual - Endpoint de Onboarding")
    print("=" * 60)
    print()
    
    success = test_onboarding_endpoint()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Teste concluído com sucesso!")
    else:
        print("❌ Teste falhou. Verifique os erros acima.")
    print("=" * 60)

