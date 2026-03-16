# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Token Speed Tester - A Python CLI tool for measuring token output speed (TTFT and throughput) of AI models across multiple platforms (Bailian, Volcengine, Zhipu). Designed for AI CLI tool usage scenarios.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Quick test (recommended for rapid iteration)
python -m ai_token_tester --quick

# Quick test specific model
python -m ai_token_tester --quick -m qwen3.5-plus

# Full test with 3 iterations
python -m ai_token_tester

# Test specific provider
python -m ai_token_tester --provider volcengine

# List available models/prompts
python -m ai_token_tester --list-models
python -m ai_token_tester --list-prompts
```

## Architecture

```
ai_token_tester/
├── cli.py              # Entry point, argument parsing, quick test mode
├── config.py           # Config loading from YAML + .env files
├── models/
│   ├── base.py         # AIProvider abstract base class
│   ├── anthropic_compat.py  # Anthropic-compatible API (Bailian, Volcengine)
│   ├── bailian.py      # DashScope native API
│   └── zhipu.py        # Zhipu AI native API
├── testers/
│   └── benchmark.py    # BenchmarkRunner orchestrates all tests
├── prompts/
│   └── test_prompts.py # TEST_PROMPTS dict with PromptSet dataclasses
└── utils/
    ├── formatter.py    # Rich-based CLI output, TestResult dataclass
    └── token_counter.py # Tiktoken-based token counting
```

### Key Patterns

**Adding a new AI provider:**
1. Create `models/new_provider.py` inheriting from `AIProvider`
2. Implement `stream_generate()` (async iterator yielding `StreamChunk`) and `count_tokens()`
3. Register in `benchmark.py` `get_provider()` method
4. Add API key/env var to `.env.example`, `config.py` `_from_env()`, and `config.yaml`

**Provider selection logic:**
- `anthropic`, `anthropic_lite`, `volcengine` all use `AnthropicCompatibleProvider`
- Provider names map to API keys in config (e.g., `volcengine` → `VOLCENGINE_API_KEY`)

**Config precedence:** `.env` file → environment variables → `config.yaml`

**Test flow:**
1. `BenchmarkRunner.run_full_benchmark()` iterates providers/models/prompts
2. `run_single_test()` measures TTFT and throughput via streaming
3. Results aggregated and formatted via `ResultFormatter`

## Configuration

API keys stored in `.env` (gitignored). Copy `.env.example` to start. Models enabled/disabled in `config.yaml`.