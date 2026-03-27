import sys
from loguru import logger
from .config import settings

logger.remove()

log_format = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
    "{name}:{function}:{line} | user:{extra[user_id]} | {message}"
)

logger.add(sys.stderr, level=settings.LOG_LEVEL, format=log_format)
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="30 days",
    level=settings.LOG_LEVEL,
    format=log_format,
)


def get_logger(user_id: str = "anonymous"):
    return logger.bind(user_id=user_id)
