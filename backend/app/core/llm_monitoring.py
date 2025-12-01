"""
Serviço de monitoramento e observabilidade para chamadas LLM.
Coleta métricas de latência, tokens, custo e qualidade das respostas.
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from app.core.logging_config import get_logger
from app.database import crud

logger = get_logger(__name__)


class LLMMonitoringCallback(BaseCallbackHandler):
    """
    Callback do LangChain para capturar métricas de chamadas LLM.
    """
    
    def __init__(self, user_id: Optional[int] = None, question: Optional[str] = None):
        super().__init__()
        self.user_id = user_id
        self.question = question
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.model: Optional[str] = None
        self.response_text: Optional[str] = None
        self.error: Optional[str] = None
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Chamado quando o LLM inicia."""
        self.start_time = time.time()
        if prompts:
            # Estimar tokens de input (aproximação: 1 token ≈ 4 caracteres)
            self.input_tokens = sum(len(prompt) // 4 for prompt in prompts)
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Chamado quando o LLM termina."""
        self.end_time = time.time()
        
        # Extrair informações da resposta
        if response.llm_output:
            # Tentar extrair tokens se disponível
            if "token_usage" in response.llm_output:
                usage = response.llm_output["token_usage"]
                self.input_tokens = usage.get("prompt_tokens", self.input_tokens)
                self.output_tokens = usage.get("completion_tokens", 0)
            
            # Extrair modelo se disponível
            if "model_name" in response.llm_output:
                self.model = response.llm_output["model_name"]
        
        # Extrair texto da resposta
        if response.generations and len(response.generations) > 0:
            if response.generations[0] and len(response.generations[0]) > 0:
                gen = response.generations[0][0]
                if hasattr(gen, "text"):
                    self.response_text = gen.text
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Chamado quando há erro no LLM."""
        self.end_time = time.time()
        self.error = str(error)
        logger.error(f"Erro no LLM: {error}", extra={"user_id": self.user_id})
    
    def get_metrics(self, response_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Retorna métricas coletadas.
        
        Args:
            response_text: Texto da resposta (opcional, pode ser passado depois)
        """
        latency_ms = None
        if self.start_time and self.end_time:
            latency_ms = int((self.end_time - self.start_time) * 1000)
        
        # Usar response_text passado como parâmetro ou o capturado no callback
        final_response_text = response_text or self.response_text
        
        return {
            "user_id": self.user_id,
            "question": self.question,
            "model": self.model or "llama-3.1-8b-instant",
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "latency_ms": latency_ms,
            "response_length": len(final_response_text) if final_response_text else 0,
            "error": self.error,
            "timestamp": datetime.utcnow()
        }


def calculate_estimated_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "llama-3.1-8b-instant"
) -> float:
    """
    Calcula custo estimado da chamada LLM.
    
    Preços aproximados da Groq (em USD por 1M tokens):
    - llama-3.1-8b-instant: $0.05 input, $0.05 output
    
    Args:
        input_tokens: Número de tokens de input
        output_tokens: Número de tokens de output
        model: Nome do modelo
    
    Returns:
        Custo estimado em USD
    """
    # Preços por 1M tokens (aproximados)
    pricing = {
        "llama-3.1-8b-instant": {"input": 0.05, "output": 0.05},
        "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
        "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    }
    
    model_pricing = pricing.get(model, {"input": 0.05, "output": 0.05})
    
    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
    
    return input_cost + output_cost


def log_llm_metrics(
    metrics: Dict[str, Any],
    db: Optional[Session] = None,
    save_to_db: bool = True
) -> Optional[int]:
    """
    Registra métricas de chamada LLM.
    
    Args:
        metrics: Dicionário com métricas (do LLMMonitoringCallback.get_metrics())
        db: Sessão do banco de dados (opcional)
        save_to_db: Se True, salva no banco de dados
    
    Returns:
        ID do registro criado (se salvo no banco) ou None
    """
    # Calcular custo estimado
    estimated_cost = calculate_estimated_cost(
        metrics.get("input_tokens", 0),
        metrics.get("output_tokens", 0),
        metrics.get("model", "llama-3.1-8b-instant")
    )
    
    # Adicionar custo às métricas
    metrics["estimated_cost_usd"] = estimated_cost
    
    # Log estruturado
    logger.info(
        "LLM call metrics",
        extra={
            "user_id": metrics.get("user_id"),
            "model": metrics.get("model"),
            "input_tokens": metrics.get("input_tokens", 0),
            "output_tokens": metrics.get("output_tokens", 0),
            "total_tokens": metrics.get("total_tokens", 0),
            "latency_ms": metrics.get("latency_ms"),
            "estimated_cost_usd": estimated_cost,
            "error": metrics.get("error"),
            "response_length": metrics.get("response_length", 0)
        }
    )
    
    # Salvar no banco de dados se solicitado
    if save_to_db and db:
        try:
            metric_id = crud.create_llm_metric(db, metrics)
            return metric_id
        except Exception as e:
            logger.error(f"Erro ao salvar métrica LLM no banco: {e}")
            return None
    
    return None


def get_llm_metrics_summary(
    db: Session,
    user_id: Optional[int] = None,
    days: int = 7
) -> Dict[str, Any]:
    """
    Obtém resumo de métricas LLM.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário (opcional, se None retorna todas)
        days: Número de dias para considerar
    
    Returns:
        Dicionário com resumo de métricas
    """
    try:
        metrics = crud.get_llm_metrics_summary(db, user_id=user_id, days=days)
        return metrics
    except Exception as e:
        logger.error(f"Erro ao obter resumo de métricas: {e}")
        return {
            "total_calls": 0,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "avg_latency_ms": 0,
            "error_rate": 0.0
        }

