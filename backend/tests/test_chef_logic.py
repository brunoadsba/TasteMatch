#!/usr/bin/env python3
"""
Teste unitário da lógica do Chef Recomenda.
Testa as funções diretamente sem precisar do servidor rodando.
"""

import sys
import os

# Adicionar o backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tastematch', 'backend'))

def test_imports():
    """Testa se todos os imports estão corretos."""
    print("🧪 Testando imports...")
    
    try:
        from app.core.recommender import select_chef_recommendation
        print("✅ select_chef_recommendation importado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar select_chef_recommendation: {e}")
        return False
    
    try:
        from app.core.llm_service import generate_chef_explanation, build_chef_explanation_prompt
        print("✅ generate_chef_explanation e build_chef_explanation_prompt importados com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar funções do llm_service: {e}")
        return False
    
    try:
        from app.api.routes.recommendations import ChefRecommendationResponse
        print("✅ ChefRecommendationResponse importado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao importar ChefRecommendationResponse: {e}")
        return False
    
    return True

def test_chef_selection_logic():
    """Testa a lógica de seleção do Chef."""
    print("\n🧪 Testando lógica de seleção do Chef...")
    
    try:
        from app.core.recommender import select_chef_recommendation
        from unittest.mock import MagicMock
        
        # Criar mock de recomendações
        mock_recommendations = [
            {
                "restaurant": MagicMock(
                    id=1,
                    name="Restaurante A",
                    cuisine_type="japonesa",
                    rating=4.5
                ),
                "similarity_score": 0.85
            },
            {
                "restaurant": MagicMock(
                    id=2,
                    name="Restaurante B",
                    cuisine_type="brasileira",
                    rating=4.8
                ),
                "similarity_score": 0.75
            },
            {
                "restaurant": MagicMock(
                    id=3,
                    name="Restaurante C",
                    cuisine_type="italiana",
                    rating=4.2
                ),
                "similarity_score": 0.90
            }
        ]
        
        # Criar mock de dados
        mock_orders = []
        mock_db = MagicMock()
        
        # Testar a função
        result = select_chef_recommendation(
            recommendations=mock_recommendations,
            user_id=1,
            orders=mock_orders,
            db=mock_db
        )
        
        if result:
            print("✅ Função select_chef_recommendation executada com sucesso")
            print(f"   Restaurante selecionado: {result['restaurant'].name}")
            print(f"   Score final: {result.get('final_score', 0):.2f}")
            print(f"   Confiança: {result.get('confidence', 0):.2%}")
            print(f"   Razões: {len(result.get('reasoning', []))}")
            return True
        else:
            print("❌ Função retornou None")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar lógica de seleção: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chef_explanation_prompt():
    """Testa a construção do prompt de explicação."""
    print("\n🧪 Testando construção do prompt de explicação...")
    
    try:
        from app.core.llm_service import build_chef_explanation_prompt
        from unittest.mock import MagicMock
        
        mock_restaurant = MagicMock(
            name="Sushi House",
            cuisine_type="japonesa",
            rating=4.7,
            description="Restaurante de sushi tradicional",
            price_range="medium"
        )
        
        user_context = {
            "name": "João",
            "total_orders": 10,
            "favorite_cuisines": ["japonesa", "brasileira"]
        }
        
        reasoning = [
            "Alta similaridade com suas preferências",
            "Excelente avaliação (4.7/5.0)",
            "Restaurante novo para você"
        ]
        
        prompt = build_chef_explanation_prompt(
            user_context=user_context,
            restaurant=mock_restaurant,
            reasoning=reasoning,
            similarity_score=0.85,
            confidence=0.90
        )
        
        if prompt and len(prompt) > 100:
            print("✅ Prompt construído com sucesso")
            print(f"   Tamanho do prompt: {len(prompt)} caracteres")
            print(f"   Contém 'Sushi House': {'Sushi House' in prompt}")
            print(f"   Contém 'japonesa': {'japonesa' in prompt}")
            print(f"   Contém razões: {all(r in prompt for r in reasoning)}")
            return True
        else:
            print("❌ Prompt inválido ou muito curto")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar prompt: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_response():
    """Testa se o modelo de resposta pode ser criado."""
    print("\n🧪 Testando modelo de resposta...")
    
    try:
        from app.api.routes.recommendations import ChefRecommendationResponse
        from app.models.restaurant import RestaurantResponse
        from datetime import datetime
        from unittest.mock import MagicMock
        
        mock_restaurant_response = RestaurantResponse(
            id=1,
            name="Test Restaurant",
            cuisine_type="japonesa",
            rating=4.5,
            created_at=datetime.now()
        )
        
        response = ChefRecommendationResponse(
            restaurant=mock_restaurant_response,
            similarity_score=0.85,
            explanation="Esta é uma explicação de teste",
            reasoning=["Razão 1", "Razão 2"],
            confidence=0.90,
            generated_at=datetime.now()
        )
        
        print("✅ ChefRecommendationResponse criado com sucesso")
        print(f"   Restaurante: {response.restaurant.name}")
        print(f"   Similaridade: {response.similarity_score:.2%}")
        print(f"   Confiança: {response.confidence:.2%}")
        print(f"   Razões: {len(response.reasoning)}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar modelo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal de teste."""
    print("\n" + "=" * 60)
    print("  TESTE UNITÁRIO DA LÓGICA DO CHEF RECOMENDA")
    print("=" * 60)
    
    results = []
    
    # Testar imports
    results.append(("Imports", test_imports()))
    
    # Testar lógica de seleção
    results.append(("Lógica de Seleção", test_chef_selection_logic()))
    
    # Testar prompt
    results.append(("Construção do Prompt", test_chef_explanation_prompt()))
    
    # Testar modelo
    results.append(("Modelo de Resposta", test_model_response()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("  RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n✅ Todos os testes passaram! A implementação está correta.")
        return 0
    else:
        print(f"\n❌ {total - passed} teste(s) falharam.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

