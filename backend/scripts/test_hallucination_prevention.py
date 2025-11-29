#!/usr/bin/env python3
"""
Script de teste para validar prevenção de alucinações
"""

import sys
import json
import requests
from typing import Dict

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
    print(f"\n{'='*70}")
    print(f"🔍 {test_name}")
    print(f"{'='*70}")
    print(f"📝 Pergunta: {message}")
    
    # Validação
    validation = result.get("validation", {})
    confidence = validation.get("confidence_score", 0.0)
    has_hallucination = validation.get("has_potential_hallucination", False)
    used_fallback = validation.get("used_fallback", False)
    
    print(f"\n📊 Validação:")
    print(f"   - Score de Confiança: {confidence:.2f}/1.0")
    print(f"   - Total de Sources: {validation.get('total_sources', 0)}")
    print(f"   - Sources de Restaurantes: {validation.get('restaurant_sources', 0)}")
    print(f"   - Alucinação Potencial: {'⚠️ SIM' if has_hallucination else '✅ NÃO'}")
    print(f"   - Usou Fallback: {'✅ SIM' if used_fallback else '❌ NÃO'}")
    
    # Restaurantes mencionados
    mentioned = validation.get("mentioned_restaurants", [])
    valid = validation.get("valid_mentions", [])
    invalid = validation.get("invalid_mentions", [])
    
    if mentioned:
        print(f"\n🍽️ Restaurantes Mencionados:")
        print(f"   - Total: {len(mentioned)}")
        if valid:
            print(f"   - ✅ Válidos: {', '.join(valid)}")
        if invalid:
            print(f"   - ⚠️ Inválidos (alucinação): {', '.join(invalid)}")
    
    # Resposta
    answer = result.get("answer", "")
    print(f"\n💬 Resposta (primeiras 300 chars):")
    print(f"   {answer[:300]}...")
    
    # Verificar se há aviso de alucinação na resposta
    if "⚠️" in answer or "Nota:" in answer:
        print(f"\n⚠️ Aviso de alucinação detectado na resposta!")
    
    # Score de confiança
    if confidence >= 0.8:
        print(f"\n✅ Score de confiança ALTO ({confidence:.2f})")
    elif confidence >= 0.5:
        print(f"\n⚠️ Score de confiança MÉDIO ({confidence:.2f})")
    else:
        print(f"\n❌ Score de confiança BAIXO ({confidence:.2f})")

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes de prevenção de alucinações...")
    
    try:
        token = get_token()
        print("✅ Token obtido com sucesso")
    except Exception as e:
        print(f"❌ Erro ao obter token: {e}")
        return
    
    # Testes
    tests = [
        {
            "name": "Teste 1: Pergunta com Restaurante Existente",
            "message": "Quero ir no Fogo de Chão"
        },
        {
            "name": "Teste 2: Pergunta Sem Contexto de Restaurantes",
            "message": "Quais são os melhores restaurantes de comida tailandesa?"
        },
        {
            "name": "Teste 3: Pergunta Geral sobre Restaurantes",
            "message": "Me recomende restaurantes italianos"
        },
        {
            "name": "Teste 4: Pergunta Específica com Nome",
            "message": "Quero pizza no Spoleto"
        }
    ]
    
    for test in tests:
        try:
            result = test_chat(token, test["message"])
            print_test_result(test["name"], test["message"], result)
        except Exception as e:
            print(f"\n❌ Erro no teste '{test['name']}': {e}")
    
    print(f"\n{'='*70}")
    print("✅ Testes concluídos!")
    print(f"{'='*70}\n")
    
    # Resumo
    print("📋 Resumo das Melhorias Implementadas:")
    print("   1. ✅ Validação pós-resposta (verifica restaurantes mencionados)")
    print("   2. ✅ Score de confiança (0.0 a 1.0)")
    print("   3. ✅ Fallback explícito (quando não há contexto)")
    print("   4. ✅ Aviso de alucinação (adicionado à resposta)")
    print("   5. ✅ Métricas de validação na resposta da API")
    print()

if __name__ == "__main__":
    main()

