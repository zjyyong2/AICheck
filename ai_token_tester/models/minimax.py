"""MiniMax AI Provider (OpenAI Compatible API)"""

import asyncio
from typing import AsyncIterator, Optional

from .base import AIProvider, StreamChunk

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class MiniMaxProvider(AIProvider):
    """MiniMax AI Provider - uses OpenAI compatible API"""

    PROVIDER_NAME = "MiniMax"

    def __init__(
        self,
        api_key: str,
        model_name: str = "MiniMax-M2.5",
        base_url: Optional[str] = None
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai包未安装，请运行: pip install openai"
            )
        super().__init__(api_key, model_name)
        self._base_url = base_url or "https://api.minimax.chat/v1"

        # 初始化 OpenAI 客户端 (兼容模式)
        self._client = openai.OpenAI(
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
        import time

        def sync_stream():
            start_time = time.time()
            first_token_time = None

            try:
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
                        if delta and delta.content:
                            current_time = time.time()
                            if first_token_time is None:
                                first_token_time = current_time - start_time

                            yield StreamChunk(
                                content=delta.content,
                                is_first=is_first,
                                is_last=False
                            )
                            is_first = False

                # 标记最后一个chunk
                if not is_first:
                    yield StreamChunk(
                        content="",
                        is_first=False,
                        is_last=True
                    )
            except Exception as e:
                print(f"MiniMax API Error: {e}")
                raise

        # 在线程池中运行同步代码
        loop = asyncio.get_event_loop()
        for chunk in await loop.run_in_executor(None, list, sync_stream()):
            yield chunk

    async def count_tokens(self, text: str) -> int:
        """计算token数量"""
        from ..utils.token_counter import TokenCounter
        counter = TokenCounter()
        return await counter.count_tokens(text)