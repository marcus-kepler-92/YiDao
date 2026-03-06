import logging
import sys
from typing import Literal

from app.core.config import settings

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(level: str | None = None) -> None:
    """
    配置全局日志

    Args:
        level: 日志级别，默认从 settings 读取
    """
    log_level = level or settings.log_level

    # 根日志配置
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # 降低第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)

    # 仅在非 Debug 模式下抑制访问日志，Debug 模式下保留 INFO 级别以便查看请求
    if settings.debug:
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    else:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    获取 logger 实例

    Args:
        name: logger 名称，通常用 __name__

    Returns:
        logging.Logger

    Usage:
        from app.core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Hello")
    """
    return logging.getLogger(name)
