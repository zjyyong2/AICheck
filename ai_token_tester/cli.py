"""CLI入口模块"""

import argparse
import asyncio
import sys
from typing import Optional

from .config import Config
from .testers.benchmark import BenchmarkRunner
from .testers.quality_runner import QualityBenchmarkRunner
from .prompts.test_prompts import TEST_PROMPTS, get_prompt_keys
from .prompts.eval_prompts import get_all_eval_keys
from .utils.formatter import ResultFormatter
from .monitors.detector import run_detection
from .storage.history import HistoryStorage


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="ai-token-tester",
        description="测试百炼和智普AI平台各模型的token输出速度",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试所有模型
  python -m ai_token_tester

  # 快速测试（只测简单代码生成）
  python -m ai_token_tester --quick

  # 只测试百炼
  python -m ai_token_tester --provider anthropic

  # 测试特定模型
  python -m ai_token_tester --model qwen3.5-plus

  # 测试特定prompt
  python -m ai_token_tester --prompt simple_code

  # 设置测试次数
  python -m ai_token_tester --iterations 5

环境变量:
  DASHSCOPE_API_KEY    百炼API密钥
  ANTHROPIC_API_KEY    Anthropic兼容接口密钥
  ZHIPUAI_API_KEY      智普API密钥
        """
    )

    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="快速测试模式：只测试简单代码生成，迭代1次"
    )

    parser.add_argument(
        "--provider", "-p",
        type=str,
        help="指定测试的提供商 (anthropic/anthropic_lite/bailian/zhipu)"
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        help="指定测试的模型名称"
    )

    parser.add_argument(
        "--prompt",
        type=str,
        choices=get_prompt_keys(),
        help="指定测试的prompt"
    )

    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=None,
        help="每个测试重复次数 (默认: 3)"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="最大输出token数 (默认: 1024)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="单次请求超时时间(秒) (默认: 60)"
    )

    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="配置文件路径"
    )

    parser.add_argument(
        "--list-models",
        action="store_true",
        help="列出所有可用模型"
    )

    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="列出所有测试prompt"
    )

    # 质量评估相关参数
    parser.add_argument(
        "--compare-quality",
        action="store_true",
        help="运行质量对比测试（评估模型输出质量）"
    )

    parser.add_argument(
        "--detect-degradation",
        action="store_true",
        help="运行降智检测（检查模型是否降智）"
    )

    parser.add_argument(
        "--quality-history",
        action="store_true",
        help="查看质量历史"
    )

    parser.add_argument(
        "--model-quality",
        type=str,
        help="指定要查看历史的模型名称（用于--quality-history）"
    )

    parser.add_argument(
        "--eval-prompt",
        type=str,
        choices=get_all_eval_keys(),
        help="指定质量评估的prompt"
    )

    return parser


def list_models(config: Config):
    """列出所有可用模型"""
    formatter = ResultFormatter()
    formatter.print_header("可用模型列表")

    for provider in config.get_all_providers():
        models = config.models.get(provider, [])
        formatter.print_info(f"\n{provider.upper()}:")
        for model in models:
            status = "[ON]" if model.enabled else "[OFF]"
            formatter.print_info(f"  {status} {model.name} ({model.api_name})")


def list_prompts():
    """列出所有测试prompt"""
    formatter = ResultFormatter()
    formatter.print_header("测试Prompt列表")

    for key, prompt_set in TEST_PROMPTS.items():
        formatter.print_info(
            f"\n{key}:\n"
            f"  名称: {prompt_set.name}\n"
            f"  类别: {prompt_set.category}\n"
            f"  预期tokens: {prompt_set.expected_tokens}\n"
            f"  Prompt: {prompt_set.prompt[:50]}..."
        )


async def run_quality_comparison(args: argparse.Namespace, config: Config):
    """运行质量对比测试"""
    formatter = ResultFormatter()
    runner = QualityBenchmarkRunner(config)

    # 确定要测试的提供商和模型
    providers = [args.provider] if args.provider else None
    models = None

    if args.model:
        if args.provider:
            models = {args.provider: [args.model]}
        else:
            for provider, model_list in config.models.items():
                for m in model_list:
                    if m.api_name == args.model or m.name == args.model:
                        models = {provider: [m.api_name]}
                        break

    # 确定要测试的eval prompt
    test_keys = [args.eval_prompt] if args.eval_prompt else None

    formatter.print_header("AI Model Quality Benchmark")
    formatter.print_info("开始质量评估...\n")

    try:
        result = await runner.run_comparison(
            providers=providers,
            models=models,
            test_keys=test_keys,
            iterations=1,
        )

        if result.results:
            formatter.print_success("质量评估完成")
        else:
            formatter.print_warning("没有完成任何测试")

    except KeyboardInterrupt:
        formatter.print_warning("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        formatter.print_error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def run_degradation_detection(args: argparse.Namespace):
    """运行降智检测"""
    formatter = ResultFormatter()
    formatter.print_header("降智检测")
    formatter.print_info("正在分析历史数据...\n")

    models = None
    if args.model:
        models = [args.model]

    try:
        alerts = run_detection(
            models=models,
            window_size=7,
            drop_threshold=0.15,
        )

        if alerts:
            sys.exit(1)  # 有告警时返回错误码

    except Exception as e:
        formatter.print_error(f"检测失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def show_quality_history(args: argparse.Namespace):
    """显示质量历史"""
    formatter = ResultFormatter()
    storage = HistoryStorage()

    model = args.model_quality if args.model_quality else None

    if model:
        history = storage.get_history(model, days=30)
        if history:
            formatter.print_header(f"质量历史: {model}")
            print(f"\n{'时间'.center(20)} | {'正确性'.center(8)} | {'完整性'.center(8)} | {'连贯性'.center(8)} | {'综合'.center(8)}")
            print("-" * 70)
            for record in history[:20]:
                time_str = record.run_time.strftime("%Y-%m-%d %H:%M")
                print(f"{time_str:^20} | {record.correctness:^8.1%} | {record.completeness:^8.1%} | {record.coherence:^8.1%} | {record.overall:^8.1%}")
        else:
            formatter.print_warning(f"没有 {model} 的历史数据")
    else:
        # 显示所有模型
        models = storage.get_all_models()
        if models:
            formatter.print_header("已测试的模型列表")
            for m in models:
                print(f"  - {m}")
        else:
            formatter.print_warning("没有历史数据")


async def run_async(args: argparse.Namespace, config: Config):
    """异步运行测试"""
    formatter = ResultFormatter()
    runner = BenchmarkRunner(config)

    # 确定要测试的提供商和模型
    providers = [args.provider] if args.provider else None
    models = None

    if args.model:
        if args.provider:
            models = {args.provider: [args.model]}
        else:
            # 如果只指定模型，需要查找属于哪个提供商
            for provider, model_list in config.models.items():
                for m in model_list:
                    if m.api_name == args.model or m.name == args.model:
                        models = {provider: [m.api_name]}
                        break
                if models:
                    break

    # 确定要测试的prompt
    prompts = [args.prompt] if args.prompt else None

    # 运行测试
    formatter.print_header("AI Token Speed Benchmark")
    formatter.print_info("开始测试...")

    try:
        results = await runner.run_full_benchmark(
            providers=providers,
            models=models,
            prompts=prompts
        )

        if results:
            runner.print_summary(results)
        else:
            formatter.print_warning("没有完成任何测试")

    except KeyboardInterrupt:
        formatter.print_warning("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        formatter.print_error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def run_quick_test(config: Config, provider: Optional[str] = None, model: Optional[str] = None):
    """快速测试模式"""
    formatter = ResultFormatter()
    runner = BenchmarkRunner(config)

    # 快速模式只测试 simple_code，迭代1次
    original_iterations = config.test_settings.iterations
    config.test_settings.iterations = 1

    formatter.print_header("Quick Benchmark")
    formatter.print_info("Testing simple code generation speed...\n")

    providers = [provider] if provider else None
    models = None

    if model:
        if provider:
            models = {provider: [model]}
        else:
            for p, model_list in config.models.items():
                for m in model_list:
                    if m.api_name == model or m.name == model:
                        models = {p: [m.api_name]}
                        break
                if models:
                    break

    try:
        results = await runner.run_full_benchmark(
            providers=providers,
            models=models,
            prompts=["simple_code"]
        )

        if results:
            # 简洁输出
            print("\n" + "="*60)
            print("QUICK TEST RESULTS")
            print("="*60)
            for key, result_list in results.items():
                if result_list:
                    r = result_list[0]
                    print(f"\n{r.provider} - {r.model}")
                    print(f"  TTFT: {r.ttft_ms:.0f}ms")
                    print(f"  Speed: {r.tokens_per_second:.1f} tokens/s")
                    print(f"  Tokens: {r.total_tokens}")
            print("\n" + "="*60)
        else:
            formatter.print_warning("No tests completed")

    except KeyboardInterrupt:
        formatter.print_warning("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        formatter.print_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        config.test_settings.iterations = original_iterations


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()

    # 加载配置
    config = Config.from_yaml(args.config)

    # 覆盖配置中的设置
    if args.iterations:
        config.test_settings.iterations = args.iterations
    if args.max_tokens:
        config.test_settings.max_tokens = args.max_tokens
    if args.timeout:
        config.test_settings.timeout = args.timeout

    # 处理列表命令
    if args.list_models:
        list_models(config)
        return

    if args.list_prompts:
        list_prompts()
        return

    # 质量评估相关命令
    if args.compare_quality:
        asyncio.run(run_quality_comparison(args, config))
        return

    if args.detect_degradation:
        run_degradation_detection(args)
        return

    if args.quality_history:
        show_quality_history(args)
        return

    # 检查API密钥
    formatter = ResultFormatter()
    providers_to_check = [args.provider] if args.provider else config.get_all_providers()

    has_api_key = False
    for provider in providers_to_check:
        if config.get_api_key(provider):
            has_api_key = True
        else:
            env_var = "ANTHROPIC_API_KEY" if "anthropic" in provider else (
                "DASHSCOPE_API_KEY" if provider == "bailian" else "ZHIPUAI_API_KEY"
            )
            formatter.print_warning(
                f"未配置 {provider} 的API密钥，请设置环境变量 {env_var}"
            )

    if not has_api_key:
        formatter.print_error("未配置任何API密钥，无法运行测试")
        sys.exit(1)

    # 运行测试
    if args.quick:
        asyncio.run(run_quick_test(config, args.provider, args.model))
    else:
        asyncio.run(run_async(args, config))


if __name__ == "__main__":
    main()