"""结果格式化工具"""

from dataclasses import dataclass
from typing import List, Optional
from statistics import mean

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


@dataclass
class TestResult:
    """单次测试结果"""
    model: str
    provider: str
    prompt_key: str
    prompt_name: str
    ttft_ms: float
    total_tokens: int
    total_time_ms: float
    tokens_per_second: float
    iteration: int = 1


@dataclass
class AggregatedResult:
    """聚合测试结果（多次测试的平均值）"""
    model: str
    provider: str
    prompt_key: str
    prompt_name: str
    avg_ttft_ms: float
    avg_tokens: float
    avg_time_ms: float
    avg_tokens_per_second: float
    min_ttft_ms: float
    max_ttft_ms: float
    iterations: int


class ResultFormatter:
    """结果格式化器"""

    def __init__(self):
        self.console = Console()

    def print_header(self, title: str = "AI Token Speed Benchmark"):
        """打印标题"""
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]{title}[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()

    def print_model_result(self, results: List[TestResult]):
        """打印单个模型的测试结果"""
        if not results:
            return

        # 按prompt分组
        prompt_groups = {}
        for r in results:
            if r.prompt_key not in prompt_groups:
                prompt_groups[r.prompt_key] = []
            prompt_groups[r.prompt_key].append(r)

        model_name = results[0].model
        provider_name = results[0].provider

        # 创建表格
        table = Table(
            title=f"[bold]{provider_name} - {model_name}[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )

        table.add_column("测试用例", style="cyan", width=15)
        table.add_column("TTFT(ms)", justify="right", width=10)
        table.add_column("Tokens", justify="right", width=8)
        table.add_column("Time(ms)", justify="right", width=10)
        table.add_column("Tokens/s", justify="right", width=10)

        all_ttft = []
        all_tps = []

        for prompt_key, prompt_results in prompt_groups.items():
            prompt_name = prompt_results[0].prompt_name

            # 计算平均值
            avg_ttft = mean(r.ttft_ms for r in prompt_results)
            avg_tokens = mean(r.total_tokens for r in prompt_results)
            avg_time = mean(r.total_time_ms for r in prompt_results)
            avg_tps = mean(r.tokens_per_second for r in prompt_results)

            all_ttft.append(avg_ttft)
            all_tps.append(avg_tps)

            table.add_row(
                prompt_name[:15],
                f"{avg_ttft:.1f}",
                f"{avg_tokens:.0f}",
                f"{avg_time:.1f}",
                f"{avg_tps:.1f}"
            )

        # 添加平均行
        table.add_section()
        table.add_row(
            "[bold]AVERAGE[/bold]",
            f"[bold]{mean(all_ttft):.1f}[/bold]",
            "",
            "",
            f"[bold]{mean(all_tps):.1f}[/bold]"
        )

        self.console.print(table)
        self.console.print()

    def print_comparison(self, all_results: dict):
        """打印多模型对比"""
        table = Table(
            title="[bold]模型对比[/bold]",
            show_header=True,
            header_style="bold magenta",
            border_style="green"
        )

        table.add_column("模型", style="cyan", width=20)
        table.add_column("提供商", width=8)
        table.add_column("平均TTFT(ms)", justify="right", width=12)
        table.add_column("平均Tokens/s", justify="right", width=12)

        for model_key, results in all_results.items():
            if not results:
                continue

            avg_ttft = mean(r.ttft_ms for r in results)
            avg_tps = mean(r.tokens_per_second for r in results)

            table.add_row(
                results[0].model,
                results[0].provider,
                f"{avg_ttft:.1f}",
                f"{avg_tps:.1f}"
            )

        self.console.print(table)

    def print_error(self, message: str):
        """打印错误信息"""
        self.console.print(f"[bold red]错误:[/bold red] {message}")

    def print_warning(self, message: str):
        """打印警告信息"""
        self.console.print(f"[bold yellow]警告:[/bold yellow] {message}")

    def print_success(self, message: str):
        """打印成功信息"""
        self.console.print(f"[bold green]{message}[/bold green]")

    def print_info(self, message: str):
        """打印信息"""
        self.console.print(f"[blue]{message}[/blue]")

    def print_running(self, model: str, prompt: str, iteration: int, total: int):
        """打印正在运行的信息"""
        self.console.print(
            f"[dim]测试中: {model} | {prompt} ({iteration}/{total})[/dim]"
        )

    def aggregate_results(self, results: List[TestResult]) -> List[AggregatedResult]:
        """聚合多次测试结果"""
        if not results:
            return []

        # 按 model + prompt_key 分组
        groups = {}
        for r in results:
            key = (r.model, r.prompt_key)
            if key not in groups:
                groups[key] = []
            groups[key].append(r)

        aggregated = []
        for (model, prompt_key), group_results in groups.items():
            ttfts = [r.ttft_ms for r in group_results]
            tokens = [r.total_tokens for r in group_results]
            times = [r.total_time_ms for r in group_results]
            tps = [r.tokens_per_second for r in group_results]

            aggregated.append(AggregatedResult(
                model=model,
                provider=group_results[0].provider,
                prompt_key=prompt_key,
                prompt_name=group_results[0].prompt_name,
                avg_ttft_ms=mean(ttfts),
                avg_tokens=mean(tokens),
                avg_time_ms=mean(times),
                avg_tokens_per_second=mean(tps),
                min_ttft_ms=min(ttfts),
                max_ttft_ms=max(ttfts),
                iterations=len(group_results)
            ))

        return aggregated