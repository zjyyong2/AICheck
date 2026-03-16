"""Anthropic兼容接口提供商实现"""

import asyncio
from typing import AsyncIterator, Optional

from .base import AIProvider, StreamChunk

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicCompatibleProvider(AIProvider):
    """Anthropic兼容接口提供商"""

    PROVIDER_NAME = "百炼(Anthropic兼容)"

    def __init__(
        self,
        api_key: str,
        model_name: str = "qwen3.5-plus",
        base_url: Optional[str] = None
    ):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic包未安装，请运行: pip install anthropic"
            )
        super().__init__(api_key, model_name)
        self._base_url = base_url or "https://coding.dashscope.aliyuncs.com/apps/anthropic"

        # 初始化 Anthropic 客户端
        self._client = anthropic.Anthropic(
            api_key=api_key,
            base_url=self._base_url
        )

    @property
    def provider_name(self) -> str:
        return self.PROVIDER_NAME

    @property
    def base_url(self) -> Optional[str]:
        return self._base_url

    async def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """流式生成文本"""
        def sync_stream():
            with self._client.messages.stream(
                model=self._model_name,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                is_first = True
                for text in stream.text_stream:
                    if text:
                        yield StreamChunk(
                            content=text,
                            is_first=is_first,
                            is_last=False
                        )
                        is_first = False
            # 标记最后一个chunk
            if not is_first:
                yield StreamChunk(content="", is_first=False, is_last=True)

        # 在线程池中运行同步代码
        loop = asyncio.get_event_loop()
        for chunk in await loop.run_in_executor(None, list, sync_stream()):
            yield chunk

    async def count_tokens(self, text: str) -> int:
        """计算token数量"""
        from ..utils.token_counter import TokenCounter
        return await TokenCounter.count_tokens(text, "qwen")

    @classmethod
    def get_available_models(cls) -> list:
        """获取可用模型列表"""
        return [
            {"name": "qwen3.5-plus", "description": "通义千问3.5增强版"},
            {"name": "qwen3.5-turbo", "description": "通义千问3.5快速版"},
            {"name": "glm-5", "description": "智普GLM-5"},
        ]