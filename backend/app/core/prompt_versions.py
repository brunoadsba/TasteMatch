"""
Gerenciamento de versões de prompt para testes A/B
"""

from typing import Dict, Optional
from enum import Enum


class PromptVersion(str, Enum):
    """Versões disponíveis de prompt"""
    V1 = "v1"  # Padrão - balanceado
    V2 = "v2"  # Conciso e direto
    V3 = "v3"  # Amigável e conversacional


# Configuração de versões (pode ser movido para settings ou feature flags)
PROMPT_VERSION_CONFIG = {
    "default": PromptVersion.V1,
    "enabled_versions": [PromptVersion.V1, PromptVersion.V2, PromptVersion.V3],
    # Distribuição para A/B testing (percentual)
    "ab_test_distribution": {
        PromptVersion.V1: 50,  # 50% dos usuários
        PromptVersion.V2: 25,  # 25% dos usuários
        PromptVersion.V3: 25,  # 25% dos usuários
    }
}


def get_prompt_version_for_user(user_id: Optional[int] = None) -> str:
    """
    Retorna versão de prompt para um usuário (para A/B testing)
    
    Args:
        user_id: ID do usuário (opcional, para consistência)
    
    Returns:
        Versão do prompt (v1, v2, v3)
    """
    # Por enquanto, retornar versão padrão
    # Em produção, pode usar hash do user_id para distribuição consistente
    if user_id:
        # Distribuição consistente baseada em user_id
        hash_value = hash(str(user_id)) % 100
        cumulative = 0
        for version, percentage in PROMPT_VERSION_CONFIG["ab_test_distribution"].items():
            cumulative += percentage
            if hash_value < cumulative:
                return version.value
    
    return PROMPT_VERSION_CONFIG["default"].value


def get_prompt_metrics_template() -> Dict:
    """
    Retorna template para métricas de prompt
    
    Returns:
        Dicionário com estrutura de métricas
    """
    return {
        "prompt_version": None,
        "response_length": 0,
        "response_time_ms": 0,
        "sources_count": 0,
        "restaurants_mentioned": 0,
        "user_satisfaction": None,  # Pode ser coletado via feedback
        "timestamp": None
    }

