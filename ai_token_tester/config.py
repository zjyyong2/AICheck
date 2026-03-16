"""配置管理模块"""

import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    api_name: str
    enabled: bool = True


@dataclass
class TestSettings:
    """测试设置"""
    iterations: int = 3
    timeout: int = 60
    max_tokens: int = 1024


@dataclass
class Config:
    """应用配置"""
    api_keys: Dict[str, str] = field(default_factory=dict)
    base_urls: Dict[str, str] = field(default_factory=dict)
    models: Dict[str, List[ModelConfig]] = field(default_factory=dict)
    test_settings: TestSettings = field(default_factory=TestSettings)

    @classmethod
    def from_yaml(cls, config_path: Optional[str] = None) -> "Config":
        """从YAML文件加载配置"""
        # 先加载 .env 文件
        cls._load_env_file()

        if config_path is None:
            # 默认查找路径
            possible_paths = [
                Path("config.yaml"),
                Path(__file__).parent.parent / "config.yaml",
                Path.home() / ".ai_token_tester" / "config.yaml",
            ]
            for p in possible_paths:
                if p.exists():
                    config_path = str(p)
                    break

        if config_path is None or not Path(config_path).exists():
            # 没有配置文件时，从环境变量直接读取
            return cls._from_env()

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls._parse_config(data)

    @classmethod
    def _load_env_file(cls):
        """加载 .env 文件"""
        if DOTENV_AVAILABLE:
            # 查找 .env 文件
            possible_paths = [
                Path(".env"),
                Path(__file__).parent.parent / ".env",
                Path.cwd() / ".env",
            ]
            for p in possible_paths:
                if p.exists():
                    load_dotenv(p)
                    break

    @classmethod
    def _from_env(cls) -> "Config":
        """从环境变量直接创建配置"""
        config = cls()

        # 百炼配置
        if os.environ.get("DASHSCOPE_API_KEY"):
            config.api_keys["bailian"] = os.environ["DASHSCOPE_API_KEY"]
        if os.environ.get("DASHSCOPE_BASE_URL"):
            config.base_urls["bailian"] = os.environ["DASHSCOPE_BASE_URL"]

        # 智普配置
        if os.environ.get("ZHIPUAI_API_KEY"):
            config.api_keys["zhipu"] = os.environ["ZHIPUAI_API_KEY"]
        if os.environ.get("ZHIPUAI_BASE_URL"):
            config.base_urls["zhipu"] = os.environ["ZHIPUAI_BASE_URL"]

        # Anthropic兼容接口配置
        if os.environ.get("ANTHROPIC_API_KEY"):
            config.api_keys["anthropic"] = os.environ["ANTHROPIC_API_KEY"]
        if os.environ.get("ANTHROPIC_BASE_URL"):
            config.base_urls["anthropic"] = os.environ["ANTHROPIC_BASE_URL"]

        # Anthropic兼容接口配置 (Lite套餐)
        if os.environ.get("ANTHROPIC_LITE_API_KEY"):
            config.api_keys["anthropic_lite"] = os.environ["ANTHROPIC_LITE_API_KEY"]
        if os.environ.get("ANTHROPIC_LITE_BASE_URL"):
            config.base_urls["anthropic_lite"] = os.environ["ANTHROPIC_LITE_BASE_URL"]

        # 火山引擎配置
        if os.environ.get("VOLCENGINE_API_KEY"):
            config.api_keys["volcengine"] = os.environ["VOLCENGINE_API_KEY"]
        if os.environ.get("VOLCENGINE_BASE_URL"):
            config.base_urls["volcengine"] = os.environ["VOLCENGINE_BASE_URL"]

        # 默认模型配置
        config.models = {
            "bailian": [
                ModelConfig("qwen-turbo", "qwen-turbo", True),
                ModelConfig("qwen-plus", "qwen-plus", True),
                ModelConfig("qwen-max", "qwen-max", True),
            ],
            "zhipu": [
                ModelConfig("glm-4-flash", "glm-4-flash", True),
                ModelConfig("glm-4", "glm-4", True),
                ModelConfig("glm-4-plus", "glm-4-plus", True),
            ],
            "anthropic": [
                ModelConfig("qwen3.5-plus", "qwen3.5-plus", True),
                ModelConfig("glm-5", "glm-5", True),
            ]
        }

        return config

    @classmethod
    def _parse_config(cls, data: dict) -> "Config":
        """解析配置数据"""
        config = cls()

        # 解析API密钥（支持环境变量）
        if "api_keys" in data:
            for provider, key in data["api_keys"].items():
                config.api_keys[provider] = cls._expand_env_var(key)

        # 解析Base URL（支持环境变量）
        if "base_urls" in data:
            for provider, url in data["base_urls"].items():
                config.base_urls[provider] = cls._expand_env_var(url)

        # 解析模型配置
        if "models" in data:
            for provider, models in data["models"].items():
                config.models[provider] = [
                    ModelConfig(**m) for m in models
                ]

        # 解析测试设置
        if "test_settings" in data:
            config.test_settings = TestSettings(**data["test_settings"])

        return config

    @staticmethod
    def _expand_env_var(value: str) -> str:
        """展开环境变量 ${VAR_NAME} 格式"""
        if not isinstance(value, str):
            return value

        pattern = r"\$\{([^}]+)\}"

        def replace(match):
            var_name = match.group(1)
            return os.environ.get(var_name, "")

        return re.sub(pattern, replace, value)

    def get_api_key(self, provider: str) -> Optional[str]:
        """获取指定提供商的API密钥"""
        return self.api_keys.get(provider)

    def get_base_url(self, provider: str) -> Optional[str]:
        """获取指定提供商的Base URL"""
        return self.base_urls.get(provider)

    def get_enabled_models(self, provider: str) -> List[ModelConfig]:
        """获取指定提供商启用的模型"""
        models = self.models.get(provider, [])
        return [m for m in models if m.enabled]

    def get_all_providers(self) -> List[str]:
        """获取所有配置的提供商"""
        return list(self.models.keys())