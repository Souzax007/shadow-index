"""
Módulo de logging centralizado usando loguru.
Configura logs no console e em arquivo com rotação.
"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger():
    """Configura o logger da aplicação."""
    # Remove logger padrão
    logger.remove()

    # Log no console com formatação colorida
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # Log em arquivo com rotação
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )

    return logger


# Instância global do logger
log = setup_logger()