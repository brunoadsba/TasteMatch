#!/usr/bin/env python3
"""
Script de teste para validar Hybrid Search do Chef Virtual
"""

import sys
import json
import requests
from typing import Dict, List

BASE_URL = "http://localhost:8000"

def get_token() -> str:
    """Obtém token de autenticação"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "teste@tastematch.com", "password": "teste123"}
    )
    return response.json()["token"]

def test_chat(token: str, message: str) -> Dict:
    """Testa endpoint de chat"""
    response = requests.post(
        f"{BASE_URL}/api/chat/",
        headers={"Authorization": f"Bearer {token}"},
        files={"message": (None, message)}
    )
    return response.json()

def print_test_result(test_name: str, message: str, result: Dict):
    """Imprime resultado do teste formatado"""
    print(f"\n{'='*60}")
    print(f"🔍 {test_name}")
    print(f"{'='*60}")
    print(f"📝 Pergunta: {message}")
    print(f"\n💬 Resposta (primeiras 200 chars):")
    print(f"   {result['answer'][:200]}...")
    
    # Filtrar apenas restaurantes
    restaurants = [
        s for s in result.get('sources', [])
        if s.get('metadata', {}).get('type') == 'restaurant'
    ]
    
    print(f"\n📊 Restaurantes encontrados ({len(restaurants)}):")
    for i, r in enumerate(restaurants[:5], 1):
        metadata = r.get('metadata', {})
        search_type = metadata.get('search_type', 'N/A')
        name = metadata.get('name', 'N/A')
        cuisine = metadata.get('cuisine_type', 'N/A')
        rating = metadata.get('rating', 'N/A')
        print(f"   {i}. {name} ({cuisine}) - Rating: {rating} - Tipo: {search_type}")
    
    # Contar tipos de busca
    exact_count = sum(1 for r in restaurants if r.get('metadata', {}).get('search_type') == 'exact')
    semantic_count = sum(1 for r in restaurants if r.get('metadata', {}).get('search_type') == 'semantic')
    
    print(f"\n📈 Estatísticas:")
    print(f"   - Busca exata: {exact_count}")
    print(f"   - Busca semântica: {semantic_count}")
    print(f"   - Total sources: {len(result.get('sources', []))}")

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes do Hybrid Search...")
    
    try:
        token = get_token()
        print("✅ Token obtido com sucesso")
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
        return
    
    # Testes
    tests = [
        {
            "name": "Teste 1: Busca Exata (Nome de Restaurante)",
            "message": "Quero ir no Fogo de Chão"
        },
        {
            "name": "Teste 2: Busca Semântica (Intenção)",
            "message": "Quero algo italiano"
        },
        {
            "name": "Teste 3: Busca Híbrida (Nome + Intenção)",
            "message": "Quero pizza no Spoleto"
        },
        {
            "name": "Teste 4: Pergunta Geral",
            "message": "Quais são os melhores restaurantes?"
        },
        {
            "name": "Teste 5: Busca por Culinária",
            "message": "Me recomende um restaurante japonês"
        }
    ]
    
    for test in tests:
        try:
            result = test_chat(token, test["message"])
            print_test_result(test["name"], test["message"], result)
        except Exception as e:
            print(f"\n❌ Erro no teste '{test['name']}': {e}")
    
    print(f"\n{'='*60}")
    print("✅ Testes concluídos!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

