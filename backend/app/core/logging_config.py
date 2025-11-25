"""
Configuração de logging estruturado para o TasteMatch.
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from app.config import settings


class StructuredFormatter(logging.Formatter):
    """Formatter que gera logs em formato JSON estruturado."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o log em JSON estruturado."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Adicionar campos extras se existirem
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "endpoint"):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "count"):
            log_data["count"] = record.count
        
        # Adicionar exception se houver
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Adicionar stack trace se houver
        if hasattr(record, "stack_info") and record.stack_info:
            log_data["stack_info"] = record.stack_info
        
        return json.dumps(log_data, ensure_ascii=False)


class HumanReadableFormatter(logging.Formatter):
    """Formatter legível para desenvolvimento."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o log de forma legível."""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        logger = record.name
        
        message = record.getMessage()
        
        # Adicionar campos extras
        extras = []
        if hasattr(record, "user_id"):
            extras.append(f"user_id={record.user_id}")
        if hasattr(record, "endpoint"):
            extras.append(f"endpoint={record.endpoint}")
        if hasattr(record, "duration_ms"):
            extras.append(f"duration={record.duration_ms}ms")
        if hasattr(record, "count"):
            extras.append(f"count={record.count}")
        
        extra_str = f" [{', '.join(extras)}]" if extras else ""
        
        formatted = f"[{timestamp}] {level} {logger} - {message}{extra_str}"
        
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging():
    """
    Configura o sistema de logging da aplicação.
    
    Em desenvolvimento: formato legível (HumanReadableFormatter)
    Em produção: formato JSON estruturado (StructuredFormatter)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Remover handlers existentes
    root_logger.handlers.clear()
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Escolher formatter baseado no ambiente
    if settings.ENVIRONMENT == "production":
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configurar nível de logs de bibliotecas externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger com nome específico.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        
    Returns:
        logging.Logger: Logger configurado
    """
    return logging.getLogger(name)

