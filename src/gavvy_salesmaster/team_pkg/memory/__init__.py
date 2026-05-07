"""gavvy_salesmaster.team_pkg.memory — 学习记忆系统

企业版通过服务端 API 提供完整记忆库（需 SentriKit_API_KEY）。
社区版使用本地简化存储。
"""

from __future__ import annotations

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from gavvy_salesmaster.core.enterprise_client import EnterpriseAPIClient, EnterpriseConfig, UPGRADE_HINT


# ── 企业版检测 ──────────────────────────────────

_HAS_ENTERPRISE = False
_ENTERPRISE_IMPORT_ERROR = ""

_cfg = EnterpriseConfig.from_env()
_HAS_ENTERPRISE = _cfg.is_enterprise
if not _cfg.is_enterprise:
    _ENTERPRISE_IMPORT_ERROR = "社区版模式（无 SentriKit_API_KEY），使用本地简化存储"


# ── 社区版本地存储（简化版） ──────────────────


class MemoryKernel:
    """社区版简化记忆内核（基于 JSON 文件）"""

    def __init__(self, base_dir: str = ""):
        self._base = Path(base_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "memory"
        ))
        self._base.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, name: str) -> Any:
        with self._lock:
            if name in self._cache:
                return self._cache[name]
            path = self._base / f"{name}.json"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                self._cache[name] = data
                return data
            return {}

    def write(self, name: str, data: Any) -> None:
        with self._lock:
            self._cache[name] = data
            path = self._base / f"{name}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


class MemoryStore:
    """社区版简化记忆存储"""

    def __init__(self, kernel: Optional[MemoryKernel] = None):
        self._kernel = kernel or MemoryKernel()
        self._edition = "community"

    def get_stats(self) -> Dict:
        return {
            "edition": self._edition,
            "hint": UPGRADE_HINT.strip()[:50] + "...",
        }

    def list_insights(self) -> List:
        return []

    def list_skills(self) -> List:
        return []

    def list_patterns(self) -> List:
        return []

    def list_episodes(self, limit: int = 100) -> List:
        return []

    def list_rules(self) -> List:
        return []

    def get_performance(self, agent_name: str) -> Dict:
        return {}


class Learner:
    """社区版简化学习者 — 记录销售执行数据到本地存储"""

    def __init__(self, kernel: Optional[MemoryKernel] = None):
        self._kernel = kernel or MemoryKernel()

    def learn_from_result(self, agent_name: str,
                          input_data: Dict,
                          output_data: Dict) -> Dict:
        """从 Agent 执行结果中学习

        - 记录执行历史到 episodes
        - 按 Agent 汇总统计
        - 识别成功/失败模式
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = output_data.get("status", "unknown")

        # 写入执行记录
        episodes = self._kernel.get("episodes") or []
        episodes.append({
            "agent": agent_name,
            "timestamp": now,
            "status": status,
            "input_summary": input_data.get("message", "")[:60],
            "output_summary": output_data.get("summary", "")[:60],
            "action": output_data.get("action", ""),
        })
        if len(episodes) > 500:
            episodes = episodes[-500:]
        self._kernel.write("episodes", episodes)

        # 更新 Agent 统计
        stats = self._kernel.get("agent_stats") or {}
        if agent_name not in stats:
            stats[agent_name] = {"total": 0, "success": 0, "failed": 0}
        stats[agent_name]["total"] += 1
        if status == "success":
            stats[agent_name]["success"] += 1
        elif status in ("failed", "blocked"):
            stats[agent_name]["failed"] += 1
        self._kernel.write("agent_stats", stats)

        # 桥接到 StrategyEvolver（发现隐藏模式）
        episode = {
            "agent": agent_name,
            "timestamp": now,
            "status": status,
            "input_summary": input_data.get("message", "")[:60],
            "output_summary": output_data.get("summary", "")[:60],
            "action": output_data.get("action", ""),
        }
        hidden_pattern = self._bridge_to_evolver(episode)

        # 回写 lead_gen 评分权重（寻客反馈闭环）
        self._feedback_to_lead_scoring(status, agent_name)

        return {
            "learned": True,
            "episode_count": len(episodes),
            "agent": agent_name,
            "status": status,
            "hidden_pattern": hidden_pattern,
            "hint": "" if _HAS_ENTERPRISE else UPGRADE_HINT.strip()[:50] + "...",
        }

    def _bridge_to_evolver(self, episode: Dict) -> Optional[str]:
        """桥接 episode 到 StrategyEvolver"""
        try:
            from gavvy_salesmaster.core.evolver import learn_to_evolver
            return learn_to_evolver(episode)
        except Exception:
            return None

    @staticmethod
    def _feedback_to_lead_scoring(status: str, agent_name: str) -> None:
        """根据执行反馈回写 lead_gen 评分权重"""
        try:
            from gavvy_salesmaster.crm_pkg.lead_gen.scoring import (
                get_lead_scoring_service,
            )
            service = get_lead_scoring_service()

            # 成功：增加 industry_match 权重（验证了行业选择正确）
            # 失败：减少 industry_match 权重（行业筛选不准）
            if status in ("success", "completed"):
                service.model.adjust_weight("industry_match", 0.01)
                service.model.adjust_weight("engagement", 0.005)
            elif status in ("failed", "blocked"):
                service.model.adjust_weight("industry_match", -0.01)
                service.model.adjust_weight("engagement", -0.005)
        except Exception:
            pass


class SkillEvolver:
    """社区版简化技能进化器"""
    def evolve_all(self) -> Dict:
        return {"evolved": False, "hint": "企业版解锁技能进化"}


# ── 全局实例 ────────────────────────────────────

_global_kernel: Optional[MemoryKernel] = None


def get_memory_dir() -> str:
    return str(MemoryKernel()._base)


def set_memory_dir(path: str) -> None:
    global _global_kernel
    _global_kernel = MemoryKernel(path)


def get_memory_store() -> MemoryStore:
    return MemoryStore(_global_kernel)


def get_learner() -> Learner:
    return Learner()


def get_evolver() -> SkillEvolver:
    return SkillEvolver()


def get_capabilities() -> List[Dict]:
    return [
        {"name": "insight", "label": "销售洞察", "level": 1, "mode": "template" if not _HAS_ENTERPRISE else "llm"},
        {"name": "skill_evolution", "label": "技能进化", "level": 1, "mode": "template" if not _HAS_ENTERPRISE else "llm"},
        {"name": "pattern_recognition", "label": "模式识别", "level": 1, "mode": "template" if not _HAS_ENTERPRISE else "llm"},
    ]


__all__ = [
    "get_memory_dir", "set_memory_dir",
    "MemoryKernel", "MemoryStore", "Learner", "SkillEvolver",
    "get_memory_store", "get_learner", "get_evolver", "get_capabilities",
    "_HAS_ENTERPRISE", "_ENTERPRISE_IMPORT_ERROR",
]
