"""质量评估运行器"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..config import Config
from ..evaluators.base import QualityScore
from ..evaluators.rule_evaluator import RuleEvaluator
from ..models.base import AIProvider
from ..models.bailian import BailianProvider
from ..models.zhipu import ZhipuProvider
from ..models.anthropic_compat import AnthropicCompatibleProvider
from ..models.minimax import MiniMaxProvider
from ..prompts.eval_prompts import EVAL_PROMPTS, EvalPrompt, get_eval_prompt
from ..storage.history import HistoryStorage
from ..utils.formatter import ResultFormatter


@dataclass
class QualityResult:
    """质量测试结果"""
    model: str
    provider: str
    test_key: str
    test_name: str
    prompt: str
    response: str
    score: QualityScore
    iteration: int = 1


@dataclass
class QualityComparisonResult:
    """质量对比结果"""
    test_id: str
    run_time: str
    results: Dict[str, List[QualityResult]] = field(default_factory=dict)
    # 聚合结果
    model_avg_scores: Dict[str, float] = field(default_factory=dict)


class QualityBenchmarkRunner:
    """质量评估运行器"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.from_yaml()
        self.formatter = ResultFormatter()
        self.evaluator = RuleEvaluator()
        self.storage = HistoryStorage()
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
            elif provider_name == "minimax":
                provider = MiniMaxProvider(api_key, model_name, base_url)
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

    async def run_single_eval(
        self,
        provider: AIProvider,
        eval_prompt: EvalPrompt,
        iteration: int = 1
    ) -> Optional[QualityResult]:
        """运行单次质量评估"""
        try:
            # 获取模型回答
            response = ""
            async for chunk in provider.stream_generate(
                prompt=eval_prompt.prompt,
                max_tokens=self.config.test_settings.max_tokens
            ):
                if chunk.content:
                    response += chunk.content

            if not response:
                self.formatter.print_warning(f"未获取到回答: {provider.model_name} - {eval_prompt.name}")
                return None

            # 评估回答质量
            score = await self.evaluator.evaluate(
                prompt=eval_prompt.prompt,
                response=response,
                expected_keywords=eval_prompt.expected_keywords,
                expected_answer=eval_prompt.expected_answer,
            )

            # 保存到历史数据库
            self.storage.save_result(
                model=provider.model_name,
                provider=provider.provider_name,
                test_key=eval_prompt.key,
                correctness=score.correctness,
                completeness=score.completeness,
                coherence=score.coherence,
                overall=score.overall,
            )

            return QualityResult(
                model=provider.model_name,
                provider=provider.provider_name,
                test_key=eval_prompt.key,
                test_name=eval_prompt.name,
                prompt=eval_prompt.prompt,
                response=response,
                score=score,
                iteration=iteration,
            )

        except asyncio.TimeoutError:
            self.formatter.print_warning(f"测试超时: {provider.model_name} - {eval_prompt.name}")
            return None
        except Exception as e:
            self.formatter.print_error(f"测试失败: {provider.model_name} - {eval_prompt.name}: {e}")
            return None

    async def run_model_quality_eval(
        self,
        provider_name: str,
        model_name: str,
        test_keys: Optional[List[str]] = None,
        iterations: int = 1
    ) -> List[QualityResult]:
        """运行单个模型的质量评估"""
        results = []

        provider = self.get_provider(provider_name, model_name)
        if not provider:
            return results

        # 确定要测试的prompts
        if test_keys:
            test_prompts = [EVAL_PROMPTS[k] for k in test_keys if k in EVAL_PROMPTS]
        else:
            test_prompts = list(EVAL_PROMPTS.values())

        total_tests = len(test_prompts) * iterations
        current_test = 0

        for eval_prompt in test_prompts:
            for i in range(iterations):
                current_test += 1
                self.formatter.print_running(
                    model_name,
                    eval_prompt.name,
                    current_test,
                    total_tests
                )

                result = await self.run_single_eval(
                    provider=provider,
                    eval_prompt=eval_prompt,
                    iteration=i + 1
                )

                if result:
                    results.append(result)

                # 测试间隔，避免频率限制
                await asyncio.sleep(0.5)

        return results

    async def run_comparison(
        self,
        providers: Optional[List[str]] = None,
        models: Optional[Dict[str, List[str]]] = None,
        test_keys: Optional[List[str]] = None,
        iterations: int = 1
    ) -> QualityComparisonResult:
        """
        运行质量对比测试

        Args:
            providers: 要测试的提供商列表，None表示全部
            models: 各提供商要测试的模型，None表示全部启用的模型
            test_keys: 要测试的eval prompt key列表，None表示全部
            iterations: 每个测试的迭代次数

        Returns:
            QualityComparisonResult: 对比结果
        """
        from datetime import datetime

        comparison = QualityComparisonResult(
            test_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            run_time=datetime.now().isoformat(),
        )

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
                self.formatter.print_info(f"\n开始质量评估: {provider_name} - {model_name}")

                results = await self.run_model_quality_eval(
                    provider_name=provider_name,
                    model_name=model_name,
                    test_keys=test_keys,
                    iterations=iterations,
                )

                if results:
                    comparison.results[key] = results
                    # 计算该模型的平均分
                    avg_score = sum(r.score.overall for r in results) / len(results)
                    comparison.model_avg_scores[key] = avg_score

        # 打印对比结果
        self._print_comparison(comparison)

        return comparison

    def _print_comparison(self, comparison: QualityComparisonResult):
        """打印对比结果"""
        self.formatter.print_header("质量评估对比结果")

        if not comparison.results:
            self.formatter.print_warning("没有可展示的结果")
            return

        # 按平均分排序
        sorted_models = sorted(
            comparison.model_avg_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 打印排名
        print("\n排名 | 模型 | 平均分")
        print("-" * 40)
        for rank, (key, avg_score) in enumerate(sorted_models, 1):
            print(f" {rank}   | {key} | {avg_score:.2%}")

        # 打印详细结果
        self.formatter.print_header("详细结果")
        for key, results in comparison.results.items():
            print(f"\n### {key}")
            for r in results:
                print(f"  {r.test_name}: {r.score.overall:.1%} "
                      f"(正确性:{r.score.correctness:.1%} "
                      f"完整性:{r.score.completeness:.1%} "
                      f"连贯性:{r.score.coherence:.1%})")
                print(f"    详情: {r.score.details}")


async def run_quality_test(
    providers: Optional[List[str]] = None,
    models: Optional[Dict[str, List[str]]] = None,
    test_keys: Optional[List[str]] = None,
    iterations: int = 1,
):
    """运行质量测试的便捷函数"""
    runner = QualityBenchmarkRunner()
    return await runner.run_comparison(
        providers=providers,
        models=models,
        test_keys=test_keys,
        iterations=iterations,
    )