"""基准测试编排器"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

from ..config import Config
from ..models.base import AIProvider
from ..models.bailian import BailianProvider
from ..models.zhipu import ZhipuProvider
from ..models.anthropic_compat import AnthropicCompatibleProvider
from ..prompts.test_prompts import TEST_PROMPTS, PromptSet
from ..utils.formatter import ResultFormatter, TestResult


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_yaml()
        self.formatter = ResultFormatter()
        self._providers: Dict[str, AIProvider] = {}

    def get_provider(self, provider_name: str, model_name: str) -> Optional[AIProvider]:
        """获取或创建Provider实例"""
        cache_key = f"{provider_name}:{model_name}"

        if cache_key in self._providers:
            return self._providers[cache_key]

        api_key = self.config.get_api_key(provider_name)
        base_url = self.config.get_base_url(provider_name)
        if not api_key:
            self.formatter.print_warning(f"未配置 {provider_name} 的API密钥")
            return None

        try:
            if provider_name == "bailian":
                provider = BailianProvider(api_key, model_name, base_url)
            elif provider_name == "zhipu":
                provider = ZhipuProvider(api_key, model_name, base_url)
            elif provider_name in ("anthropic", "anthropic_lite", "volcengine"):
                provider = AnthropicCompatibleProvider(api_key, model_name, base_url)
            else:
                self.formatter.print_warning(f"未知的提供商: {provider_name}")
                return None

            self._providers[cache_key] = provider
            return provider
        except ImportError as e:
            self.formatter.print_error(f"导入 {provider_name} SDK失败: {e}")
            return None
        except Exception as e:
            self.formatter.print_error(f"创建 {provider_name} Provider失败: {e}")
            return None

    async def run_single_test(
        self,
        provider: AIProvider,
        prompt_set: PromptSet,
        iteration: int = 1
    ) -> Optional[TestResult]:
        """运行单次测试"""
        import time

        start_time = time.perf_counter()
        first_token_time = None
        total_content = ""

        try:
            async for chunk in provider.stream_generate(
                prompt=prompt_set.prompt,
                max_tokens=self.config.test_settings.max_tokens
            ):
                if first_token_time is None and chunk.content:
                    first_token_time = time.perf_counter()

                if chunk.content:
                    total_content += chunk.content
        except asyncio.TimeoutError:
            self.formatter.print_warning(f"测试超时: {provider.model_name} - {prompt_set.name}")
            return None
        except Exception as e:
            self.formatter.print_error(f"测试失败: {provider.model_name} - {prompt_set.name}: {e}")
            return None

        end_time = time.perf_counter()

        if first_token_time is None:
            return None

        ttft_ms = (first_token_time - start_time) * 1000
        total_time_ms = (end_time - start_time) * 1000
        total_tokens = await provider.count_tokens(total_content)
        tokens_per_second = total_tokens / (total_time_ms / 1000) if total_time_ms > 0 else 0

        return TestResult(
            model=provider.model_name,
            provider=provider.provider_name,
            prompt_key=prompt_set.key,
            prompt_name=prompt_set.name,
            ttft_ms=ttft_ms,
            total_tokens=total_tokens,
            total_time_ms=total_time_ms,
            tokens_per_second=tokens_per_second,
            iteration=iteration
        )

    async def run_model_benchmark(
        self,
        provider_name: str,
        model_name: str,
        prompts: Optional[List[str]] = None
    ) -> List[TestResult]:
        """运行单个模型的基准测试"""
        results = []

        provider = self.get_provider(provider_name, model_name)
        if not provider:
            return results

        # 确定要测试的prompts
        if prompts:
            test_prompts = [TEST_PROMPTS[p] for p in prompts if p in TEST_PROMPTS]
        else:
            test_prompts = list(TEST_PROMPTS.values())

        iterations = self.config.test_settings.iterations
        total_tests = len(test_prompts) * iterations
        current_test = 0

        for prompt_set in test_prompts:
            for i in range(iterations):
                current_test += 1
                self.formatter.print_running(
                    model_name,
                    prompt_set.name,
                    current_test,
                    total_tests
                )

                result = await self.run_single_test(
                    provider=provider,
                    prompt_set=prompt_set,
                    iteration=i + 1
                )

                if result:
                    results.append(result)

                # 测试间隔，避免频率限制
                await asyncio.sleep(0.5)

        return results

    async def run_full_benchmark(
        self,
        providers: Optional[List[str]] = None,
        models: Optional[Dict[str, List[str]]] = None,
        prompts: Optional[List[str]] = None
    ) -> Dict[str, List[TestResult]]:
        """
        运行完整的基准测试

        Args:
            providers: 要测试的提供商列表，None表示全部
            models: 各提供商要测试的模型，None表示全部启用的模型
            prompts: 要测试的prompt列表，None表示全部

        Returns:
            Dict[str, List[TestResult]]: 各模型的测试结果
        """
        all_results = {}

        # 确定要测试的提供商
        test_providers = providers or self.config.get_all_providers()

        for provider_name in test_providers:
            # 获取该提供商要测试的模型
            if models and provider_name in models:
                test_models = models[provider_name]
            else:
                model_configs = self.config.get_enabled_models(provider_name)
                test_models = [m.api_name for m in model_configs]

            for model_name in test_models:
                key = f"{provider_name}:{model_name}"
                self.formatter.print_info(f"\n开始测试: {provider_name} - {model_name}")

                results = await self.run_model_benchmark(
                    provider_name=provider_name,
                    model_name=model_name,
                    prompts=prompts
                )

                if results:
                    all_results[key] = results
                    self.formatter.print_model_result(results)

        # 打印对比结果
        if len(all_results) > 1:
            self.formatter.print_comparison(all_results)

        # 保存测试结果到文件
        self._save_results(all_results)

        return all_results

    def _save_results(self, all_results: Dict[str, List[TestResult]]):
        """保存测试结果到文件"""
        try:
            # 创建输出目录
            output_dir = Path.home() / ".ai_token_tester"
            output_dir.mkdir(parents=True, exist_ok=True)

            # 转换结果为可序列化的格式
            output = []
            for key, results in all_results.items():
                for r in results:
                    output.append({
                        "provider": r.provider,
                        "model": r.model,
                        "prompt": r.prompt_name,
                        "ttft_ms": r.ttft_ms,
                        "total_tokens": r.total_tokens,
                        "tokens_per_second": r.tokens_per_second,
                    })

            # 保存到文件
            output_file = output_dir / "latest_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # 保存失败不影响主流程
            pass

    def print_summary(self, all_results: Dict[str, List[TestResult]]):
        """打印测试摘要"""
        self.formatter.print_header("测试摘要")

        total_tests = sum(len(r) for r in all_results.values())
        total_models = len(all_results)

        self.formatter.print_info(f"共测试 {total_models} 个模型，{total_tests} 次测试")

        # 找出最佳性能
        if all_results:
            best_ttft = None
            best_tps = None

            for key, results in all_results.items():
                for r in results:
                    if best_ttft is None or r.ttft_ms < best_ttft[1]:
                        best_ttft = (f"{r.provider} {r.model}", r.ttft_ms)
                    if best_tps is None or r.tokens_per_second > best_tps[1]:
                        best_tps = (f"{r.provider} {r.model}", r.tokens_per_second)

            if best_ttft:
                self.formatter.print_success(
                    f"最低TTFT: {best_ttft[0]} - {best_ttft[1]:.1f}ms"
                )
            if best_tps:
                self.formatter.print_success(
                    f"最高吞吐量: {best_tps[0]} - {best_tps[1]:.1f} tokens/s"
                )