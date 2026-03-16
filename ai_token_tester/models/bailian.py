"""百炼(DashScope)提供商实现"""

import asyncio
from typing import AsyncIterator, Optional

from .base import AIProvider, StreamChunk

try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False


class BailianProvider(AIProvider):
    """百炼(DashScope)提供商"""

    PROVIDER_NAME = "百炼"

    def __init__(
        self,
        api_key: str,
        model_name: str = "qwen-turbo",
        base_url: Optional[str] = None
    ):
        if not DASHSCOPE_AVAILABLE:
            raise ImportError(
                "dashscope包未安装，请运行: pip install dashscope"
            )
        super().__init__(api_key, model_name)
        dashscope.api_key = api_key
        self._base_url = base_url

        # 如果设置了自定义base_url，使用HTTP客户端
        if base_url:
            self._client = None  # 可以使用自定义HTTP客户端

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
        # DashScope的SDK是同步的，需要在executor中运行
        def sync_stream():
            responses = Generation.call(
                model=self._model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                stream=True,
                result_format="message",
                **kwargs
            )
            is_first = True
            for response in responses:
                if response.status_code == 200:
                    content = response.output.choices[0].message.content
                    if content:
                        chunk = StreamChunk(
                            content=content,
                            is_first=is_first,
                            is_last=False
                        )
                        is_first = False
                        yield chunk
            # 标记最后一个chunk
            if not is_first:
                yield StreamChunk(content="", is_first=False, is_last=True)

        # 在线程池中运行同步代码
        loop = asyncio.get_event_loop()
        for chunk in await loop.run_in_executor(None, list, sync_stream()):
            yield chunk

    async def count_tokens(self, text: str) -> int:
        """计算token数量"""
        # 使用tiktoken进行估算
        from ..utils.token_counter import TokenCounter
        return await TokenCounter.count_tokens(text, "qwen")

    @classmethod
    def get_available_models(cls) -> list:
        """获取可用模型列表"""
        return [
            {"name": "qwen-turbo", "description": "通义千问快速版"},
            {"name": "qwen-plus", "description": "通义千问增强版"},
            {"name": "qwen-max", "description": "通义千问旗舰版"},
            {"name": "qwen-long", "description": "通义千问长文本版"},
        ]