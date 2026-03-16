"""AI提供商抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, Optional


@dataclass
class StreamMetrics:
    """流式输出指标"""
    ttft_ms: float  # 首token延迟(毫秒)
    total_tokens: int  # 总输出token数
    total_time_ms: float  # 总耗时(毫秒)
    tokens_per_second: float  # 吞吐量

    def __str__(self) -> str:
        return (
            f"TTFT: {self.ttft_ms:.1f}ms | "
            f"Tokens: {self.total_tokens} | "
            f"Time: {self.total_time_ms:.1f}ms | "
            f"Speed: {self.tokens_per_second:.1f} tokens/s"
        )


@dataclass
class StreamChunk:
    """流式输出块"""
    content: str
    is_first: bool = False
    is_last: bool = False


class AIProvider(ABC):
    """AI提供商抽象基类"""

    def __init__(self, api_key: str, model_name: str):
        self._api_key = api_key
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商名称"""
        pass

    @abstractmethod
    async def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """
        流式生成文本

        Args:
            prompt: 输入提示
            max_tokens: 最大输出token数
            **kwargs: 其他参数

        Yields:
            StreamChunk: 流式输出块
        """
        pass

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        计算文本的token数量

        Args:
            text: 要计算的文本

        Returns:
            int: token数量
        """
        pass

    def validate_api_key(self) -> bool:
        """验证API密钥是否有效"""
        return bool(self._api_key and len(self._api_key) > 0)