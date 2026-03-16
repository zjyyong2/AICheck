"""降智检测器 - 检测模型性能下降并发送告警"""

import sys
from dataclasses import dataclass
from typing import List, Optional

from ..storage.history import HistoryStorage


@dataclass
class DegradationAlert:
    """降智告警"""
    model: str
    metric: str
    current_score: float
    baseline_score: float
    drop_percentage: float
    severity: str  # "warning", "critical"
    message: str


class DegradationDetector:
    """降智检测器"""

    def __init__(
        self,
        storage: HistoryStorage,
        window_size: int = 7,
        drop_threshold: float = 0.15,
        trend_threshold: int = 3,
    ):
        """
        初始化降智检测器

        Args:
            storage: 历史数据存储
            window_size: 滑动窗口大小
            drop_threshold: 下降阈值（15%触发告警）
            trend_threshold: 连续下降次数阈值
        """
        self.storage = storage
        self.window_size = window_size
        self.drop_threshold = drop_threshold
        self.trend_threshold = trend_threshold

    def detect(self, model: str) -> List[DegradationAlert]:
        """
        检测模型是否降智

        Args:
            model: 模型名称

        Returns:
            List[DegradationAlert]: 告警列表
        """
        alerts = []
        metrics = ["overall", "correctness", "completeness", "coherence"]

        for metric in metrics:
            alert = self._detect_metric_degradation(model, metric)
            if alert:
                alerts.append(alert)
                # 保存告警到数据库
                self.storage.save_alert(
                    model=alert.model,
                    metric=alert.metric,
                    current_score=alert.current_score,
                    baseline_score=alert.baseline_score,
                    drop_percentage=alert.drop_percentage,
                    severity=alert.severity,
                    message=alert.message,
                )

        return alerts

    def _detect_metric_degradation(
        self, model: str, metric: str
    ) -> Optional[DegradationAlert]:
        """检测单个指标的降智"""
        # 1. 获取历史数据
        history = self.storage.get_history(model, days=30)
        if len(history) < self.window_size:
            return None  # 数据不足，跳过

        # 获取最近N次测试的平均分
        recent_scores = [
            getattr(r, metric) for r in history[: self.window_size]
        ]
        current_avg = sum(recent_scores) / len(recent_scores)

        # 2. 获取基准分数（历史平均或指定基准）
        baseline = self.storage.get_baseline(model, metric)
        if baseline is None:
            return None

        # 3. 计算下降百分比
        if baseline == 0:
            return None

        drop_percentage = (baseline - current_avg) / baseline

        # 4. 判断是否触发告警
        if drop_percentage >= self.drop_threshold:
            severity = "critical" if drop_threshold >= 0.25 else "warning"
            message = (
                f"[{model}] {metric} 指标下降 {drop_percentage:.1%}，"
                f"当前: {current_avg:.2f}, 基准: {baseline:.2f}"
            )

            return DegradationAlert(
                model=model,
                metric=metric,
                current_score=current_avg,
                baseline_score=baseline,
                drop_percentage=drop_percentage,
                severity=severity,
                message=message,
            )

        return None

    def print_alerts(self, alerts: List[DegradationAlert]):
        """打印告警到控制台"""
        if not alerts:
            print("\n[INFO] No degradation detected")
            return

        print("\n" + "=" * 60)
        print("! DEGRADATION ALERT")
        print("=" * 60)

        for alert in alerts:
            icon = "[CRITICAL]" if alert.severity == "critical" else "[WARNING]"
            print(f"\n{icon} {alert.model}")
            print(f"   Metric: {alert.metric}")
            print(f"   Current: {alert.current_score:.2f} -> Baseline: {alert.baseline_score:.2f}")
            print(f"   Drop: {alert.drop_percentage:.1%}")

        print("\n" + "=" * 60)


def run_detection(
    models: Optional[List[str]] = None,
    window_size: int = 7,
    drop_threshold: float = 0.15,
    trend_threshold: int = 3,
) -> List[DegradationAlert]:
    """
    运行降智检测

    Args:
        models: 要检测的模型列表，None表示检测所有模型
        window_size: 滑动窗口大小
        drop_threshold: 下降阈值
        trend_threshold: 连续下降次数阈值

    Returns:
        List[DegradationAlert]: 告警列表
    """
    storage = HistoryStorage()
    detector = DegradationDetector(
        storage=storage,
        window_size=window_size,
        drop_threshold=drop_threshold,
        trend_threshold=trend_threshold,
    )

    # 确定要检测的模型
    if models is None:
        models = storage.get_all_models()

    all_alerts = []
    for model in models:
        alerts = detector.detect(model)
        all_alerts.extend(alerts)

    # 打印告警
    detector.print_alerts(all_alerts)

    return all_alerts