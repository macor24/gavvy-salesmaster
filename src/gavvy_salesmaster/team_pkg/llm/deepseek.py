"""gavvy_salesmaster.team_pkg.llm.deepseek — DeepSeek API 调用引擎

零外部依赖（使用 urllib）。
支持 DeepSeek / OpenAI 兼容 API。
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError


DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
ENV_API_KEY = "LLM_API_KEY"
ENV_BASE_URL = "LLM_BASE_URL"
ENV_MODEL = "LLM_MODEL"


def get_config() -> dict:
    """获取 LLM 配置（环境变量优先）"""
    return {
        "api_key": os.environ.get(ENV_API_KEY, "") or os.environ.get("OPENAI_API_KEY", ""),
        "base_url": os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL),
        "model": os.environ.get(ENV_MODEL, DEFAULT_MODEL),
    }


def llm_call(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    timeout: int = 30,
) -> Optional[str]:
    """调用 LLM API，返回原始文本。"""
    cfg = get_config()
    if not cfg["api_key"]:
        return None

    payload = json.dumps({
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    try:
        req = Request(
            f"{cfg['base_url']}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg['api_key']}",
            },
            method="POST",
        )
        resp = urlopen(req, timeout=timeout)
        result = json.loads(resp.read().decode("utf-8"))
        return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception:
        return None


def extract_json(text: Optional[str]) -> Optional[Dict]:
    """从 LLM 返回中提取 JSON。"""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                return None
        return None


class DeepSeekEngine:
    """DeepSeek LLM 引擎。

    提供结构化调用接口，自动处理 JSON 解析和错误降级。
    """

    def __init__(self):
        self._config = get_config()

    @property
    def available(self) -> bool:
        return bool(self._config["api_key"])

    def chat(self, system: str, user: str, **kwargs) -> Optional[str]:
        return llm_call(system, user, **kwargs)

    def chat_json(self, system: str, user: str, **kwargs) -> Optional[Dict]:
        """调用 LLM 并返回解析后的 JSON。"""
        text = self.chat(system, user, **kwargs)
        return extract_json(text)

    def generate_sales_message(self, product_info: str, customer_info: str) -> str:
        """生成销售话术。"""
        if not self.available:
            return ""
        system = "你是一位专业销售顾问，根据产品信息和客户信息生成个性化销售话术。"
        user = f"产品: {product_info}\n客户: {customer_info}\n请生成一段简洁有力的初次接触话术。"
        return self.chat(system, user) or ""

    def analyze_customer_intent(self, conversation: str) -> Dict:
        """分析客户意向等级。"""
        if not self.available:
            return {"intent": "unknown", "score": 0.5}
        system = "你是一位销售心理学专家，分析客户对话中的购买意向。"
        user = f"对话记录:\n{conversation}\n\n分析客户意向等级（high/medium/low）和信心评分(0-1)。输出JSON。"
        result = self.chat_json(system, user)
        return result or {"intent": "unknown", "score": 0.5}

    def negotiate_price(self, product_price: str, customer_request: str, history: str = "") -> Dict:
        """价格谈判。"""
        if not self.available:
            return {"action": "hold", "reason": "LLM不可用，保持原价"}
        system = "你是一位议价专家，在给定价格范围内进行谈判。"
        user = f"产品价格: {product_price}\n客户要求: {customer_request}\n历史: {history}\n\n输出JSON:{'action':'accept/ counter/ reject', 'counter_price':0, 'reason':'...'}"
        return self.chat_json(system, user) or {"action": "hold", "reason": "分析失败"}
