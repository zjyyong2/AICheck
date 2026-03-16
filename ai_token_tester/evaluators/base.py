"""评估器基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class QualityScore:
    """质量评分"""
    correctness: float = 0.0      # 正确性 (0-1)
    completeness: float = 0.0      # 完整性 (0-1)
    coherence: float = 0.0         # 连贯性 (0-1)
    efficiency: float = 0.0        # 效率 (0-1, 仅代码类)
    overall: float = 0.0           # 综合得分 (0-1)

    # 附加信息
    details: str = ""               # 评估详情
    errors: List[str] = None        # 发现的问题

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> dict:
        return {
            "correctness": self.correctness,
            "completeness": self.completeness,
            "coherence": self.coherence,
            "efficiency": self.efficiency,
            "overall": self.overall,
            "details": self.details,
            "errors": self.errors,
        }


class QualityEvaluator(ABC):
    """质量评估器基类"""

    @abstractmethod
    async def evaluate(
        self,
        prompt: str,
        response: str,
        expected_keywords: Optional[List[str]] = None,
        expected_answer: Optional[str] = None,
    ) -> QualityScore:
        """
        评估回答质量

        Args:
            prompt: 输入的prompt
            response: 模型回答
            expected_keywords: 期望包含的关键词
            expected_answer: 期望的标准答案

        Returns:
            QualityScore: 质量评分
        """
        pass

    def calculate_overall(self, score: QualityScore) -> float:
        """计算综合得分"""
        # 正确性权重最高，其次是完整性
        weights = {
            "correctness": 0.5,
            "completeness": 0.3,
            "coherence": 0.2,
        }
        return (
            score.correctness * weights["correctness"]
            + score.completeness * weights["completeness"]
            + score.coherence * weights["coherence"]
        )