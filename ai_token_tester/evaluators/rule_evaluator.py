"""规则评估器 - 通过规则验证评估回答质量"""

import re
import subprocess
import sys
from typing import List, Optional

from .base import QualityEvaluator, QualityScore


class RuleEvaluator(QualityEvaluator):
    """规则评估器 - 使用关键词匹配、答案验证、代码执行等方式评估"""

    def __init__(self):
        self.name = "RuleEvaluator"

    async def evaluate(
        self,
        prompt: str,
        response: str,
        expected_keywords: Optional[List[str]] = None,
        expected_answer: Optional[str] = None,
    ) -> QualityScore:
        """使用规则评估回答质量"""
        score = QualityScore()

        # 1. 关键词匹配评估
        if expected_keywords:
            score.correctness = self._evaluate_keywords(response, expected_keywords)
            score.completeness = self._evaluate_completeness(response, expected_keywords)
        else:
            score.correctness = 0.5  # 无关键词要求，默认0.5
            score.completeness = 0.5

        # 2. 答案匹配评估
        if expected_answer:
            answer_score = self._evaluate_answer(response, expected_answer)
            score.correctness = max(score.correctness, answer_score)

        # 3. 连贯性评估
        score.coherence = self._evaluate_coherence(response)

        # 4. 计算综合得分
        score.overall = self.calculate_overall(score)
        score.details = self._generate_details(score, expected_keywords, expected_answer)

        return score

    def _evaluate_keywords(
        self, response: str, expected_keywords: List[str]
    ) -> float:
        """评估关键词匹配度"""
        if not expected_keywords:
            return 0.5

        response_lower = response.lower()
        matched = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
        return min(matched / len(expected_keywords), 1.0)

    def _evaluate_completeness(
        self, response: str, expected_keywords: List[str]
    ) -> float:
        """评估回答完整性 - 基于长度和结构"""
        if not expected_keywords:
            # 无关键词要求，基于基本完整性检查
            return self._basic_completeness(response)

        # 检查回答长度是否合理（不能太短）
        min_length = 50  # 至少50个字符
        if len(response) < min_length:
            return len(response) / min_length

        # 检查是否包含足够内容
        keyword_score = self._evaluate_keywords(response, expected_keywords)
        length_score = min(len(response) / 200, 1.0)  # 200字符为满分

        return (keyword_score * 0.7 + length_score * 0.3)

    def _basic_completeness(self, response: str) -> float:
        """基础完整性检查"""
        if len(response) < 20:
            return 0.2
        elif len(response) < 50:
            return 0.5
        elif len(response) < 100:
            return 0.7
        else:
            return 0.9

    def _evaluate_answer(self, response: str, expected_answer: str) -> float:
        """评估答案匹配度"""
        # 简化的答案匹配 - 检查回答中是否包含答案的关键数字/内容
        expected_lower = expected_answer.lower()

        # 提取答案中的数字
        expected_numbers = re.findall(r'[\d.-]+', expected_answer)
        if expected_numbers:
            # 检查是否包含答案中的数字
            response_numbers = re.findall(r'[\d.-]+', response)
            matched = sum(1 for num in expected_numbers if num in response_numbers)
            return min(matched / len(expected_numbers), 1.0)

        # 非数字答案，检查关键词
        keywords = expected_answer.split()
        matched = sum(1 for kw in keywords if kw.lower() in response.lower())
        return min(matched / len(keywords), 1.0) if keywords else 0.5

    def _evaluate_coherence(self, response: str) -> float:
        """评估回答连贯性"""
        if not response:
            return 0.0

        # 检查基本连贯性指标
        issues = 0

        # 1. 检查是否过短
        if len(response) < 30:
            issues += 1

        # 2. 检查是否有完整句子（包含标点）
        sentences = re.split(r'[。！？.!?]', response)
        valid_sentences = [s.strip() for s in sentences if s.strip()]
        if len(valid_sentences) < 1:
            issues += 1

        # 3. 检查是否有乱码或无意义字符
        if re.search(r'[{}\[\]]{10,}', response):
            issues += 1

        # 基础分数1.0，每发现一个问题扣0.3
        return max(1.0 - issues * 0.3, 0.1)

    def _generate_details(
        self,
        score: QualityScore,
        expected_keywords: Optional[List[str]] = None,
        expected_answer: Optional[str] = None,
    ) -> str:
        """生成评估详情"""
        details = []
        details.append(f"正确性: {score.correctness:.1%}")
        details.append(f"完整性: {score.completeness:.1%}")
        details.append(f"连贯性: {score.coherence:.1%}")
        details.append(f"综合: {score.overall:.1%}")

        if expected_keywords:
            details.append(f"期望关键词: {', '.join(expected_keywords[:3])}...")

        return " | ".join(details)


class CodeEvaluator(RuleEvaluator):
    """代码专用评估器"""

    async def evaluate(
        self,
        prompt: str,
        response: str,
        expected_keywords: Optional[List[str]] = None,
        expected_answer: Optional[str] = None,
    ) -> QualityScore:
        """评估代码质量"""
        score = await super().evaluate(
            prompt, response, expected_keywords, expected_answer
        )

        # 代码效率评估
        score.efficiency = self._evaluate_code_efficiency(response)

        # 代码可执行性检查（可选）
        if "def " in response or "function" in response.lower():
            score.details += f" | 效率: {score.efficiency:.1%}"

        return score

    def _evaluate_code_efficiency(self, response: str) -> float:
        """评估代码效率 - 检查是否包含常见的优化模式"""
        efficiency_indicators = [
            "O(n)",  # 时间复杂度提及
            "optim",  # optimization
            "memo",
            "cache",
            "lru_cache",
            "yield",
            "generator",
        ]

        response_lower = response.lower()
        matches = sum(1 for ind in efficiency_indicators if ind in response_lower)

        # 基础分数0.5，每发现一个优化指标加0.1
        return min(0.5 + matches * 0.1, 1.0)