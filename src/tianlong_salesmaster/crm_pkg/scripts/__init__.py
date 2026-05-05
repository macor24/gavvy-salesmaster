"""tianlong_salesmaster.crm_pkg.scripts — 话术训练系统

销售话术训练引擎，包含：

场景:
  - 首次接触 / 需求挖掘 / 异议处理 / 逼单成交 / 售后维护 / 流失挽回

能力:
  - 话术库管理（场景分类 + 标签 + 版本）
  - 话术评分（手动评分 + AI推荐）
  - 模拟训练（场景对话演练）
  - 话术推荐（根据客户特征推荐最合适的话术）
"""

from __future__ import annotations

import json
import random
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from tianlong_salesmaster.core.storage.db import get_kernel

# ── 集合名称 ──────────────────────────────────────

_COLL_SCRIPTS = "scripts_items"
_COLL_TRAINING = "scripts_training"
_COLL_RATINGS = "scripts_ratings"

# ── 种子场景 ──────────────────────────────────────

SEED_SCENARIOS = {
    "first_contact": {
        "name": "首次接触",
        "icon": "👋",
        "description": "首次与潜在客户沟通，建立信任并了解基本情况",
        "goal": "获取客户基本信息，确认需求方向，建立良好第一印象",
    },
    "need_discovery": {
        "name": "需求挖掘",
        "icon": "🔍",
        "description": "深入了解客户的真实需求和痛点",
        "goal": "明确客户的核心需求、预算范围、决策流程和决策人",
    },
    "objection_handling": {
        "name": "异议处理",
        "icon": "🤔",
        "description": "处理客户的疑虑、价格异议、信任问题等",
        "goal": "有效消除客户顾虑，将异议转化为成交机会",
    },
    "closing": {
        "name": "逼单成交",
        "icon": "🎯",
        "description": "识别成交信号，推动客户做决策",
        "goal": "引导客户做出购买决定，完成成交",
    },
    "after_sales": {
        "name": "售后维护",
        "icon": "🤝",
        "description": "售后跟进、客户满意度、复购引导",
        "goal": "提升客户满意度，挖掘增值和复购机会",
    },
    "churn_recovery": {
        "name": "流失挽回",
        "icon": "🔄",
        "description": "挽回将要流失或已流失的客户",
        "goal": "了解流失原因，重新建立客户关系",
    },
}

# ── 种子话术模板 ──────────────────────────────────

SEED_SCRIPTS = [
    {
        "scenario": "first_contact",
        "title": "开场白 — 价值前置",
        "content": "您好，我是{company}的{name}。了解到您在{industry}行业深耕多年，我们在帮助同类型企业{benefit}方面有丰富的经验。想占用您3分钟，介绍一下我们的解决方案，看是否对您有帮助？",
        "tags": ["开场白", "价值前置"],
        "tips": "开场要突出对客户的价值而非介绍自己",
    },
    {
        "scenario": "first_contact",
        "title": "开场白 — 痛点切入",
        "content": "您好，我是{company}的{name}。最近和不少{industry}行业的同行交流，他们普遍反映{pain_point}是最大的痛点。您这边是否也有类似的困扰？",
        "tags": ["开场白", "痛点切入"],
        "tips": "用行业共性痛点建立共鸣，降低客户防备",
    },
    {
        "scenario": "need_discovery",
        "title": "需求探索 — SPIN追问法",
        "content": "您刚才提到的这个问题，目前是怎么处理的？\n\n（倾听后追问）如果这个问题持续存在，对您团队的影响有多大？\n\n假如有一个方案能解决这个问题，您最看重哪些方面？",
        "tags": ["SPIN", "需求深入"],
        "tips": "遵循 现状→问题→影响→需求 的提问逻辑",
    },
    {
        "scenario": "need_discovery",
        "title": "预算探测",
        "content": "像这样体量的项目，您预期的投入大概在什么范围？我这边可以根据预算为您匹配最合适的产品方案。",
        "tags": ["预算", "需求确认"],
        "tips": "先提供价值再问预算，不要让客户觉得你在试探",
    },
    {
        "scenario": "objection_handling",
        "title": "价格异议 — 价值对比",
        "content": "我理解您的顾虑。表面上看我们的价格比同类高一些，但实际上我们的产品包含了{a}、{b}、{c}三项独家功能。按年计算，每天的成本其实只有{price_per_day}元，而它能帮您每天节省{time_save}小时的工作量。",
        "tags": ["价格异议", "价值量化"],
        "tips": "将年费拆解到天，让数字无感化；强调ROI而非价格",
    },
    {
        "scenario": "objection_handling",
        "title": "竞品对比 — 差异化优势",
        "content": "您提到的{competitor}确实是一个不错的选择。我帮您客观分析一下两者的差异：他们有{a}方面的优势，而我们强在{b}。考虑到您的核心需求是{need}，我们的方案匹配度会更高。",
        "tags": ["竞品", "对比话术"],
        "tips": "先肯定竞品建立信任，再用差异化匹配客户需求",
    },
    {
        "scenario": "objection_handling",
        "title": "推迟处理的应对",
        "content": "完全理解您现在手头事情多。不过根据我们服务过的同类型企业来看，早一个月处理这个问题的客户，平均多创造了{revenue}的收益。我可以先发一份资料给您，5分钟就能看完，不影响您的工作节奏。",
        "tags": ["推迟", "紧迫感"],
        "tips": "不要催客户，用数据说明尽早行动的价值",
    },
    {
        "scenario": "closing",
        "title": "假设成交法",
        "content": "如果我们要开始合作的话，您这边希望我们什么时候完成部署？是选择月度方案还是年度方案？",
        "tags": ["逼单", "假设成交"],
        "tips": "跳过\"要不要\"，直接问\"怎么做\"，引导客户进入决策后的场景",
    },
    {
        "scenario": "closing",
        "title": "限时优惠逼单",
        "content": "这个优惠方案是到{deadline}截止的。如果今天确定的话，我还能额外帮您申请一个{bonus}。错过的话下次活动可能要等{next_time}了。",
        "tags": ["逼单", "限时优惠"],
        "tips": "优惠要真实有据，不要虚假紧迫感",
    },
    {
        "scenario": "closing",
        "title": "风险逆转法",
        "content": "我建议您可以先试用{free_trial_period}，试用期内不满意随时可以取消。这期间我全程陪跑，确保您快速看到效果。您看这样风险是不是就小很多了？",
        "tags": ["逼单", "风险逆转"],
        "tips": "降低客户的决策风险是最高效的成交方式",
    },
    {
        "scenario": "after_sales",
        "title": "活跃跟进 — 价值确认",
        "content": "您好，我们的产品使用得还顺利吗？最近我们有新的{new_feature}功能上线，对{benefit}非常有帮助，我给您做个简短的演示？",
        "tags": ["售后", "复购"],
        "tips": "定期回顾价值，让客户感受到持续服务",
    },
    {
        "scenario": "after_sales",
        "title": "复购引导",
        "content": "看到您对我们的产品体验不错，目前有一个升级方案，在现有功能基础上增加了{a}和{b}，很多老客户升级后效率提升了{c}%。作为老客户，您可以享受{d}的专属优惠。",
        "tags": ["复购", "升级"],
        "tips": "用老客户案例数据说话，专属优惠增强信任",
    },
    {
        "scenario": "churn_recovery",
        "title": "流失原因了解",
        "content": "您好，看到您最近没有继续使用我们的产品了。非常希望能了解一下原因，是我们做得不够好，还是产品不适合您的需求？您的反馈对我们改进非常重要。",
        "tags": ["流失", "原因了解"],
        "tips": "态度真诚，不要辩驳，先收集真实反馈",
    },
    {
        "scenario": "churn_recovery",
        "title": "挽回方案",
        "content": "基于您的使用情况，我这边有一个针对性的方案。之前您遇到{issue}的问题，我们已经做了优化。另外我们新增了{new_feature}功能，应该正好能解决您的需求。我给您免费开通试用一个月，您看是否方便我给您演示一下？",
        "tags": ["流失", "挽回"],
        "tips": "先解决问题再推方案，挽回比新客成本低5倍",
    },
]


# ═══════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════

@dataclass
class Script:
    """话术"""
    id: str = ""
    scenario: str = ""           # 场景ID
    title: str = ""
    content: str = ""            # 话术正文
    tags: List[str] = field(default_factory=list)
    tips: str = ""               # 使用技巧
    scenario_name: str = ""      # 场景中文名
    avg_rating: float = 0.0      # 平均评分
    rating_count: int = 0        # 评分次数
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"sp_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not self.scenario_name and self.scenario:
            sc = SEED_SCENARIOS.get(self.scenario, {})
            self.scenario_name = sc.get("name", self.scenario)

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> Script:
        return Script(**{k: v for k, v in d.items()
                         if k in Script.__dataclass_fields__})


@dataclass
class TrainingSession:
    """训练会话"""
    id: str = ""
    scenario: str = ""
    state: str = "active"        # active / completed / cancelled
    messages: List[Dict] = field(default_factory=list)
    current_script_id: str = ""  # 当前使用的话术
    score: int = 0
    feedback: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"tr_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Rating:
    """话术评分"""
    id: str = ""
    script_id: str = ""
    score: int = 3              # 1-5
    comment: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"rt_{uuid.uuid4().hex[:10]}"
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════
# 话术训练引擎
# ═══════════════════════════════════════════════════════

class ScriptsEngine:
    """话术训练引擎"""

    def __init__(self):
        self._kernel = get_kernel()
        self._ensure_seeds()

    def _get_all(self, coll: str) -> List[Dict]:
        data = self._kernel.get(coll)
        return data if isinstance(data, list) else []

    def _save_all(self, coll: str, data: List[Dict]) -> None:
        self._kernel.write(coll, data)

    def _find_index(self, coll: str, item_id: str) -> int:
        items = self._get_all(coll)
        for i, item in enumerate(items):
            if item.get("id") == item_id:
                return i
        return -1

    def _ensure_seeds(self) -> None:
        """初始化种子话术"""
        items = self._get_all(_COLL_SCRIPTS)
        if len(items) > 0:
            return
        for s in SEED_SCRIPTS:
            script = Script(
                scenario=s["scenario"],
                title=s["title"],
                content=s["content"],
                tags=s.get("tags", []),
                tips=s.get("tips", ""),
            )
            items.append(script.to_dict())
        self._save_all(_COLL_SCRIPTS, items)

    # ── 场景 ──

    def list_scenarios(self) -> List[Dict]:
        result = []
        for sid, sc in SEED_SCENARIOS.items():
            count = sum(1 for s in self._get_all(_COLL_SCRIPTS)
                        if s.get("scenario") == sid)
            result.append({
                "id": sid,
                "name": sc["name"],
                "icon": sc["icon"],
                "description": sc["description"],
                "goal": sc["goal"],
                "script_count": count,
            })
        return result

    def get_scenario(self, scenario_id: str) -> Optional[Dict]:
        sc = SEED_SCENARIOS.get(scenario_id)
        if not sc:
            return None
        count = sum(1 for s in self._get_all(_COLL_SCRIPTS)
                    if s.get("scenario") == scenario_id)
        return {"id": scenario_id, **sc, "script_count": count}

    # ── 话术 CRUD ──

    def list_scripts(self, scenario: str = "", tag: str = "",
                     sort: str = "rating") -> List[Dict]:
        items = self._get_all(_COLL_SCRIPTS)
        if scenario:
            items = [s for s in items if s.get("scenario") == scenario]
        if tag:
            items = [s for s in items if tag in s.get("tags", [])]
        if sort == "rating":
            items.sort(key=lambda s: s.get("avg_rating", 0), reverse=True)
        elif sort == "newest":
            items.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        return items

    def get_script(self, script_id: str) -> Optional[Dict]:
        idx = self._find_index(_COLL_SCRIPTS, script_id)
        if idx < 0:
            return None
        return self._get_all(_COLL_SCRIPTS)[idx]

    def add_script(self, script: Script) -> Dict:
        items = self._get_all(_COLL_SCRIPTS)
        items.append(script.to_dict())
        self._save_all(_COLL_SCRIPTS, items)
        return script.to_dict()

    def update_script(self, script_id: str, updates: Dict) -> Optional[Dict]:
        idx = self._find_index(_COLL_SCRIPTS, script_id)
        if idx < 0:
            return None
        items = self._get_all(_COLL_SCRIPTS)
        item = items[idx]
        for k in ["title", "content", "tags", "tips", "scenario"]:
            if k in updates and updates[k] is not None:
                item[k] = updates[k]
        item["updated_at"] = datetime.now().isoformat()
        if item.get("scenario"):
            sc = SEED_SCENARIOS.get(item["scenario"], {})
            item["scenario_name"] = sc.get("name", item["scenario"])
        items[idx] = item
        self._save_all(_COLL_SCRIPTS, items)
        return item

    def delete_script(self, script_id: str) -> bool:
        idx = self._find_index(_COLL_SCRIPTS, script_id)
        if idx < 0:
            return False
        items = self._get_all(_COLL_SCRIPTS)
        items.pop(idx)
        self._save_all(_COLL_SCRIPTS, items)
        # 删除关联评分
        ratings = self._get_all(_COLL_RATINGS)
        ratings = [r for r in ratings if r.get("script_id") != script_id]
        self._save_all(_COLL_RATINGS, ratings)
        return True

    def search_scripts(self, query: str) -> List[Dict]:
        q = query.lower().strip()
        if not q:
            return self.list_scripts()
        items = self._get_all(_COLL_SCRIPTS)
        return [s for s in items
                if q in s.get("title", "").lower()
                or q in s.get("content", "").lower()
                or q in " ".join(s.get("tags", [])).lower()
                or q in s.get("scenario_name", "").lower()]

    # ── 评分 ──

    def rate_script(self, script_id: str, score: int,
                    comment: str = "") -> Optional[Dict]:
        if score < 1 or score > 5:
            return None
        idx = self._find_index(_COLL_SCRIPTS, script_id)
        if idx < 0:
            return None

        # 添加评分记录
        rating = Rating(script_id=script_id, score=score, comment=comment)
        ratings = self._get_all(_COLL_RATINGS)
        ratings.append(rating.to_dict())
        self._save_all(_COLL_RATINGS, ratings)

        # 更新话术平均分
        script_ratings = [r for r in ratings if r.get("script_id") == script_id]
        avg = sum(r.get("score", 0) for r in script_ratings) / max(len(script_ratings), 1)
        items = self._get_all(_COLL_SCRIPTS)
        items[idx]["avg_rating"] = round(avg, 1)
        items[idx]["rating_count"] = len(script_ratings)
        self._save_all(_COLL_SCRIPTS, items)

        return items[idx]

    def get_ratings(self, script_id: str = "") -> List[Dict]:
        items = self._get_all(_COLL_RATINGS)
        if script_id:
            items = [r for r in items if r.get("script_id") == script_id]
        return items[::-1]

    # ── 训练会话 ──

    def start_training(self, scenario: str,
                       script_id: str = "") -> Optional[Dict]:
        if scenario not in SEED_SCENARIOS:
            return None
        session = TrainingSession(scenario=scenario)
        if script_id:
            session.current_script_id = script_id
        else:
            # 根据场景自动推荐
            scripts = self.list_scripts(scenario=scenario, sort="rating")
            if scripts:
                session.current_script_id = scripts[0]["id"]
        items = self._get_all(_COLL_TRAINING)
        items.append(session.to_dict())
        self._save_all(_COLL_TRAINING, items)
        return session.to_dict()

    def training_step(self, session_id: str, message: str,
                      role: str = "user") -> Optional[Dict]:
        idx = self._find_index(_COLL_TRAINING, session_id)
        if idx < 0:
            return None
        items = self._get_all(_COLL_TRAINING)
        session = items[idx]
        if session.get("state") != "active":
            return None

        # 添加用户消息
        messages = session.get("messages", [])
        messages.append({
            "role": role,
            "content": message,
            "timestamp": datetime.now().isoformat(),
        })

        # 获取当前话术
        script_content = ""
        script_id = session.get("current_script_id", "")
        if script_id:
            script = self.get_script(script_id)
            if script:
                script_content = script.get("content", "")

        # 生成AI反馈
        feedback = self._generate_feedback(
            scenario=session.get("scenario", ""),
            script_content=script_content,
            user_message=message,
        )
        messages.append({
            "role": "coach",
            "content": feedback,
            "timestamp": datetime.now().isoformat(),
        })

        session["messages"] = messages
        session["updated_at"] = datetime.now().isoformat()
        items[idx] = session
        self._save_all(_COLL_TRAINING, items)
        return {"feedback": feedback, "messages": messages}

    def complete_training(self, session_id: str, score: int = 0,
                          feedback: str = "") -> Optional[Dict]:
        idx = self._find_index(_COLL_TRAINING, session_id)
        if idx < 0:
            return None
        items = self._get_all(_COLL_TRAINING)
        session = items[idx]
        session["state"] = "completed"
        session["score"] = score
        session["feedback"] = feedback
        session["updated_at"] = datetime.now().isoformat()
        items[idx] = session
        self._save_all(_COLL_TRAINING, items)
        return session

    def list_training_sessions(self, scenario: str = "",
                               limit: int = 20) -> List[Dict]:
        items = self._get_all(_COLL_TRAINING)
        if scenario:
            items = [s for s in items if s.get("scenario") == scenario]
        items.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        return items[:limit]

    # ── 话术推荐（根据场景+标签） ──

    def recommend_scripts(self, scenario: str = "",
                          tags: Optional[List[str]] = None,
                          limit: int = 5) -> List[Dict]:
        items = self._get_all(_COLL_SCRIPTS)
        if scenario:
            items = [s for s in items if s.get("scenario") == scenario]
        if tags:
            items = [s for s in items
                     if any(t in s.get("tags", []) for t in tags)]
        items.sort(key=lambda s: s.get("avg_rating", 0), reverse=True)
        return items[:limit]

    # ── AI反馈生成（规则引擎） ──

    def _generate_feedback(self, scenario: str, script_content: str,
                           user_message: str) -> str:
        """基于规则的AI反馈"""
        msg_lower = user_message.lower()
        feedback_parts = []

        # 长度检查
        if len(user_message) < 10:
            feedback_parts.append("💡 回复过短，建议补充更多信息来建立客户信任。")
        elif len(user_message) > 500:
            feedback_parts.append("💡 回复较长，注意不要一次性给客户太多信息，建议分步沟通。")

        # 场景特定检查
        scenario_checks = {
            "first_contact": [
                ("自我介绍" if any(kw in msg_lower for kw in ["您好", "你好", "我是"]) else None,
                 "✅ 有自我介绍"),
                (None if "您" in msg_lower or "你" in msg_lower else None,
                 "💡 建议使用'您'来称呼客户，更显尊重"),
                ("价值" if any(kw in msg_lower for kw in ["帮助", "价值", "解决", "提升"]) else None,
                 "💡 开场后尽快提到你能为客户创造的价值"),
            ],
            "objection_handling": [
                ("先理解再化解" if any(kw in msg_lower for kw in ["理解", "明白", "是的", "确实"]) else None,
                 "💡 处理异议前先表示理解，降低对立感"),
                ("价值量化" if any(kw in msg_lower for kw in ["每天", "每年", "节省", "创造", "ROI"]) else None,
                 "✅ 尝试将价值量化，让客户看到具体收益"),
            ],
            "closing": [
                ("行动号召" if any(kw in msg_lower for kw in ["今天", "现在", "确定", "方案"]) else None,
                 "✅ 有明确的行动号召"),
                ("限时" if any(kw in msg_lower for kw in ["优惠", "截止", "限时", "活动"]) else None,
                 "💡 限时优惠可增加紧迫感，但要确保真实"),
            ],
        }

        checks = scenario_checks.get(scenario, [])
        for keyword, feedback_text in checks:
            if keyword is True:
                feedback_parts.append(feedback_text)
            elif keyword is None:
                feedback_parts.append(feedback_text)
            # keyword为字符串时，匹配到才显示

        # 通用检查
        if "?" in user_message or "？" in user_message:
            feedback_parts.append("✅ 使用提问引导客户思考，非常好")
        if "价格" in msg_lower or "贵" in msg_lower:
            feedback_parts.append("💡 如果客户问价格，建议先强调价值再报价")

        # 话术对比
        if script_content:
            feedback_parts.append(f"\n📖 参考话术：\n{script_content[:300]}")

        if not feedback_parts:
            feedback_parts.append("✅ 回复基本得体，可以尝试加入更多引导性问题")

        return "\n".join(feedback_parts)

    # ── 统计 ──

    def get_stats(self) -> Dict:
        scripts = self._get_all(_COLL_SCRIPTS)
        sessions = self._get_all(_COLL_TRAINING)
        ratings = self._get_all(_COLL_RATINGS)
        active_sessions = sum(1 for s in sessions if s.get("state") == "active")
        completed = sum(1 for s in sessions if s.get("state") == "completed")
        by_scenario = {}
        for s in scripts:
            sc = s.get("scenario", "unknown")
            by_scenario[sc] = by_scenario.get(sc, 0) + 1
        return {
            "total_scripts": len(scripts),
            "total_sessions": len(sessions),
            "active_sessions": active_sessions,
            "completed_sessions": completed,
            "total_ratings": len(ratings),
            "scenarios": len(SEED_SCENARIOS),
            "by_scenario": by_scenario,
        }


def get_scripts_engine() -> ScriptsEngine:
    return ScriptsEngine()
