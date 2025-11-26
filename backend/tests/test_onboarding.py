"""
Testes para o sistema de onboarding gamificado.
"""

import pytest
from sqlalchemy.orm import Session
from app.database.models import User, UserPreferences, Restaurant
from app.core.onboarding_service import (
    generate_cold_start_embedding,
    complete_onboarding,
    normalize_cuisine_type
)
from app.database.crud import get_user_preferences
import json


def test_normalize_cuisine_type():
    """Testa normalização de tipos de culinária."""
    assert normalize_cuisine_type("Italiano") == "italiana"
    assert normalize_cuisine_type("JAPONÊS") == "japonesa"
    assert normalize_cuisine_type("brasileiro") == "brasileira"
    assert normalize_cuisine_type("mexicano") == "mexicana"
    assert normalize_cuisine_type("chinesa") == "chinesa"  # Já normalizado
    assert normalize_cuisine_type("indiana") == "indiana"  # Já normalizado


def test_generate_cold_start_embedding_with_restaurants(db: Session):
    """Testa geração de vetor sintético quando há restaurantes no banco."""
    # Verificar se há restaurantes no banco
    from app.database.crud import get_restaurants
    restaurants = get_restaurants(db, skip=0, limit=10)
    
    if len(restaurants) == 0:
        pytest.skip("Não há restaurantes no banco para testar")
    
    # Buscar culinárias disponíveis
    cuisine_types = set()
    for r in restaurants:
        if r.embedding and r.rating and float(r.rating) >= 4.0:
            cuisine_types.add(r.cuisine_type)
    
    if len(cuisine_types) == 0:
        pytest.skip("Não há restaurantes com rating >= 4.0 e embedding")
    
    # Testar com uma culinária disponível
    selected_cuisine = list(cuisine_types)[0]
    synthetic_vector = generate_cold_start_embedding(
        selected_cuisines=[selected_cuisine],
        db=db
    )
    
    assert synthetic_vector is not None, "Vetor sintético deve ser gerado"
    assert isinstance(synthetic_vector, list), "Vetor deve ser uma lista"
    assert len(synthetic_vector) > 0, "Vetor não deve estar vazio"
    # Embedding deve ter 384 dimensões (all-MiniLM-L6-v2)
    assert len(synthetic_vector) == 384, f"Vetor deve ter 384 dimensões, tem {len(synthetic_vector)}"


def test_generate_cold_start_embedding_no_restaurants(db: Session):
    """Testa geração de vetor sintético quando não há restaurantes."""
    # Usar culinária que não existe no banco
    synthetic_vector = generate_cold_start_embedding(
        selected_cuisines=["culinaria_inexistente_123"],
        db=db
    )
    
    # Deve retornar None quando não encontra restaurantes
    assert synthetic_vector is None or len(synthetic_vector) == 0


def test_complete_onboarding(db: Session, test_user: User):
    """Testa completar onboarding de um usuário."""
    from app.database.crud import get_restaurants
    restaurants = get_restaurants(db, skip=0, limit=10)
    
    if len(restaurants) == 0:
        pytest.skip("Não há restaurantes no banco para testar")
    
    # Buscar culinárias disponíveis
    cuisine_types = set()
    for r in restaurants:
        if r.embedding and r.rating and float(r.rating) >= 4.0:
            cuisine_types.add(r.cuisine_type)
    
    if len(cuisine_types) == 0:
        pytest.skip("Não há restaurantes com rating >= 4.0 e embedding")
    
    selected_cuisines = list(cuisine_types)[:2]  # Pegar até 2 culinárias
    
    # Completar onboarding
    success = complete_onboarding(
        user_id=test_user.id,
        selected_cuisines=selected_cuisines,
        price_preference="medium",
        db=db
    )
    
    assert success is True, "Onboarding deve ser completado com sucesso"
    
    # Verificar se preferências foram salvas
    preferences = get_user_preferences(db, user_id=test_user.id)
    assert preferences is not None, "Preferências devem ser criadas"
    assert preferences.preference_embedding is not None, "Embedding deve ser salvo"
    
    # Verificar se embedding é válido
    embedding = json.loads(preferences.preference_embedding)
    assert isinstance(embedding, list), "Embedding deve ser uma lista"
    assert len(embedding) == 384, "Embedding deve ter 384 dimensões"
    
    # Verificar se culinárias favoritas foram salvas
    if preferences.favorite_cuisines:
        favorite_cuisines = json.loads(preferences.favorite_cuisines)
        assert isinstance(favorite_cuisines, list), "Culinárias favoritas devem ser uma lista"
        assert len(favorite_cuisines) > 0, "Deve ter pelo menos uma culinária favorita"


def test_onboarding_with_price_preference(db: Session, test_user: User):
    """Testa onboarding com filtro de preço."""
    from app.database.crud import get_restaurants
    restaurants = get_restaurants(db, skip=0, limit=100)
    
    if len(restaurants) == 0:
        pytest.skip("Não há restaurantes no banco para testar")
    
    # Buscar culinárias disponíveis
    cuisine_types = set()
    for r in restaurants:
        if r.embedding and r.rating and float(r.rating) >= 4.0:
            cuisine_types.add(r.cuisine_type)
    
    if len(cuisine_types) == 0:
        pytest.skip("Não há restaurantes com rating >= 4.0 e embedding")
    
    selected_cuisine = list(cuisine_types)[0]
    
    # Testar com diferentes faixas de preço
    for price in ["low", "medium", "high"]:
        synthetic_vector = generate_cold_start_embedding(
            selected_cuisines=[selected_cuisine],
            price_preference=price,
            db=db
        )
        
        # Pode retornar None se não houver restaurantes com essa faixa de preço
        # Mas não deve quebrar
        if synthetic_vector is not None:
            assert len(synthetic_vector) == 384, f"Vetor deve ter 384 dimensões para preço {price}"

