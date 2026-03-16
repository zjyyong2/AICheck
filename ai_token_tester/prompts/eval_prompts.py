"""质量评估专用Prompt集 - 用于评估模型输出质量"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Callable


@dataclass
class EvalPrompt:
    """质量评估Prompt"""
    key: str
    name: str
    prompt: str
    category: str
    # 验证规则
    expected_keywords: Optional[List[str]] = None  # 期望包含的关键词
    expected_answer: Optional[str] = None  # 期望的标准答案（用于精确匹配）
    code_template: Optional[str] = None  # 代码模板（用于代码验证）
    validator: Optional[Callable] = None  # 自定义验证函数


# 质量评估Prompt集 - 使用规则评估
EVAL_PROMPTS: Dict[str, EvalPrompt] = {
    # === 编程实现类 ===
    "code_quicksort": EvalPrompt(
        key="code_quicksort",
        name="快速排序实现",
        prompt="用Python实现快速排序算法，要求原地排序。",
        category="code_implement",
        expected_keywords=["def quicksort", "pivot", "partition"],
    ),

    "code_binary_search": EvalPrompt(
        key="code_binary_search",
        name="二分查找实现",
        prompt="用Python实现二分查找算法，返回找到的索引或-1。",
        category="code_implement",
        expected_keywords=["def binary_search", "mid", "left", "right"],
    ),

    # === 代码修复类 ===
    "fix_division_by_zero": EvalPrompt(
        key="fix_division_by_zero",
        name="修复除零错误",
        prompt="修复以下代码的bug：\ndef divide(a, b):\n    return a / b",
        category="code_fix",
        expected_keywords=["if", "b == 0", "ZeroDivisionError", "return"],
    ),

    "fix_index_error": EvalPrompt(
        key="fix_index_error",
        name="修复索引错误",
        prompt="修复以下代码的bug：\ndef get_item(lst, idx):\n    return lst[idx]",
        category="code_fix",
        expected_keywords=["if", "idx", "len", "range", "IndexError"],
    ),

    # === 数学推理类 ===
    "math_quadratic": EvalPrompt(
        key="math_quadratic",
        name="一元二次方程",
        prompt="求方程 x^2 - 5x + 6 = 0 的两个根。",
        category="math_reasoning",
        expected_answer="x=2 或 x=3",  # 简化的答案匹配
        expected_keywords=["2", "3"],
    ),

    "math_linear_equation": EvalPrompt(
        key="math_linear_equation",
        name="一元一次方程",
        prompt="解方程：3x + 6 = 0，求x的值。",
        category="math_reasoning",
        expected_keywords=["-2", "x = -2"],
    ),

    # === 逻辑推理类 ===
    "logic_transitive": EvalPrompt(
        key="logic_transitive",
        name="传递关系推理",
        prompt="已知 A > B, B > C，请问 A 和 C 的大小关系是什么？",
        category="logic_puzzle",
        expected_keywords=["A > C", "大于", ">"],
    ),

    "logic_syllogism": EvalPrompt(
        key="logic_syllogism",
        name="三段论推理",
        prompt="所有猫都是哺乳动物，有些哺乳动物是黑色的。能推出什么结论？",
        category="logic_puzzle",
        expected_keywords=["有些猫是黑色的", "可能", "或许"],
    ),

    # === 代码审查类 ===
    "review_loop": EvalPrompt(
        key="review_loop",
        name="循环优化建议",
        prompt="审查以下代码，指出问题并提供改进建议：\nfor i in range(len(data)):\n    print(data[i])",
        category="code_review",
        expected_keywords=["enumerate", "改进", "优化", "更好"],
    ),

    "review_recursion": EvalPrompt(
        key="review_recursion",
        name="递归审查",
        prompt="审查以下代码的递归实现，有何问题？\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)",
        category="code_review",
        expected_keywords=["递归", "栈溢出", "效率", "优化", "memo"],
    ),
}


def get_eval_prompt(key: str) -> Optional[EvalPrompt]:
    """根据key获取评估Prompt"""
    return EVAL_PROMPTS.get(key)


def get_prompts_by_category(category: str) -> List[EvalPrompt]:
    """按类别获取评估Prompt"""
    return [p for p in EVAL_PROMPTS.values() if p.category == category]


def get_all_eval_categories() -> List[str]:
    """获取所有类别"""
    return list(set(p.category for p in EVAL_PROMPTS.values()))


def get_all_eval_keys() -> List[str]:
    """获取所有Prompt key"""
    return list(EVAL_PROMPTS.keys())