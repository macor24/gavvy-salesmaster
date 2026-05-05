"""tianlong.sales.master — Chat Sales 核心引擎

基于 Chat Sales 六大能力模块（13项技能）的完整实现。
通过 HTTP API 或 CLI 子进程调用天龙1号，不强制代码级依赖。

能力架构：
  Phase 1: 高阶心理博弈与能量感知（§1-3）
  Phase 2: 自动化复杂多线程谈判管理（§4-5）
# Phase 3: 价值量化与商业洞察顾问技能（§6-7）
"""

from __future__ import annotations

import json
import os
import sys
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .tianlong_client import TianlongAPIClient


# ── 天龙1号 API 客户端（轻量） ────────────────

_TIANLONG_API_URL: Optional[str] = None
_TIANLONG_AVAILABLE: Optional[bool] = None
_TIANLONG_ENABLED: bool = True
_TIANLONG_CLIENT: Optional[TianlongAPIClient] = None


def _get_tianlong_client() -> TianlongAPIClient:
    global _TIANLONG_CLIENT
    if _TIANLONG_CLIENT is None:
        url = _TIANLONG_API_URL or os.environ.get("TIANLONG_API_URL", "")
        _TIANLONG_CLIENT = TianlongAPIClient(
            api_url=url,
            project_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
    return _TIANLONG_CLIENT


def _get_tianlong_api_url() -> str:
    return _TIANLONG_API_URL or os.environ.get("TIANLONG_API_URL", "")


def check_tianlong() -> bool:
    global _TIANLONG_AVAILABLE
    if _TIANLONG_AVAILABLE is not None:
        return _TIANLONG_AVAILABLE
    client = _get_tianlong_client()
    result = client.health()
    if "status" in result and result["status"] == "ok":
        _TIANLONG_AVAILABLE = True
        return True
    _TIANLONG_AVAILABLE = False
    return False


def is_tianlong_enabled() -> bool:
    return _TIANLONG_ENABLED and check_tianlong()


def set_tianlong_enabled(enabled: bool) -> bool:
    global _TIANLONG_ENABLED
    _TIANLONG_ENABLED = enabled
    return _TIANLONG_ENABLED


def get_tianlong_status() -> dict:
    mode = "http" if _get_tianlong_api_url() else "local"
    return {"available": check_tianlong(), "enabled": _TIANLONG_ENABLED, "active": is_tianlong_enabled(), "mode": mode}


def _tianlong_report_highlight(title: str, body: str, highlights: list, action_items: list) -> bool:
    client = _get_tianlong_client()
    result = client.report(title=title, body=body, highlights=highlights, action_items=action_items)
    return result.get("status") == "ok"


# ── 进化闭环快捷调用 ──────────────────────────

def tianlong_run_evolve() -> dict:
    """触发天龙1号完整进化闭环"""
    client = _get_tianlong_client()
    return client.run_evolve()


def tianlong_evolve_status() -> dict:
    """天龙1号进化状态"""
    client = _get_tianlong_client()
    return client.evolve_status()


def tianlong_evaluate_metacog(success_rate_7d: float = 0.85, days_since_last_improvement: int = 0, repeat_error_count: int = 0) -> dict:
    """退化检测"""
    client = _get_tianlong_client()
    return client.evaluate_metacog(
        success_rate_7d=success_rate_7d,
        days_since_last_improvement=days_since_last_improvement,
        repeat_error_count=repeat_error_count,
    )


def tianlong_evaluate_judge(summary: str) -> dict:
    """提案评分"""
    client = _get_tianlong_client()
    return client.evaluate_judge(summary=summary)


# ── 自动调度 ─────────────────────────────────

def tianlong_auto_check() -> dict:
    """自动检查是否需要进化，需要则触发。返回检查结果。"""
    client = _get_tianlong_client()
    
    # 1. 获取指标
    try:
        from tianlong.selfmodel import SelfModel
        sm = SelfModel(project_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        history = sm.get_history()
        snapshot = history.get("latest_snapshot", {})
        decisions = history.get("recent_decisions", [])
        success_rate = snapshot.get("overall_success_rate", 0.85) or 0.85
        days_stagnant = 0
        if decisions:
            try:
                from datetime import datetime
                last_ts = decisions[-1].get("timestamp", "")
                if last_ts:
                    last_dt = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
                    days_stagnant = (datetime.now() - last_dt).days
            except ValueError:
                pass
        repeat_errors = max(1, int(snapshot.get("error_rate_7d", 0) * 10))
    except Exception:
        success_rate, days_stagnant, repeat_errors = 0.85, 0, 1
    
    # 2. 退化检测
    mc = client.evaluate_metacog(
        success_rate_7d=success_rate,
        days_since_last_improvement=days_stagnant,
        repeat_error_count=repeat_errors,
    )
    
    result = {
        "checked": True,
        "should_evolve": mc.get("should_evolve", False),
        "metacog_score": mc.get("score", 0),
        "success_rate": success_rate,
        "days_stagnant": days_stagnant,
    }
    
    # 3. 需要则触发
    if mc.get("should_evolve", False):
        evolve_result = client.run_evolve()
        result["evolved"] = True
        result["evolve_result"] = evolve_result.get("evolved", False)
    else:
        result["evolved"] = False
    
    return result


# ── 六维引擎导入 ─────────────────────────────

from .psychology import PsychologicalEngine, EnergyState, ComplianceStep
from .multithread import MultiThreadManager, CustomerContact
from .value import ValueConsultant, ValueEquation
from .risk import RiskManager
from .language import LanguageMaster
from .evolver import StrategyEvolver


# ═══════════════════════════════════════════════════════════════
# 基础数据类型
# ═══════════════════════════════════════════════════════════════

class NegotiationStage(Enum):
    INITIAL = "initial"
    DISCOVERY = "discovery"
    SOLUTION = "solution"
    OBJECTION = "objection"
    CLOSING = "closing"
    POST_SALE = "post_sale"


class CustomerEmotion(Enum):
    NEUTRAL = "neutral"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    INTERESTED = "interested"
    DOUBTFUL = "doubtful"
    INDIFFERENT = "indifferent"


# ═══════════════════════════════════════════════════════════════
# Phase 1: 高阶心理博弈与能量感知
# ═══════════════════════════════════════════════════════════════

@dataclass
class SalesMaster:
    """Chat Sales — 六维能力总控制器。"""

    def __init__(self, company_name: str = "", industry: str = "",
                 reporter: Any = None):
        self.company = company_name
        self.industry = industry
        self.psychology = PsychologicalEngine()
        self.multithread = MultiThreadManager()
        self.consultant = ValueConsultant()
        self.risk = RiskManager()
        self.language = LanguageMaster()
        self.evolver = StrategyEvolver()
        self._reporter = reporter
        self._stage: str = "initial"
        self._session_log: List[Dict] = []
        self._deal_open: bool = False

    def start_deal(self, customer: str) -> None:
        self._deal_open = True
        self._session_log = []
        self._stage = "initial"

    def process_customer_input(self, text: str, pause_sec: float = 0.0,
                                sentiment: str = "neutral") -> Dict:
        result: Dict[str, Any] = {}
        energy = self.psychology.assess_energy(text, pause_sec, sentiment)
        energy_response = self.psychology.generate_energy_response(energy)
        result["psychology"] = {
            "emotion": energy.emotion,
            "intensity": energy.intensity,
            "hesitation": energy.hesitation_signals,
        }
        para = self.language.decode_paralanguage(text, pause_sec)
        result["paralanguage"] = para
        value = self.consultant.translate_pain_to_value(text)
        result["value_translation"] = value
        responses = []
        if energy_response:
            responses.append(energy_response)
        if para.get("response"):
            responses.append(para["response"])
        if not responses:
            llm = _get_llm()
            if llm.available:
                try:
                    strategy = llm.generate_strategy({
                        "company": self.company, "industry": self.industry,
                        "stage": self._stage, "utterances": len(self._session_log) + 1,
                        "emotion": energy.emotion, "compliance_score": self.psychology.compliance_score,
                        "history": [s.get("input", "") for s in self._session_log[-5:]],
                    })
                    llm_msg = strategy.get("recommended_message", "")
                    if llm_msg:
                        responses = [llm_msg]
                except Exception:
                    pass
        result["recommended_response"] = "\n\n".join(responses) if responses else ""
        result["compliance_status"] = {"score": self.psychology.compliance_score}
        self._session_log.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": text[:100],
            "analysis": result,
        })
        return result

    def get_session_summary(self) -> Dict:
        return {
            "company": self.company, "industry": self.industry,
            "stage": self._stage, "utterances": len(self._session_log),
            "compliance_score": self.psychology.compliance_score,
            "contacts": list(self.multithread._contacts.keys()) if self.multithread._contacts else [],
        }

    def generate_sales_strategy_report(self) -> str:
        llm = _get_llm()
        if llm.available:
            try:
                strategy = llm.generate_strategy({
                    "company": self.company or "未知", "industry": self.industry or "未知",
                    "stage": self._stage, "utterances": len(self._session_log),
                    "emotion": self.psychology._energy.emotion,
                    "compliance_score": self.psychology.compliance_score,
                    "history": [s.get("input", "") for s in self._session_log],
                })
                risk = strategy.get("risk_warning", "")
                readiness = strategy.get("deal_readiness", 0)
                next_action = strategy.get("next_action", "跟进")
            except Exception:
                risk, readiness, next_action = "", 0, "跟进"
        else:
            risk, readiness, next_action = "", 0, "跟进"

        lines = [
            "## 销售策略报告", "",
            "**客户**: " + (self.company if self.company else "未知"),
            "**行业**: " + (self.industry if self.industry else "未知"),
            "**阶段**: " + self._stage, "",
            "### 心理博弈状态",
            "- 服从性阶梯完成度: " + f"{self.psychology.compliance_score:.0%}",
            "- 当前情绪: " + self.psychology._energy.emotion,
            "- 犹豫信号: " + str(len(self.psychology._energy.hesitation_signals)) + "次", "",
        ]
        if self.multithread._contacts:
            for name, c in self.multithread._contacts.items():
                lines.append(f"- {name} ({c.role.value}) 关系:{c.relationship:.0%} 决策权:{c.decision_power:.0%}")
        else:
            lines.append("- 尚未建立联系人图谱")
        lines.extend([
            "", "### 价值等式状态",
            "- 客户感知价值: " + f"{self.consultant.value_equation.perceived_value:.0%}",
            "- 价格抗拒: " + f"{self.consultant.value_equation.price_resistance:.0%}",
            "- 等值平衡: " + ("是" if self.consultant.value_equation.is_balanced else "否"), "",
            "### A/B测试建议", self.evolver.suggest_ab_test(),
        ])
        text = "\n".join(lines)

        # Reporter 自动汇报（HTTP / CLI 双模式）
        try:
            _tianlong_report_highlight(
                title="销售策略报告: " + (self.company or "未知"),
                body=text,
                highlights=[
                    "服从性阶梯完成度: " + f"{self.psychology.compliance_score:.0%}",
                    "价值等式: " + ("平衡" if self.consultant.value_equation.is_balanced else "不平衡"),
                    "联系人: " + str(len(self.multithread._contacts)) + "个",
                ],
                action_items=["审阅销售策略", "检查价值等式是否需要调整"],
            )
        except Exception:
            pass
        return text
