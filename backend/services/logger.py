"""统一日志模块"""

import logging
import sys

# 单行格式：时间 [级别] 消息
_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)

_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)

logger = logging.getLogger("ai-growth-assistant")
logger.setLevel(logging.INFO)
logger.addHandler(_handler)
logger.propagate = False  # 不重复输出到根 logger
