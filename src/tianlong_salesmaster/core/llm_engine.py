"""SentriKit_salesmaster.team_pkg.llm — SalesMaster LLM 驱动引擎

通过 HTTP API 调用 LLM，零外部依赖（使用 urllib）。
不强制依赖任何 LLM 库。无 Key 时自动降级。

降级链（三级）:
  1. DeepSeek API（主引擎）
  2. 本地 3B 量化模型（llama.cpp 子进程，可选，需安装）
  3. 规则引擎关键词匹配（兜底）
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # noqa: E402 — 用于本地模型子进程调用
import shutil  # noqa: E402 — 用于检查 llama-cli 是否在 PATH 中
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen
from urllib.error import URLError


# ── LLM 配置（复用 judge/llm.py 的设计）──

@dataclass
class SalesLLMConfig:
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "SalesLLMConfig":
        return cls(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            model=os.environ.get("LLM_MODEL", "deepseek-chat"),
        )

    @classmethod
    def from_config(cls) -> "SalesLLMConfig":
        """从项目 config 加载"""
        try:
            from SentriKit import config
            cfg = config.ensure_config()
            key = cfg.get("deepseek_key", "") or cfg.get("openai_key", "") or os.environ.get("DEEPSEEK_API_KEY", "")
            return cls(api_key=key)
        except Exception:
            return cls.from_env()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


# ── Prompt 模板 ──

PSYCHOLOGY_PROMPT = """你是一位销售心理分析师。分析客户的以下发言，输出JSON。

客户发言: {text}
客户情感: {sentiment}

请分析:
1. emotion: 客户当前情绪 (excited/interested/neutral/hesitant/anxious/skeptical/frustrated)
2. intensity: 兴趣强度 (0.0-1.0)
3. hesitation_signals: 犹豫信号列表 (如"预算""考虑""不确定"等关键词)
4. compliance_ladder: 服从性阶梯完成度 (0-100%)
5. loss_aversion: 损失厌恶程度 (0.0-1.0) — 客户是否更担心失去现有方案

只输出JSON，不要其他文字：
{{"emotion":"...","intensity":0.0,"hesitation_signals":[],"compliance_ladder":0,"loss_aversion":0.0}}"""

VALUE_TRANSLATION_PROMPT = """你是一位技术销售顾问。将客户的技术需求翻译为商业价值。

客户需求: {text}

输出JSON:
1. business_value: 商业价值描述(一句话)
2. pain_points: 痛点列表 (最多3个)
3. success_metric: 可量化的成功指标
4. estimated_roi: 预估ROI描述
5. urgency_level: 紧迫程度 (low/medium/high)

{{"business_value":"...","pain_points":[],"success_metric":"...","estimated_roi":"...","urgency_level":"medium"}}"""

COMPETITOR_INTEL_PROMPT = """你是一位竞品情报分析师。分析当前市场格局，输出JSON。

客户提到: {text}
已知客户: {customer}

输出JSON:
1. mentioned_competitors: 客户提到的竞品列表
2. our_advantages: 我们的优势点 (最多3个)
3. risk_factors: 竞品可能反击的风险点
4. positioning_advice: 定位建议

{{"mentioned_competitors":[],"our_advantages":[],"risk_factors":[],"positioning_advice":"..."}}"""

STRATEGY_PROMPT = """你是一位销售策略师。基于以下销售对话分析，制定下一步策略。

客户信息:
- 公司: {company}
- 行业: {industry}
- 阶段: {stage}
- 发言次数: {utterances}
- 当前情绪: {emotion}
- 合规分数: {compliance_score}

历史对话:
{history}

输出JSON:
1. next_action: 下一步行动建议
2. recommended_message: 推荐的回复话术 (中文, 不超过100字)
3. risk_warning: 风险警告 (无风险则空字符串)
4. deal_readiness: 成交准备度 (0-100)

{{"next_action":"...","recommended_message":"...","risk_warning":"...","deal_readiness":0}}"""


# ── LLM 调用器 ──


# ═══════════════════════════════════════════════════════
# 第一级降级：Ollama 本地模型（HTTP API，最易安装）
# ═══════════════════════════════════════════════════════

_OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_OLLAMA_DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")


class OllamaLLM:
    """Ollama 本地模型调用器（通过 HTTP API）。

    零外部 Python 依赖，使用 urllib 调用 Ollama API。
    安装 Ollama: curl -fsSL https://ollama.com/install.sh | sh
    下载模型: ollama pull qwen2.5:3b

    API 兼容 OpenAI 格式，返回标准 chat/completions 响应。
    """

    def __init__(
        self,
        base_url: str = _OLLAMA_BASE_URL,
        model: str = _OLLAMA_DEFAULT_MODEL,
        timeout: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def available(self) -> bool:
        """Ollama 可用条件：能够访问 API 且模型存在。

        通过轻量请求 /api/tags 检测，不消耗 token。
        """
        try:
            req = Request(f"{self.base_url}/api/tags", method="GET")
            resp = urlopen(req, timeout=3)
            data = json.loads(resp.read().decode())
            models = data.get("models", [])
            # 检查目标模型是否已拉取
            model_name = self.model
            if ":" not in model_name:
                model_name += ":latest"
            for m in models:
                if m.get("name") == model_name:
                    return True
            # 任意模型存在也算可用（降级到可用模型）
            return len(models) > 0
        except Exception:
            return False

    def chat(
        self,
        system: str,
        user: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """调用 Ollama 模型生成回复（OpenAI 兼容格式）。"""
        if not self._check_server():
            return None

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }).encode("utf-8")

        try:
            req = Request(
                f"{self.base_url}/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urlopen(req, timeout=self.timeout)
            result = json.loads(resp.read().decode("utf-8"))
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() if content else None
        except Exception:
            return None

    def chat_json(
        self,
        system: str,
        user: str,
        **kwargs,
    ) -> Optional[Dict]:
        """调用 Ollama 模型并返回 JSON。"""
        content = self.chat(system, user, **kwargs)
        if not content:
            return None
        return self._extract_json(content)

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """从文本中提取 JSON 对象。"""
        text = text.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    return None
            return None

    def _check_server(self) -> bool:
        """轻量检测 Ollama 服务是否运行。"""
        try:
            req = Request(f"{self.base_url}/api/tags", method="GET")
            resp = urlopen(req, timeout=3)
            return resp.status == 200
        except Exception:
            return False

    @staticmethod
    def install_guide() -> str:
        return (
            "安装 Ollama:\n"
            "  curl -fsSL https://ollama.com/install.sh | sh\n"
            "下载模型:\n"
            "  ollama pull qwen2.5:3b\n"
            "设置环境变量:\n"
            "  export OLLAMA_HOST=http://localhost:11434\n"
            "  export OLLAMA_MODEL=qwen2.5:3b\n"
        )


# ═══════════════════════════════════════════════════════
# 第二级降级：本地 3B 量化模型（llama.cpp 子进程）
# ═══════════════════════════════════════════════════════

_LOCAL_MODEL_PATH = os.path.expanduser("~/.local/llm/qwen2.5-3b-instruct-q4_k_m.gguf")
_LOCAL_CMD = "llama-cli"  # llama.cpp 的 CLI 命令


class LocalLLM:
    """本地 3B 量化模型调用器（通过 llama.cpp 子进程）。

    零外部依赖，子进程调用方式：
        llama-cli -m <model.gguf> -p "<prompt>" -n 512 --temp 0.7

    没有安装 llama.cpp 或没有模型文件时，available 返回 False，
    自动跳过，不影响调用方。
    """

    def __init__(
        self,
        model_path: str = _LOCAL_MODEL_PATH,
        cli_cmd: str = _LOCAL_CMD,
    ):
        self.model_path = model_path
        self.cli_cmd = cli_cmd

    @property
    def available(self) -> bool:
        """本地模型可用条件：llama-cli 存在 + 模型文件存在"""
        if not os.path.exists(self.model_path):
            return False
        return shutil.which(self.cli_cmd) is not None

    def chat(
        self,
        system: str,
        user: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        timeout: int = 30,
    ) -> Optional[str]:
        """调用本地模型生成回复。

        使用 Qwen 2.5 的 chat template 格式：
            <|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>
        """
        if not self.available:
            return None

        prompt = (
            f"<|system|>\n{system}\n"
            f"<|user|>\n{user}\n"
            f"<|assistant|>\n"
        )

        cmd = [
            self.cli_cmd,
            "-m", self.model_path,
            "-p", prompt,
            "-n", str(max_tokens),
            "--temp", str(temperature),
            "--no-display-prompt",  # 不输出 prompt 本身
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode != 0:
                return None
            output = result.stdout.strip()
            return output if output else None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def chat_json(
        self,
        system: str,
        user: str,
        **kwargs,
    ) -> Optional[Dict]:
        """调用本地模型并返回 JSON。"""
        text = self.chat(system, user, **kwargs)
        if not text:
            return None
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """从文本中提取 JSON 对象。"""
        text = text.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    return None
            return None


# ═══════════════════════════════════════════════════════
# 三级降级链编排器
# ═══════════════════════════════════════════════════════

# 熔断配置
_CIRCUIT_BREAK_THRESHOLD = 5     # 连续失败阈值
_CIRCUIT_RECOVERY_SECONDS = 60   # 熔断恢复时间


class FallbackChain:
    """三级降级链编排器。

    调用顺序：
      1. DeepSeek API（主引擎）
      2. Ollama 本地模型（HTTP API，优先于子进程）
      3. 本地 3B 量化模型（llama.cpp 子进程）
      4. 规则引擎（关键词匹配兜底）

    带熔断机制：API 连续失败 5 次后熔断 60 秒，不再调用。
    """

    def __init__(
        self,
        api: Optional[SalesLLMConfig] = None,
        local: Optional[LocalLLM] = None,
        ollama: Optional[OllamaLLM] = None,
    ):
        self._api_config = api or SalesLLMConfig.from_config()
        self._local = local or LocalLLM()
        self._ollama = ollama or OllamaLLM()
        self._rules = RuleFallback()

        # 熔断状态
        self._api_fail_count: int = 0
        self._circuit_open: bool = False
        self._circuit_opened_at: float = 0.0

    @property
    def api_available(self) -> bool:
        """API 是否可用（有 Key + 未熔断）"""
        if not self._api_config.is_configured:
            return False
        if self._circuit_open:
            # 检查熔断是否到期
            if time.time() - self._circuit_opened_at >= _CIRCUIT_RECOVERY_SECONDS:
                self._circuit_open = False
                self._api_fail_count = 0
                return True
            return False
        return True

    @property
    def local_available(self) -> bool:
        return self._local.available

    @property
    def ollama_available(self) -> bool:
        return self._ollama.available

    @property
    def level(self) -> str:
        if self.api_available:
            return "api"
        if self.ollama_available:
            return "ollama"
        if self.local_available:
            return "local"
        return "rule"

    def _call_api(self, system: str, user: str) -> Optional[str]:
        """调用 DeepSeek API（带重试和熔断）"""
        if not self._api_config.is_configured:
            # 无 Key 不计入失败计数（不是 API 故障）
            return None

        if self._circuit_open:
            # 检查熔断是否到期
            if time.time() - self._circuit_opened_at >= _CIRCUIT_RECOVERY_SECONDS:
                self._circuit_open = False
                self._api_fail_count = 0
            else:
                return None

        payload = json.dumps({
            "model": self._api_config.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self._api_config.temperature,
            "max_tokens": self._api_config.max_tokens,
        }).encode("utf-8")

        for attempt in range(3):  # 重试 3 次
            try:
                req = Request(
                    f"{self._api_config.base_url}/chat/completions",
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self._api_config.api_key}",
                    },
                    method="POST",
                )
                resp = urlopen(req, timeout=self._api_config.timeout)
                result = json.loads(resp.read().decode("utf-8"))
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    self._api_fail_count = 0  # 成功，重置失败计数
                    return content
            except Exception:
                pass
            time.sleep([1, 3, 7][attempt])

        # 连续失败
        self._api_fail_count += 1
        if self._api_fail_count >= _CIRCUIT_BREAK_THRESHOLD:
            self._circuit_open = True
            self._circuit_opened_at = time.time()
        return None

    def chat(self, system: str, user: str) -> Optional[str]:
        # 第一级：DeepSeek API
        try:
            result = self._call_api(system, user)
            if result:
                return result
        except Exception:
            pass

        # 第二级：Ollama 本地模型
        if self.ollama_available:
            try:
                result = self._ollama.chat(system, user)
                if result:
                    return result
            except Exception:
                pass

        # 第三级：本地 3B 量化模型（llama.cpp 子进程）
        if self.local_available:
            try:
                result = self._local.chat(system, user)
                if result:
                    return result
            except Exception:
                pass

        # 第四级：规则引擎兜底
        try:
            return self._rules.generate_response(system, user)
        except Exception:
            return None

    def chat_json(self, system: str, user: str) -> Optional[Dict]:
        """三级降级 + JSON 解析。"""
        text = self.chat(system, user)
        if not text:
            return None
        return self._parse_json(text)

    @staticmethod
    def _parse_json(content: Optional[str]) -> Optional[Dict]:
        """从 LLM 返回中提取 JSON。"""
        if not content:
            return None
        text = content.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$\s*", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    return None
            return None

    def reset_circuit(self) -> None:
        """手动重置熔断器。"""
        self._circuit_open = False
        self._api_fail_count = 0

    def get_status(self) -> Dict:
        return {
            "api_available": self.api_available,
            "ollama_available": self.ollama_available,
            "local_available": self.local_available,
            "level": self.level,
            "circuit_open": self._circuit_open,
            "api_fail_count": self._api_fail_count,
            "api_key_configured": self._api_config.is_configured,
            "ollama_model": self._ollama.model if self.ollama_available else "",
            "local_model_path": self._local.model_path if self.local_available else "",
        }


# ═══════════════════════════════════════════════════════
# RuleFallback（规则引擎降级）
# ═══════════════════════════════════════════════════════

class RuleFallback:
    """规则引擎降级——API 和本地模型都不可用时的兜底方案。"""

    @staticmethod
    def generate_response(system: str, user: str) -> Optional[str]:
        """根据 system prompt 类型生成对应的规则响应。"""
        sys_lower = system.lower()
        # 精确匹配优先（按匹配粒度从细到粗）
        if "psycholog" in sys_lower or "心理" in system or "emotion" in sys_lower or "sentiment" in sys_lower:
            return RuleFallback._psychology_response(user)
        if "competitor" in sys_lower or "竞品" in system or "intel" in sys_lower:
            return RuleFallback._competitor_response(user)
        if "strateg" in sys_lower or "策略" in system or "next_action" in sys_lower:
            return RuleFallback._strategy_response(user)
        if "value" in sys_lower or "价值" in system or "翻译" in system or "商业" in system or "roi" in sys_lower:
            return RuleFallback._value_response(user)
        if "sales" in sys_lower or "销售" in system or "market" in sys_lower or "市场" in system:
            return RuleFallback._sales_response(user)
        return None

    @staticmethod
    def _sales_response(user: str) -> str:
        import random
        templates = [
            f"您好，了解到贵公司正在寻求AI解决方案，我们的产品能有效提升效率、降低成本。期待进一步交流。",
            f"感谢您的关注！我们为同行业客户提供了成熟的AI驱动方案，效果显著。请问您目前关注哪些具体需求？",
        ]
        return random.choice(templates)

    @staticmethod
    def _psychology_response(user: str) -> str:
        return json.dumps({
            "emotion": "neutral",
            "intensity": 0.5,
            "hesitation_signals": [],
            "compliance_ladder": 50,
            "loss_aversion": 0.3,
        }, ensure_ascii=False)

    @staticmethod
    def _competitor_response(user: str) -> str:
        return json.dumps({
            "mentioned_competitors": [],
            "our_advantages": ["功能全面", "开源免费", "易于集成"],
            "risk_factors": [],
            "positioning_advice": "突出开源免费和企业级支持的优势",
        }, ensure_ascii=False)

    @staticmethod
    def _strategy_response(user: str) -> str:
        return json.dumps({
            "next_action": "跟进客户具体需求",
            "recommended_message": "请问您对我们的方案还有什么具体问题？我们可以为您安排一次详细演示。",
            "risk_warning": "",
            "deal_readiness": 30,
        }, ensure_ascii=False)

    @staticmethod
    def _value_response(user: str) -> str:
        return json.dumps({
            "business_value": "通过AI Agent自动化提升运营效率，降低人工成本",
            "pain_points": ["效率瓶颈", "成本压力", "技术迭代"],
            "success_metric": "ROI提升30%以上",
            "estimated_roi": "高",
            "urgency_level": "medium",
        }, ensure_ascii=False)

    @staticmethod
    def negotiate_price(base_price: float, customer_offer: float) -> Dict:
        ratio = customer_offer / base_price if base_price > 0 else 1
        if ratio >= 0.9:
            return {"action": "accept", "reason": "客户出价合理"}
        elif ratio >= 0.7:
            mid = (base_price + customer_offer) / 2
            return {"action": "counter", "counter_price": round(mid, -2), "reason": "折中方案"}
        else:
            return {"action": "reject", "reason": "出价过低，无法接受"}


# ═══════════════════════════════════════════════════════
# SalesLLM（保持向后兼容的包装器）
# ═══════════════════════════════════════════════════════

class SalesLLM:
    """SalesMaster 的统一 LLM 调用器。

    - 无 Key 时自动降级到规则引擎
    - 带简单缓存避免重复调用
    - 内部使用 FallbackChain 三级降级
    """

    def __init__(self):
        self.config = SalesLLMConfig.from_config()
        self._cache: Dict[str, Any] = {}

        # 内部使用 FallbackChain 三级降级
        self._chain = FallbackChain(api=self.config)

    @property
    def available(self) -> bool:
        return self._chain.api_available or self._chain.local_available

    def _call(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """调用 LLM（使用 FallbackChain 三级降级）。"""
        cache_key = f"{system_prompt[:50]}:{user_prompt[:100]}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        content = self._chain.chat(system_prompt, user_prompt)
        if content:
            self._cache[cache_key] = content
        return content

    def _parse_json(self, content: Optional[str]) -> Optional[Dict]:
        """从 LLM 返回中提取 JSON。"""
        if not content:
            return None
        text = content.strip()
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    return None
            return None

    # ── 各引擎的 LLM 分析 ──

    def analyze_psychology(self, text: str, sentiment: str = "neutral") -> Dict:
        """心理引擎：情绪/犹豫/损失厌恶分析"""
        if not self.available:
            return {"emotion": "neutral", "intensity": 0.5, "hesitation_signals": [],
                    "compliance_ladder": 0, "loss_aversion": 0.0}
        prompt = PSYCHOLOGY_PROMPT.format(text=text, sentiment=sentiment)
        result = self._parse_json(self._call("你是一位销售心理分析师。", prompt))
        return result or {"emotion": "neutral", "intensity": 0.5, "hesitation_signals": [],
                          "compliance_ladder": 0, "loss_aversion": 0.0}

    def translate_value(self, text: str) -> Dict:
        """价值引擎：技术需求→商业价值"""
        if not self.available:
            return {"business_value": text, "pain_points": [], "success_metric": "综合影响",
                    "estimated_roi": "待评估", "urgency_level": "medium"}
        prompt = VALUE_TRANSLATION_PROMPT.format(text=text)
        result = self._parse_json(self._call("你是一位技术销售顾问。", prompt))
        return result or {"business_value": text, "pain_points": [], "success_metric": "综合影响",
                          "estimated_roi": "待评估", "urgency_level": "medium"}

    def analyze_competitors(self, text: str, customer: str = "") -> Dict:
        """竞品情报引擎"""
        if not self.available:
            return {"mentioned_competitors": [], "our_advantages": [],
                    "risk_factors": [], "positioning_advice": ""}
        prompt = COMPETITOR_INTEL_PROMPT.format(text=text, customer=customer)
        result = self._parse_json(self._call("你是一位竞品情报分析师。", prompt))
        return result or {"mentioned_competitors": [], "our_advantages": [],
                          "risk_factors": [], "positioning_advice": ""}

    def generate_strategy(self, context: Dict) -> Dict:
        """策略引擎：生成下一步行动"""
        if not self.available:
            return {"next_action": "跟进", "recommended_message": "",
                    "risk_warning": "", "deal_readiness": 0}
        history_text = "\n".join(context.get("history", []))[:1000]
        prompt = STRATEGY_PROMPT.format(
            company=context.get("company", ""),
            industry=context.get("industry", ""),
            stage=context.get("stage", "initial"),
            utterances=context.get("utterances", 0),
            emotion=context.get("emotion", "neutral"),
            compliance_score=context.get("compliance_score", 0.0),
            history=history_text,
        )
        result = self._parse_json(self._call("你是一位销售策略师。", prompt))
        return result or {"next_action": "跟进", "recommended_message": "",
                          "risk_warning": "", "deal_readiness": 0}


# ── 快捷函数 ──

_global_llm: Optional[SalesLLM] = None


def get_sales_llm() -> SalesLLM:
    global _global_llm
    if _global_llm is None:
        _global_llm = SalesLLM()
    return _global_llm
