"""SentriKit_salesmaster.team_pkg.llm — LLM 集成模块

支持多 LLM 提供商：OpenAI GPT、DeepSeek、Claude、智谱 GLM、通义千问等。
"""

from __future__ import annotations

import os
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple


# ── LLM 提供商枚举 ────────────────────────────────────────

class LLMProvider(Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    ZHIPU = "zhipu"
    DASHSCOPE = "dashscope"  # 通义千问
    MOCK = "mock"           # 模拟模式（用于测试）


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str = "user"
    content: str = ""
    name: Optional[str] = None
    function_call: Optional[Dict] = None

    def to_dict(self) -> Dict:
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        return result

    @staticmethod
    def from_dict(data: Dict) -> "LLMMessage":
        return LLMMessage(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name"),
            function_call=data.get("function_call")
        )


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str = ""
    model: str = ""
    provider: str = ""
    usage: Dict = field(default_factory=dict)  # token 使用量
    finish_reason: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None

    @property
    def total_tokens(self) -> int:
        return self.usage.get("total_tokens", 0)

    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)

    @property
    def is_error(self) -> bool:
        return self.error is not None


@dataclass
class FunctionCall:
    """函数调用定义"""
    name: str = ""
    description: str = ""
    parameters: Dict = field(default_factory=dict)  # JSON Schema


@dataclass
class FunctionCallResult:
    """函数调用结果"""
    call_id: str = ""
    function_name: str = ""
    arguments: Dict = field(default_factory=dict)
    result: Any = None
    error: Optional[str] = None


# ── LLM 配置 ────────────────────────────────────────

class LLMConfig:
    """LLM 配置"""

    def __init__(self,
                 provider: str = "mock",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: str = "gpt-4",
                 temperature: float = 0.7,
                 max_tokens: int = 2000,
                 timeout: float = 60.0,
                 **kwargs):
        self.provider = provider
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra = kwargs

    @classmethod
    def from_env(cls, provider: str = "mock") -> "LLMConfig":
        """从环境变量创建配置"""
        return cls(provider=provider)

    @classmethod
    def openai(cls, api_key: Optional[str] = None, model: str = "gpt-4",
               **kwargs) -> "LLMConfig":
        """OpenAI 配置"""
        return cls(
            provider="openai",
            api_key=api_key,
            base_url="https://api.openai.com/v1",
            model=model,
            **kwargs
        )

    @classmethod
    def deepseek(cls, api_key: Optional[str] = None, model: str = "deepseek-chat",
                 **kwargs) -> "LLMConfig":
        """DeepSeek 配置"""
        return cls(
            provider="deepseek",
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            model=model,
            **kwargs
        )

    @classmethod
    def anthropic(cls, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229",
                  **kwargs) -> "LLMConfig":
        """Anthropic Claude 配置"""
        return cls(
            provider="anthropic",
            api_key=api_key,
            base_url="https://api.anthropic.com/v1",
            model=model,
            **kwargs
        )

    @classmethod
    def zhipu(cls, api_key: Optional[str] = None, model: str = "glm-4",
              **kwargs) -> "LLMConfig":
        """智谱 GLM 配置"""
        return cls(
            provider="zhipu",
            api_key=api_key,
            base_url="https://open.bigmodel.cn/api/paas/v4",
            model=model,
            **kwargs
        )

    @classmethod
    def dashscope(cls, api_key: Optional[str] = None, model: str = "qwen-turbo",
                  **kwargs) -> "LLMConfig":
        """通义千问配置"""
        return cls(
            provider="dashscope",
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/api/v1",
            model=model,
            **kwargs
        )

    @classmethod
    def mock(cls, **kwargs) -> "LLMConfig":
        """模拟模式配置（用于测试）"""
        return cls(provider="mock", model="mock", **kwargs)


# ── LLM 基类 ────────────────────────────────────────

class BaseLLM(ABC):
    """LLM 基类"""

    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """发送对话请求"""
        pass

    @abstractmethod
    def chat_stream(self, messages: List[LLMMessage],
                   callback: Optional[Callable[[str], None]] = None,
                   **kwargs) -> LLMResponse:
        """流式对话"""
        pass

    @abstractmethod
    def function_calling(self, messages: List[LLMMessage],
                        functions: List[FunctionCall],
                        **kwargs) -> Tuple[LLMResponse, Optional[FunctionCall]]:
        """函数调用"""
        pass


# ── Mock LLM（用于测试）───────────────────────────────────────

class MockLLM(BaseLLM):
    """模拟 LLM（用于开发和测试）"""

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._response_delay = 0.5  # 模拟延迟

    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """模拟对话"""
        start = time.time()

        # 模拟延迟
        time.sleep(self._response_delay)

        # 生成模拟响应
        last_message = messages[-1].content if messages else ""
        response_content = self._generate_mock_response(last_message, kwargs)

        return LLMResponse(
            content=response_content,
            model=self.config.model,
            provider=self.config.provider,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
            latency_ms=(time.time() - start) * 1000
        )

    def chat_stream(self, messages: List[LLMMessage],
                   callback: Optional[Callable[[str], None]] = None,
                   **kwargs) -> LLMResponse:
        """模拟流式对话"""
        start = time.time()

        last_message = messages[-1].content if messages else ""
        response_content = self._generate_mock_response(last_message, kwargs)

        # 模拟流式输出
        words = response_content.split()
        for i, word in enumerate(words):
            if callback:
                callback(word + (" " if i < len(words) - 1 else ""))
            time.sleep(0.05)

        return LLMResponse(
            content=response_content,
            model=self.config.model,
            provider=self.config.provider,
            usage={"prompt_tokens": 100, "completion_tokens": len(words), "total_tokens": 100 + len(words)},
            finish_reason="stop",
            latency_ms=(time.time() - start) * 1000
        )

    def function_calling(self, messages: List[LLMMessage],
                        functions: List[FunctionCall],
                        **kwargs) -> Tuple[LLMResponse, Optional[FunctionCall]]:
        """模拟函数调用"""
        # 随机决定是否需要调用函数
        import random
        if random.random() < 0.3:  # 30% 概率调用函数
            func = functions[0]
            return LLMResponse(
                content="",
                model=self.config.model,
                provider=self.config.provider,
                usage={"total_tokens": 50}
            ), FunctionCallResult(
                call_id="mock_call_1",
                function_name=func.name,
                arguments={"arg1": "value1"}
            )

        return self.chat(messages, **kwargs), None

    def _generate_mock_response(self, last_message: str, kwargs: Dict) -> str:
        """生成模拟响应"""
        # 根据消息内容生成不同的响应
        if "销售" in last_message or "卖" in last_message:
            return "好的，我来帮您分析一下这个销售机会。根据您提供的信息，我建议从以下几个方面入手..."
        elif "客户" in last_message or "跟进" in last_message:
            return "客户跟进是非常重要的环节。我建议您今天下午给客户打个电话，确认一下需求..."
        elif "报价" in last_message or "价格" in last_message:
            return "根据市场行情和竞争对手的定价，我建议您报一个中等偏上的价格..."
        elif "合同" in last_message or "签署" in last_message:
            return "合同签署前请确保所有条款都已确认。我建议先发一份合同草案给客户审阅..."
        else:
            return "感谢您的提问。我理解您的需求，让我为您提供一些建议..."


# ── OpenAI LLM ────────────────────────────────────────

class OpenAILLM(BaseLLM):
    """OpenAI LLM"""

    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """发送对话请求"""
        try:
            import openai
        except ImportError:
            return LLMResponse(
                error="请安装 openai: pip install openai"
            )

        start = time.time()

        try:
            client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )

            response = client.chat.completions.create(
                model=self.config.model,
                messages=[m.to_dict() for m in messages],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                provider="openai",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                finish_reason=response.choices[0].finish_reason,
                latency_ms=(time.time() - start) * 1000
            )

        except Exception as e:
            return LLMResponse(
                error=str(e),
                latency_ms=(time.time() - start) * 1000
            )

    def chat_stream(self, messages: List[LLMMessage],
                   callback: Optional[Callable[[str], None]] = None,
                   **kwargs) -> LLMResponse:
        """流式对话"""
        try:
            import openai
        except ImportError:
            return LLMResponse(error="请安装 openai: pip install openai")

        start = time.time()
        full_content = ""

        try:
            client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )

            stream = client.chat.completions.create(
                model=self.config.model,
                messages=[m.to_dict() for m in messages],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=True,
                **kwargs
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    if callback:
                        callback(content)

            return LLMResponse(
                content=full_content,
                model=self.config.model,
                provider="openai",
                finish_reason="stop",
                latency_ms=(time.time() - start) * 1000
            )

        except Exception as e:
            return LLMResponse(
                content=full_content,
                error=str(e),
                latency_ms=(time.time() - start) * 1000
            )

    def function_calling(self, messages: List[LLMMessage],
                        functions: List[FunctionCall],
                        **kwargs) -> Tuple[LLMResponse, Optional[FunctionCallResult]]:
        """函数调用"""
        try:
            import openai
        except ImportError:
            return LLMResponse(error="请安装 openai: pip install openai"), None

        start = time.time()

        try:
            client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )

            tools = []
            for func in functions:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": func.name,
                        "description": func.description,
                        "parameters": func.parameters
                    }
                })

            response = client.chat.completions.create(
                model=self.config.model,
                messages=[m.to_dict() for m in messages],
                tools=tools,
                tool_choice="auto",
                temperature=self.config.temperature,
                **kwargs
            )

            message = response.choices[0].message

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                return LLMResponse(
                    content=message.content or "",
                    model=response.model,
                    provider="openai",
                    usage={"total_tokens": response.usage.total_tokens if response.usage else 0},
                    finish_reason=response.choices[0].finish_reason,
                    latency_ms=(time.time() - start) * 1000
                ), FunctionCallResult(
                    call_id=tool_call.id,
                    function_name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments)
                )

            return LLMResponse(
                content=message.content or "",
                model=response.model,
                provider="openai",
                usage={"total_tokens": response.usage.total_tokens if response.usage else 0},
                finish_reason=response.choices[0].finish_reason,
                latency_ms=(time.time() - start) * 1000
            ), None

        except Exception as e:
            return LLMResponse(
                error=str(e),
                latency_ms=(time.time() - start) * 1000
            ), None


# ── DeepSeek LLM ────────────────────────────────────────

class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM"""

    def chat(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """发送对话请求"""
        try:
            import openai
        except ImportError:
            return LLMResponse(error="请安装 openai: pip install openai")

        start = time.time()

        try:
            client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )

            response = client.chat.completions.create(
                model=self.config.model,
                messages=[m.to_dict() for m in messages],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                **kwargs
            )

            return LLMResponse(
                content=response.choices[0].message.content or "",
                model=response.model,
                provider="deepseek",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                },
                finish_reason=response.choices[0].finish_reason,
                latency_ms=(time.time() - start) * 1000
            )

        except Exception as e:
            return LLMResponse(error=str(e), latency_ms=(time.time() - start) * 1000)

    def chat_stream(self, messages: List[LLMMessage],
                   callback: Optional[Callable[[str], None]] = None,
                   **kwargs) -> LLMResponse:
        """流式对话"""
        # 与 OpenAI 类似的实现
        try:
            import openai
        except ImportError:
            return LLMResponse(error="请安装 openai: pip install openai")

        start = time.time()
        full_content = ""

        try:
            client = openai.OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )

            stream = client.chat.completions.create(
                model=self.config.model,
                messages=[m.to_dict() for m in messages],
                stream=True,
                **kwargs
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    if callback:
                        callback(content)

            return LLMResponse(
                content=full_content,
                model=self.config.model,
                provider="deepseek",
                latency_ms=(time.time() - start) * 1000
            )

        except Exception as e:
            return LLMResponse(
                content=full_content,
                error=str(e),
                latency_ms=(time.time() - start) * 1000
            )

    def function_calling(self, messages: List[LLMMessage],
                        functions: List[FunctionCall],
                        **kwargs) -> Tuple[LLMResponse, Optional[FunctionCallResult]]:
        """函数调用"""
        # 实现与 OpenAI 类似
        return self.chat(messages, **kwargs), None


# ── LLM 工厂 ────────────────────────────────────────

class LLMFactory:
    """LLM 工厂类"""

    _providers = {
        "openai": OpenAILLM,
        "deepseek": DeepSeekLLM,
        "mock": MockLLM,
    }

    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLM:
        """创建 LLM 实例"""
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"不支持的 LLM 提供商: {config.provider}")
        return provider_class(config)

    @classmethod
    def register(cls, name: str, provider_class: type):
        """注册新的 LLM 提供商"""
        cls._providers[name] = provider_class


# ── LLM 管理器 ────────────────────────────────────────

class LLMManager:
    """LLM 管理器"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig.mock()
        self._llm: Optional[BaseLLM] = None

    @property
    def llm(self) -> BaseLLM:
        """获取 LLM 实例（懒加载）"""
        if self._llm is None:
            self._llm = LLMFactory.create(self.config)
        return self._llm

    def chat(self, message: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        """简单对话"""
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=message))
        return self.llm.chat(messages, **kwargs)

    def chat_with_history(self, messages: List[Dict], **kwargs) -> LLMResponse:
        """带历史的对话"""
        llm_messages = [LLMMessage.from_dict(m) for m in messages]
        return self.llm.chat(llm_messages, **kwargs)

    def chat_stream(self, message: str, system_prompt: str = "",
                   callback: Optional[Callable[[str], None]] = None,
                   **kwargs) -> LLMResponse:
        """流式对话"""
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=message))
        return self.llm.chat_stream(messages, callback, **kwargs)

    def function_calling(self, messages: List[Dict],
                        functions: List[FunctionCall],
                        **kwargs) -> Tuple[LLMResponse, Optional[FunctionCallResult]]:
        """函数调用"""
        llm_messages = [LLMMessage.from_dict(m) for m in messages]
        return self.llm.function_calling(llm_messages, functions, **kwargs)


# ── 预设 Agent 角色 ────────────────────────────────────────

AGENT_SYSTEM_PROMPTS = {
    "market_research": """你是一个专业的市场调研官，擅长：
1. 分析行业趋势和市场竞争格局
2. 识别潜在客户和市场机会
3. 收集和分析市场数据
4. 生成市场洞察报告

请用专业、简洁的语言回答。""",

    "competitor_intel": """你是一个专业的竞品分析官，擅长：
1. 监控竞品动态和产品更新
2. 分析竞品优劣势
3. 追踪竞品定价策略
4. 生成竞品对比报告

请用客观、分析性的语言回答。""",

    "presales": """你是一个专业的售前谈判官，擅长：
1. 理解客户需求和痛点
2. 展示产品价值和差异化
3. 处理客户异议和价格谈判
4. 推动销售进程和成交

请用专业、有说服力的语言回答。""",

    "aftersales": """你是一个专业的售后维系官，擅长：
1. 维护客户关系和满意度
2. 处理客户问题和投诉
3. 推动客户成功和续费
4. 收集客户反馈和改进建议

请用耐心、专业的语言回答。""",

    "procurement": """你是一个专业的采购供应链官，擅长：
1. 供应商寻源和评估
2. 成本分析和谈判
3. 供应链风险管理
4. 合同条款审核

请用严谨、专业的语言回答。""",

    "operations": """你是一个专业的运营增长官，擅长：
1. 分析销售数据和 KPIs
2. 识别增长机会和优化点
3. 制定运营策略
4. 生成数据报告和建议

请用数据驱动、专业的语言回答。""",
}


# ── 工厂函数 ────────────────────────────────────────

__all__ = [
    "LLMProvider",
    "MessageRole",
    "LLMMessage",
    "LLMResponse",
    "FunctionCall",
    "FunctionCallResult",
    "LLMConfig",
    "BaseLLM",
    "MockLLM",
    "OpenAILLM",
    "DeepSeekLLM",
    "LLMFactory",
    "LLMManager",
    "AGENT_SYSTEM_PROMPTS",
    "get_llm_manager",
    "create_llm",
    "get_llm",
    "SalesLLM",
    "SalesLLMConfig",
    "get_sales_llm",
    "FallbackChain",
]

from SentriKit_salesmaster.core.llm_engine import (
    SalesLLM,
    SalesLLMConfig,
    get_sales_llm,
    FallbackChain,
)

def get_llm_manager(config: Optional[LLMConfig] = None) -> LLMManager:
    """获取 LLM 管理器"""
    return LLMManager(config)


def create_llm(provider: str = "mock", **kwargs) -> BaseLLM:
    """快速创建 LLM 实例"""
    config = LLMConfig(provider=provider, **kwargs)
    return LLMFactory.create(config)


# ── 快速获取 LLM 实例 ────────────────────────────

_global_llm: Optional[BaseLLM] = None


def get_llm(provider: str = "", **kwargs) -> BaseLLM:
    """获取 LLM 实例（带自动检测+缓存）

    优先使用环境变量配置的 provider，自动检测 DeepSeek/OpenAI API Key。
    无 Key 时返回 MockLLM（可正常调用但返回模拟响应）。
    """
    global _global_llm

    if _global_llm is not None and not provider:
        return _global_llm

    if not provider:
        # 自动检测: DEEPSEEK -> OPENAI -> MOCK
        if os.environ.get("DEEPSEEK_API_KEY"):
            provider = "deepseek"
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            provider = "mock"

    config = LLMConfig(provider=provider, **kwargs)
    llm = LLMFactory.create(config)

    if not provider:
        _global_llm = llm

    return llm
