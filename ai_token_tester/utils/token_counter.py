"""Token计数工具"""

import asyncio
from typing import Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class TokenCounter:
    """Token计数器"""

    # 模型到tiktoken编码的映射
    MODEL_ENCODING_MAP = {
        "qwen": "cl100k_base",  # 通义千问使用cl100k_base近似
        "glm": "cl100k_base",   # GLM使用cl100k_base近似
        "gpt": "cl100k_base",
        "default": "cl100k_base",
    }

    _encodings = {}

    @classmethod
    async def count_tokens(cls, text: str, model_type: str = "default") -> int:
        """
        计算文本的token数量

        Args:
            text: 要计算的文本
            model_type: 模型类型 (qwen, glm, gpt等)

        Returns:
            int: token数量
        """
        if not TIKTOKEN_AVAILABLE:
            # 如果tiktoken不可用，使用简单的估算
            return cls._simple_estimate(text)

        encoding_name = cls.MODEL_ENCODING_MAP.get(model_type, "cl100k_base")

        if encoding_name not in cls._encodings:
            cls._encodings[encoding_name] = tiktoken.get_encoding(encoding_name)

        encoding = cls._encodings[encoding_name]

        # 在线程池中运行，避免阻塞
        loop = asyncio.get_event_loop()
        tokens = await loop.run_in_executor(None, encoding.encode, text)
        return len(tokens)

    @staticmethod
    def _simple_estimate(text: str) -> int:
        """
        简单估算token数量
        中文约1.5字符/token，英文约4字符/token
        """
        # 统计中文字符数
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        # 统计非中文字符数
        other_chars = len(text) - chinese_chars

        # 估算
        return int(chinese_chars / 1.5 + other_chars / 4)

    @classmethod
    def count_tokens_sync(cls, text: str, model_type: str = "default") -> int:
        """同步版本的token计数"""
        if not TIKTOKEN_AVAILABLE:
            return cls._simple_estimate(text)

        encoding_name = cls.MODEL_ENCODING_MAP.get(model_type, "cl100k_base")

        if encoding_name not in cls._encodings:
            cls._encodings[encoding_name] = tiktoken.get_encoding(encoding_name)

        encoding = cls._encodings[encoding_name]
        return len(encoding.encode(text))