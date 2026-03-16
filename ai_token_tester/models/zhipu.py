"""智普AI提供商实现"""

import asyncio
from typing import AsyncIterator, Optional

from .base import AIProvider, StreamChunk

try:
    from zhipuai import ZhipuAI
    ZHIPU_AVAILABLE = True
except ImportError:
    ZHIPU_AVAILABLE = False


class ZhipuProvider(AIProvider):
    """智普AI提供商"""

    PROVIDER_NAME = "智普"

    def __init__(
        self,
        api_key: str,
        model_name: str = "glm-4-flash",
        base_url: Optional[str] = None
    ):
        if not ZHIPU_AVAILABLE:
            raise ImportError(
                "zhipuai包未安装，请运行: pip install zhipuai"
            )
        super().__init__(api_key, model_name)
        self._base_url = base_url

        # 初始化客户端，支持自定义base_url
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = ZhipuAI(**client_kwargs)

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
        # 智普的SDK是同步的，需要在executor中运行
        def sync_stream():
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            is_first = True
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        stream_chunk = StreamChunk(
                            content=delta.content,
                            is_first=is_first,
                            is_last=False
                        )
                        is_first = False
                        yield stream_chunk
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
        return await TokenCounter.count_tokens(text, "glm")

    @classmethod
    def get_available_models(cls) -> list:
        """获取可用模型列表"""
        return [
            {"name": "glm-4-flash", "description": "GLM-4快速版"},
            {"name": "glm-4", "description": "GLM-4标准版"},
            {"name": "glm-4-plus", "description": "GLM-4增强版"},
            {"name": "glm-4-air", "description": "GLM-4轻量版"},
        ]