"""标准测试Prompt集 - 针对AI CLI工具场景"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PromptSet:
    """测试Prompt"""
    key: str
    name: str
    prompt: str
    expected_tokens: int
    category: str = "general"


# 针对AI CLI工具使用场景的测试Prompt集
TEST_PROMPTS: Dict[str, PromptSet] = {
    # === 简单任务 - 测试基础响应速度 ===
    "simple_code": PromptSet(
        key="simple_code",
        name="简单代码生成",
        prompt="用Python写一个计算斐波那契数列的函数",
        expected_tokens=200,
        category="code_generation"
    ),

    # === 代码理解 - 测试理解+生成能力 ===
    "code_explain": PromptSet(
        key="code_explain",
        name="代码解释",
        prompt="解释以下代码的作用：\n\ndef foo(x):\n    return [i*2 for i in x if i > 0]",
        expected_tokens=150,
        category="code_understanding"
    ),

    # === 复杂任务 - 测试长文本生成 ===
    "complex_code": PromptSet(
        key="complex_code",
        name="复杂代码生成",
        prompt="用Python实现一个简单的HTTP服务器，支持GET和POST请求，使用标准库",
        expected_tokens=500,
        category="code_generation"
    ),

    # === 代码重构 - 测试推理能力 ===
    "refactor": PromptSet(
        key="refactor",
        name="代码重构",
        prompt="重构以下代码，使其更Pythonic：\n\nfor i in range(len(lst)):\n    print(lst[i])",
        expected_tokens=150,
        category="code_modification"
    ),

    # === Bug修复 - 测试问题定位 ===
    "bug_fix": PromptSet(
        key="bug_fix",
        name="Bug修复",
        prompt="找出并修复以下代码的bug，解释问题原因：\n\ndef divide(a, b):\n    return a / b",
        expected_tokens=200,
        category="debugging"
    ),

    # === 算法实现 - 测试逻辑推理 ===
    "algorithm": PromptSet(
        key="algorithm",
        name="算法实现",
        prompt="实现一个二分查找算法，并解释其时间复杂度",
        expected_tokens=300,
        category="code_generation"
    ),

    # === 代码审查 - 测试分析能力 ===
    "code_review": PromptSet(
        key="code_review",
        name="代码审查",
        prompt="审查以下代码，指出潜在问题和改进建议：\n\ndef process_data(data):\n    result = []\n    for item in data:\n        result.append(str(item).upper())\n    return result",
        expected_tokens=250,
        category="code_understanding"
    ),

    # === 快速问答 - 测试首token延迟 ===
    "quick_answer": PromptSet(
        key="quick_answer",
        name="快速问答",
        prompt="什么是Python的GIL？用一句话回答",
        expected_tokens=50,
        category="qa"
    ),
}


def get_prompt_by_category(category: str) -> List[PromptSet]:
    """按类别获取测试Prompt"""
    return [p for p in TEST_PROMPTS.values() if p.category == category]


def get_all_categories() -> List[str]:
    """获取所有类别"""
    return list(set(p.category for p in TEST_PROMPTS.values()))


def get_prompt_keys() -> List[str]:
    """获取所有Prompt key"""
    return list(TEST_PROMPTS.keys())