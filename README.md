# AI Token Speed Tester

一个用于测试 AI 模型 token 输出速度的 Python 命令行工具，支持百炼（阿里云）、火山引擎和智普 AI 平台，特别针对 AI CLI 工具使用场景设计。

## 功能特性

- ✅ 支持 **百炼 Anthropic 兼容接口** (qwen3.5-plus, MiniMax-M2.5, glm-4.7, glm-5 等)
- ✅ 支持 **火山引擎 Anthropic 兼容接口** (MiniMax-M2.5, GLM-4.7, Kimi-K2.5 等)
- ✅ 支持 **百炼原生接口** (qwen-turbo, qwen-plus, qwen-max 等)
- ✅ 支持 **智普 AI** (glm-4-flash, glm-4, glm-4-plus 等)
- ✅ 测试 **TTFT (首Token延迟)**
- ✅ 测试 **吞吐量 (tokens/s)**
- ✅ **质量评估** - 评估模型输出的正确性、完整性、连贯性
- ✅ **降智检测** - 持续监控模型质量，检测性能下降
- ✅ **快速测试模式** (`--quick`)，秒级出结果
- ✅ **多次测试取平均**，减少误差
- ✅ **标准测试集**，确保可比性
- ✅ 美观的 **命令行输出**

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API 密钥：

```env
# 百炼 Anthropic 兼容接口
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic

# 火山引擎 Anthropic 兼容接口
VOLCENGINE_API_KEY=your-api-key-here
VOLCENGINE_BASE_URL=https://ark.cn-beijing.volces.com/api/coding

# 或者使用百炼原生接口
DASHSCOPE_API_KEY=your-api-key-here

# 或者使用智普 AI
ZHIPUAI_API_KEY=your-api-key-here
```

### 3. 运行测试

```bash
# 快速测试（推荐首选）- 只测简单代码生成，1次迭代
python -m ai_token_tester --quick

# 快速测试特定模型
python -m ai_token_tester --quick -m qwen3.5-plus

# 完整测试所有启用的模型
python -m ai_token_tester

# 测试特定平台
python -m ai_token_tester --provider volcengine

# 测试特定模型
python -m ai_token_tester --model qwen3.5-plus

# 指定测试次数
python -m ai_token_tester --iterations 5

# 测试特定 prompt
python -m ai_token_tester --prompt simple_code
```

## 命令行参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--quick` | `-q` | **快速测试模式**：只测简单代码生成，迭代1次 |
| `--provider` | `-p` | 指定测试的提供商 (anthropic/volcengine/bailian/zhipu) |
| `--model` | `-m` | 指定测试的模型名称 |
| `--prompt` | | 指定测试的 prompt |
| `--iterations` | `-i` | 每个测试重复次数 (默认: 3) |
| `--max-tokens` | | 最大输出 token 数 (默认: 1024) |
| `--timeout` | | 单次请求超时时间/秒 (默认: 60) |
| `--config` | `-c` | 配置文件路径 |
| `--list-models` | | 列出所有可用模型 |
| `--list-prompts` | | 列出所有测试 prompt |
| `--compare-quality` | | 运行质量对比测试 |
| `--detect-degradation` | | 运行降智检测 |
| `--quality-history` | | 查看质量历史 |
| `--model-quality` | | 指定查看历史的模型 |
| `--eval-prompt` | | 指定质量评估的 prompt |

## 测试用例

工具内置 8 个针对 AI CLI 场景设计的测试用例：

| 名称 | 说明 | 预期 Tokens |
|------|------|-------------|
| simple_code | 简单代码生成 | 200 |
| code_explain | 代码解释 | 150 |
| complex_code | 复杂代码生成 | 500 |
| refactor | 代码重构 | 150 |
| bug_fix | Bug 修复 | 200 |
| algorithm | 算法实现 | 300 |
| code_review | 代码审查 | 250 |
| quick_answer | 快速问答 | 50 |

## 质量评估

工具支持评估模型输出的质量，通过规则验证（关键词匹配、答案验证、代码执行）来判断模型回答的正确性。

### 质量评估命令

```bash
# 运行质量对比测试
python -m ai_token_tester --compare-quality

# 测试特定平台
python -m ai_token_tester --compare-quality --provider volcengine

# 测试特定模型
python -m ai_token_tester --compare-quality --model qwen3.5-plus

# 指定评估用例
python -m ai_token_tester --compare-quality --eval-prompt math_quadratic
```

### 质量评估用例

| 名称 | 说明 | 评估方式 |
|------|------|----------|
| code_quicksort | 快速排序实现 | 关键词检查 |
| code_binary_search | 二分查找实现 | 关键词检查 |
| fix_division_by_zero | 修复除零错误 | 关键词检查 |
| fix_index_error | 修复索引错误 | 关键词检查 |
| math_quadratic | 一元二次方程 | 答案验证 |
| math_linear_equation | 一元一次方程 | 答案验证 |
| logic_transitive | 传递关系推理 | 关键词检查 |
| logic_syllogism | 三段论推理 | 关键词检查 |
| review_loop | 循环优化建议 | 关键词检查 |
| review_recursion | 递归审查 | 关键词检查 |

## 降智检测

持续监控模型质量，检测模型是否出现"降智"现象。

### 降智检测命令

```bash
# 运行降智检测
python -m ai_token_tester --detect-degradation

# 查看特定模型历史
python -m ai_token_tester --quality-history --model-quality "Doubao-Seed-2.0-pro"

# 查看所有历史模型
python -m ai_token_tester --quality-history
```

### 检测逻辑

- **滑动窗口对比**: 比较最近7次平均分与历史基准
- **阈值告警**: 下降超过15%触发警告，25%触发严重告警
- **数据存储**: 历史数据保存在 `~/.ai_token_tester/quality_history.db`

### 输出示例

```
+----------+
| Degradation Detection |
+----------+

Analyzing historical data...

============================================================
! DEGRADATION ALERT
============================================================

[WARNING] qwen3.5-plus
   Metric: overall
   Current: 0.65 -> Baseline: 0.85
   Drop: 23.5%

============================================================
```

## 配置文件

`config.yaml` 支持以下配置：

```yaml
api_keys:
  anthropic: "${ANTHROPIC_API_KEY}"
  volcengine: "${VOLCENGINE_API_KEY}"
  bailian: "${DASHSCOPE_API_KEY}"
  zhipu: "${ZHIPUAI_API_KEY}"

base_urls:
  anthropic: "${ANTHROPIC_BASE_URL}"
  volcengine: "${VOLCENGINE_BASE_URL}"
  bailian: "${DASHSCOPE_BASE_URL}"
  zhipu: "${ZHIPUAI_BASE_URL}"

models:
  anthropic:
    - name: "qwen3.5-plus"
      api_name: "qwen3.5-plus"
      enabled: true
    - name: "MiniMax-M2.5"
      api_name: "MiniMax-M2.5"
      enabled: true

  volcengine:
    - name: "MiniMax-M2.5"
      api_name: "MiniMax-M2.5"
      enabled: true
    - name: "GLM-4.7"
      api_name: "GLM-4.7"
      enabled: true
    - name: "Kimi-K2.5"
      api_name: "Kimi-K2.5"
      enabled: true

test_settings:
  iterations: 3
  timeout: 120
  max_tokens: 1024
```

## 项目结构

```
AICheck/
├── ai_token_tester/
│   ├── __init__.py
│   ├── __main__.py          # 入口点
│   ├── cli.py               # CLI 参数解析
│   ├── config.py            # 配置管理
│   ├── models/
│   │   ├── base.py          # AI 提供商抽象基类
│   │   ├── bailian.py       # 百炼原生接口
│   │   ├── zhipu.py         # 智普 AI 接口
│   │   └── anthropic_compat.py  # Anthropic 兼容接口
│   ├── testers/
│   │   ├── benchmark.py     # 基准测试编排
│   │   ├── quality_runner.py # 质量评估运行器
│   │   ├── ttft_tester.py   # TTFT 测试
│   │   └── throughput_tester.py
│   ├── prompts/
│   │   ├── test_prompts.py  # 速度测试 Prompt 集
│   │   └── eval_prompts.py  # 质量评估 Prompt 集
│   ├── evaluators/          # 质量评估器
│   │   ├── base.py          # 评估器基类
│   │   └── rule_evaluator.py # 规则评估器
│   ├── storage/             # 数据存储
│   │   └── history.py       # SQLite 历史存储
│   ├── monitors/            # 监控模块
│   │   └── detector.py      # 降智检测器
│   └── utils/
│       ├── formatter.py     # 输出格式化
│       └── token_counter.py # Token 计数
├── config.yaml              # 配置文件
├── .env                     # 环境变量 (不提交)
├── .env.example             # 环境变量模板
├── requirements.txt
├── benchmark_report.md      # 测试报告
└── README.md
```

## 测试报告示例

### 快速测试模式 (`--quick`)

```
+-----------------+
| Quick Benchmark |
+-----------------+

Testing simple code generation speed...

============================================================
QUICK TEST RESULTS
============================================================

百炼(Anthropic兼容) - qwen3.5-plus
  TTFT: 15228ms
  Speed: 59.8 tokens/s
  Tokens: 910

火山引擎(Anthropic兼容) - Kimi-K2.5
  TTFT: 92146ms
  Speed: 13.0 tokens/s
  Tokens: 1194

============================================================
```

### 完整测试报告

```
                 百炼(Anthropic兼容) - qwen3.5-plus
+-------------------------------------------------------------------+
| 测试用例        |   TTFT(ms) |   Tokens |   Time(ms) |   Tokens/s |
|-----------------+------------+----------+------------+------------|
| 简单代码生成    |    17012.3 |     1020 |    17012.7 |       59.8 |
| 代码解释        |     9329.4 |      463 |     9329.6 |       49.6 |
| 复杂代码生成    |    17449.7 |      968 |    17450.1 |       55.7 |
| 代码重构        |     8638.9 |      458 |     8639.3 |       53.2 |
| Bug修复         |    13138.1 |      791 |    13138.4 |       60.1 |
| 算法实现        |    17784.4 |     1139 |    17784.8 |       64.6 |
| 代码审查        |    20955.9 |     1112 |    20956.3 |       53.1 |
| 快速问答        |    18931.4 |       43 |    18931.4 |        2.3 |
|-----------------+------------+----------+------------+------------|
| AVERAGE         |    15405.0 |          |            |       49.8 |
+-------------------------------------------------------------------+
```

## 测试结果对比

### 全平台模型性能排名（快速测试）

| 排名 | 平台 | 模型 | TTFT | 吞吐量 |
|:----:|------|------|------|--------|
| 🥇 | 百炼 | qwen3.5-plus | ~16秒 | **50-60 tokens/s** |
| 🥈 | 百炼 | MiniMax-M2.5 | 29秒 | **45.9 tokens/s** |
| 🥉 | 百炼 | glm-4.7 | 35秒 | 20.5 tokens/s |
| 4 | 百炼 | glm-5 | ~50秒 | 16 tokens/s |
| 5 | 火山引擎 | Kimi-K2.5 | 92秒 | 13.0 tokens/s |
| 6 | 火山引擎 | MiniMax-M2.5 | 106秒 | 11.8 tokens/s |
| 7 | 火山引擎 | GLM-4.7 | 98秒 | 10.1 tokens/s |

### 关键发现

1. **平台差异显著**：同一模型在不同平台性能差距巨大
   - MiniMax-M2.5: 百炼 **45.9** vs 火山引擎 11.8 tokens/s（快 **4倍**）
   - GLM-4.7: 百炼 **20.5** vs 火山引擎 10.1 tokens/s（快 **2倍**）

2. **性价比推荐**：
   - **速度优先**: 百炼 + qwen3.5-plus（最快）
   - **性价比**: 百炼 Lite 套餐（性能甚至略优于 Pro）
   - **避免**: 火山引擎（同模型速度明显较慢）

## 扩展开发

### 添加新的 AI 提供商

1. 在 `ai_token_tester/models/` 下创建新文件
2. 继承 `AIProvider` 基类
3. 实现 `stream_generate` 和 `count_tokens` 方法
4. 在 `benchmark.py` 中注册新提供商

```python
from .base import AIProvider, StreamChunk

class NewProvider(AIProvider):
    @property
    def provider_name(self) -> str:
        return "新提供商"

    async def stream_generate(self, prompt: str, max_tokens: int = 1024):
        # 实现流式生成
        pass

    async def count_tokens(self, text: str) -> int:
        # 实现 token 计数
        pass
```

### 添加新的测试用例

在 `ai_token_tester/prompts/test_prompts.py` 中添加：

```python
TEST_PROMPTS["new_test"] = PromptSet(
    key="new_test",
    name="新测试用例",
    prompt="你的测试 prompt",
    expected_tokens=200,
    category="code_generation"
)
```

### 添加新的质量评估用例

在 `ai_token_tester/prompts/eval_prompts.py` 中添加：

```python
EVAL_PROMPTS["new_eval"] = EvalPrompt(
    key="new_eval",
    name="新评估用例",
    prompt="你的评估 prompt",
    category="logic_puzzle",
    expected_keywords=["keyword1", "keyword2"],
    expected_answer="标准答案",
)
```

## 依赖说明

| 包名 | 用途 |
|------|------|
| anthropic | Anthropic SDK (兼容接口) |
| dashscope | 百炼 SDK |
| zhipuai | 智普 AI SDK |
| tiktoken | Token 计数 |
| rich | 命令行美化输出 |
| pyyaml | 配置文件解析 |
| python-dotenv | 环境变量加载 |

## 注意事项

1. **API 密钥安全**: 不要将 `.env` 文件提交到版本控制
2. **速率限制**: 注意各平台的 API 调用频率限制
3. **网络延迟**: 测试结果受网络影响，建议多次测试取平均
4. **Token 计数**: 使用 tiktoken 估算，不同模型 tokenizer 可能略有差异

## License

MIT License