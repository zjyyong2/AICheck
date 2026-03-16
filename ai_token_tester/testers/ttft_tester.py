"""TTFT (Time to First Token) 测试器"""

import asyncio
import time
from typing import Optional

from ..models.base import AIProvider
from ..utils.formatter import TestResult


class TTFTTester:
    """首Token延迟测试器"""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def test_single(
        self,
        prompt: str,
        prompt_key: str,
        prompt_name: str,
        max_tokens: int = 1024,
        timeout: int = 60
    ) -> Optional[TestResult]:
        """
        执行单次TTFT测试

        Args:
            prompt: 测试提示
            prompt_key: Prompt标识
            prompt_name: Prompt名称
            max_tokens: 最大输出token数
            timeout: 超时时间(秒)

        Returns:
            TestResult: 测试结果，超时返回None
        """
        start_time = time.perf_counter()
        first_token_time = None
        tokens = []
        total_content = ""

        try:
            async with asyncio.timeout(timeout):
                async for chunk in self.provider.stream_generate(prompt, max_tokens):
                    if first_token_time is None and chunk.content:
                        first_token_time = time.perf_counter()

                    if chunk.content:
                        tokens.append(chunk.content)
                        total_content += chunk.content
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            raise e

        end_time = time.perf_counter()

        # 计算指标
        if first_token_time is None:
            # 没有收到任何token
            return None

        ttft_ms = (first_token_time - start_time) * 1000
        total_time_ms = (end_time - start_time) * 1000
        total_tokens = await self.provider.count_tokens(total_content)
        tokens_per_second = total_tokens / (total_time_ms / 1000) if total_time_ms > 0 else 0

        return TestResult(
            model=self.provider.model_name,
            provider=self.provider.provider_name,
            prompt_key=prompt_key,
            prompt_name=prompt_name,
            ttft_ms=ttft_ms,
            total_tokens=total_tokens,
            total_time_ms=total_time_ms,
            tokens_per_second=tokens_per_second
        )

    async def test_multiple(
        self,
        prompt: str,
        prompt_key: str,
        prompt_name: str,
        iterations: int = 3,
        max_tokens: int = 1024,
        timeout: int = 60
    ) -> list:
        """
        执行多次测试

        Args:
            prompt: 测试提示
            prompt_key: Prompt标识
            prompt_name: Prompt名称
            iterations: 测试次数
            max_tokens: 最大输出token数
            timeout: 超时时间(秒)

        Returns:
            list[TestResult]: 测试结果列表
        """
        results = []

        for i in range(iterations):
            result = await self.test_single(
                prompt=prompt,
                prompt_key=prompt_key,
                prompt_name=prompt_name,
                max_tokens=max_tokens,
                timeout=timeout
            )
            if result:
                result.iteration = i + 1
                results.append(result)

        return results