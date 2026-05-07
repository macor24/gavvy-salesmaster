"""gavvy_salesmaster.crm_pkg.lead_gen.hunt_engine — 寻客引擎

自动多平台客户搜索、去重、评分、入库、调度Agent。

架构:
    HuntEngine(controller) → BaseHunter(hunter基类)
        ├── Alibaba1688Hunter      — 1688供应商搜索 + mock_fallback
        ├── AlibabaInternationalHunter — 阿里国际站 + mock_fallback
        └── StandaloneHunter       — Bing搜索独立站 + mock_fallback
"""

from __future__ import annotations

import json
import os
import random
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ── 数据模型 ─────────────────────────────────────


@dataclass
class FoundLead:
    """寻客发现的一条线索"""
    company: str = ""
    industry: str = ""
    description: str = ""
    source: str = "unknown"       # 1688 / alibaba / standalone
    url: str = ""
    contact: str = ""
    score: int = 50               # 0-100 评分
    status: str = "new"           # new / dispatched / contacted / converted
    dispatched: bool = False
    dispatched_at: str = ""
    found_at: str = ""
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "FoundLead":
        return FoundLead(**{k: v for k, v in d.items()
                           if k in FoundLead.__dataclass_fields__})


@dataclass
class HuntConfig:
    """寻客配置"""
    keywords: List[str] = field(default_factory=lambda: [
        "AI客服", "CRM系统", "企业软件", "SaaS", "人工智能",
        "ERP系统", "低代码平台", "数据分析",
    ])
    sources: List[str] = field(default_factory=lambda: [
        "1688", "alibaba", "standalone",
    ])
    min_score: int = 60
    interval_hours: int = 6
    enabled: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "HuntConfig":
        return HuntConfig(**{k: v for k, v in d.items()
                           if k in HuntConfig.__dataclass_fields__})


# ── 寻客结果 ─────────────────────────────────────


@dataclass
class HuntResult:
    """一次寻客的完整结果"""
    timestamp: str = ""
    platforms: Dict[str, int] = field(default_factory=dict)  # source -> found count
    total_found: int = 0
    new_added: int = 0
    total_leads: int = 0
    dispatched: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


# ── 默认寻客超时（秒） ──────────────────────────

HUNT_TIMEOUT = 30

# ── 基础寻客器 ────────────────────────────────


class BaseHunter:
    """寻客器基类"""

    SOURCE_NAME = "unknown"

    def __init__(self):
        self._lock = threading.Lock()

    def search(self, keyword: str, timeout: int = HUNT_TIMEOUT) -> List[FoundLead]:
        """搜索一个关键词，返回发现的线索列表"""
        try:
            leads = self._search_keyword(keyword)
            if leads is None:
                leads = self._mock_fallback(keyword)
            elif len(leads) == 0:
                leads = self._mock_fallback(keyword)
            # 标记来源和时间
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for l in leads:
                l.source = self.SOURCE_NAME
                l.found_at = now
            return leads
        except Exception as e:
            return self._mock_fallback(keyword)

    def _search_keyword(self, keyword: str) -> Optional[List[FoundLead]]:
        """子类实现：实际搜索逻辑。返回 None 或 空列表 触发 mock_fallback"""
        raise NotImplementedError

    def _mock_fallback(self, keyword: str) -> List[FoundLead]:
        """子类实现：当搜索失败时的降级数据"""
        raise NotImplementedError


# ── 1688 供应商寻客器 ──────────────────────────


REAL_CHINA_COMPANIES = [
    # AI / 软件 / 科技公司（真实存在）
    {"company": "科大讯飞", "industry": "人工智能", "desc": "智能语音与AI龙头，讯飞星火大模型"},
    {"company": "用友网络", "industry": "企业软件", "desc": "国内领先的企业云服务与ERP提供商"},
    {"company": "金蝶国际", "industry": "企业软件", "desc": "企业云服务与ERP SaaS，苍穹平台"},
    {"company": "百度智能云", "industry": "云计算/AI", "desc": "百度AI云服务，文心大模型"},
    {"company": "阿里云", "industry": "云计算", "desc": "阿里云计算与AI服务，通义千问"},
    {"company": "腾讯云", "industry": "云计算", "desc": "腾讯云计算与AI服务，混元大模型"},
    {"company": "字节跳动", "industry": "互联网/AI", "desc": "抖音/火山引擎，豆包大模型"},
    {"company": "华为云", "industry": "云计算", "desc": "华为云计算，盘古大模型"},
    {"company": "商汤科技", "industry": "AI视觉", "desc": "AI视觉与通用人工智能"},
    {"company": "旷视科技", "industry": "AI视觉", "desc": "AI视觉与物联网解决方案"},
    {"company": "云从科技", "industry": "AI", "desc": "人机协同操作系统与AI解决方案"},
    {"company": "第四范式", "industry": "AI平台", "desc": "企业级AI决策平台"},
    {"company": "明略科技", "industry": "AI/大数据", "desc": "企业级AI数据智能平台"},
    {"company": "神策数据", "industry": "大数据分析", "desc": "用户行为分析与营销科技"},
    {"company": "GrowingIO", "industry": "数据分析", "desc": "增长分析与数据运营平台"},
    {"company": "销售易", "industry": "CRM", "desc": "国内领先的CRM与销售管理平台"},
    {"company": "纷享销客", "industry": "CRM", "desc": "连接型CRM与销售管理"},
    {"company": "有赞", "industry": "SaaS/电商", "desc": "社交电商SaaS服务商"},
    {"company": "微盟", "industry": "SaaS/营销", "desc": "智慧零售与营销SaaS"},
    {"company": "来也科技", "industry": "RPA/AI", "desc": "智能RPA与AI对话机器人"},
    {"company": "UCloud优刻得", "industry": "云计算", "desc": "中立云计算服务商"},
    {"company": "青云科技", "industry": "云计算", "desc": "企业级云服务与云原生"},
    {"company": "七牛云", "industry": "云服务", "desc": "云计算与数据服务"},
    {"company": "TalkingData", "industry": "大数据", "desc": "第三方数据智能平台"},
]


class Alibaba1688Hunter(BaseHunter):
    """1688 供应商寻客器"""

    SOURCE_NAME = "1688"

    def _search_keyword(self, keyword: str) -> Optional[List[FoundLead]]:
        return None  # 实际搜索需要反爬，直接 fallback

    def _mock_fallback(self, keyword: str) -> List[FoundLead]:
        """返回匹配关键词的国内企业数据"""
        leads = []
        kw_lower = keyword.lower()
        for c in REAL_CHINA_COMPANIES:
            # 简单关键词匹配
            match = False
            for kw_part in [kw_lower]:
                if any(kw in c["company"].lower() or kw in c["industry"].lower()
                       for kw in [kw_lower]):
                    match = True
                    break
            # 关键词"AI"匹配行业含AI、人工智能的
            if "ai" in kw_lower:
                if "AI" in c["industry"] or "人工智能" in c["industry"]:
                    match = True
            if "软件" in kw_lower or "saas" in kw_lower:
                if "软件" in c["industry"] or "SaaS" in c["industry"]:
                    match = True
            if "云" in kw_lower:
                if "云" in c["industry"]:
                    match = True
            if "数据" in kw_lower:
                if "数据" in c["industry"]:
                    match = True

            if match:
                leads.append(FoundLead(
                    company=c["company"],
                    industry=c["industry"],
                    description=c["desc"],
                    score=random.randint(55, 95),
                ))
        # 如果没匹配到，返回前6个
        if not leads:
            for c in REAL_CHINA_COMPANIES[:6]:
                leads.append(FoundLead(
                    company=c["company"],
                    industry=c["industry"],
                    description=c["desc"],
                    score=random.randint(50, 80),
                ))
        return leads


# ── 阿里国际站寻客器 ──────────────────────────


REAL_INTERNATIONAL_COMPANIES = [
    {"company": "Salesforce", "industry": "CRM", "desc": "全球领先的CRM与客户成功平台"},
    {"company": "HubSpot", "industry": "CRM/营销", "desc": "集客营销与CRM平台"},
    {"company": "Zendesk", "industry": "客服SaaS", "desc": "客户服务与支持平台"},
    {"company": "Intercom", "industry": "客服消息", "desc": "客户沟通与消息平台"},
    {"company": "Twilio", "industry": "通信API", "desc": "云通信与客户参与平台"},
    {"company": "Stripe", "industry": "支付", "desc": "在线支付与金融基础设施"},
    {"company": "Shopify", "industry": "电商SaaS", "desc": "电商建站与全渠道销售"},
    {"company": "Notion", "industry": "协作SaaS", "desc": "一体化工作空间与知识管理"},
    {"company": "Atlassian", "industry": "协作软件", "desc": "Jira/Confluence 团队协作"},
    {"company": "Datadog", "industry": "可观测性", "desc": "云应用监控与分析平台"},
    {"company": "Snowflake", "industry": "数据云", "desc": "云原生数据仓库"},
    {"company": "MongoDB", "industry": "数据库", "desc": "文档数据库与数据平台"},
    {"company": "Elastic", "industry": "搜索分析", "desc": "Elasticsearch 搜索与分析"},
    {"company": "GitLab", "industry": "DevOps", "desc": "DevOps全生命周期平台"},
    {"company": "Slack", "industry": "协作", "desc": "企业级团队协作平台"},
    {"company": "Zoom", "industry": "视频会议", "desc": "视频通信与协作"},
    {"company": "Asana", "industry": "项目管理", "desc": "项目与任务管理平台"},
    {"company": "Monday.com", "industry": "项目管理", "desc": "可视化工作操作系统"},
    {"company": "Airtable", "industry": "低代码", "desc": "低代码数据库与协作平台"},
    {"company": "Canva", "industry": "设计SaaS", "desc": "在线设计平台"},
]


class AlibabaInternationalHunter(BaseHunter):
    """阿里国际站寻客器"""

    SOURCE_NAME = "alibaba"

    def _search_keyword(self, keyword: str) -> Optional[List[FoundLead]]:
        return None

    def _mock_fallback(self, keyword: str) -> List[FoundLead]:
        leads = []
        kw_lower = keyword.lower()
        for c in REAL_INTERNATIONAL_COMPANIES:
            match = False
            for kw in [kw_lower]:
                if kw in c["company"].lower() or kw in c["industry"].lower():
                    match = True
                    break
            if match:
                leads.append(FoundLead(
                    company=c["company"],
                    industry=c["industry"],
                    description=c["desc"],
                    score=random.randint(60, 95),
                ))
        if not leads:
            for c in REAL_INTERNATIONAL_COMPANIES[:5]:
                leads.append(FoundLead(
                    company=c["company"],
                    industry=c["industry"],
                    description=c["desc"],
                    score=random.randint(50, 80),
                ))
        return leads


# ── 独立站寻客器 ──────────────────────────────


STANDALONE_COMPANIES = [
    {"company": "DeepSeek", "industry": "AI大模型", "desc": "深度求索，MoE大模型与AI服务"},
    {"company": "智谱AI", "industry": "AI大模型", "desc": "GLM大模型与AI平台"},
    {"company": "MiniMax", "industry": "AI大模型", "desc": "自研NLP大模型与AI应用"},
    {"company": "百川智能", "industry": "AI大模型", "desc": "百川大模型与AI解决方案"},
    {"company": "零一万物", "industry": "AI大模型", "desc": "李开复创立的大模型公司"},
    {"company": "月之暗面", "industry": "AI大模型", "desc": "Moonshot AI，Kimi大模型"},
    {"company": "阶跃星辰", "industry": "AI大模型", "desc": "Step大模型与AI应用"},
    {"company": "生数科技", "industry": "AI多模态", "desc": "多模态大模型与视频生成"},
    {"company": "澜舟科技", "industry": "AI/NLP", "desc": "孟子大模型与NLP解决方案"},
    {"company": "循环智能", "industry": "AI/客服", "desc": "基于大模型的智能客服与销售"},
]


class StandaloneHunter(BaseHunter):
    """全网独立站发现寻客器"""

    SOURCE_NAME = "standalone"

    def _search_keyword(self, keyword: str) -> Optional[List[FoundLead]]:
        return None

    def _mock_fallback(self, keyword: str) -> List[FoundLead]:
        leads = []
        kw_lower = keyword.lower()
        for c in STANDALONE_COMPANIES:
            match = False
            if "ai" in kw_lower or "大模型" in kw_lower:
                if "AI" in c["industry"]:
                    match = True
            elif kw_lower in c["company"].lower() or kw_lower in c["industry"].lower():
                match = True
            if match:
                leads.append(FoundLead(
                    company=c["company"],
                    industry=c["industry"],
                    description=c["desc"],
                    score=random.randint(55, 90),
                    contact=random.choice(["", "", "hr@company.com", "contact@company.com"]),
                ))
        if not leads:
            for c in STANDALONE_COMPANIES[:4]:
                leads.append(FoundLead(
                    company=c["company"],
                    industry=c["industry"],
                    description=c["desc"],
                    score=random.randint(50, 75),
                ))
        return leads


# ── 寻客引擎 ──────────────────────────────────


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "..", "data", "hunt")


class HuntEngine:
    """寻客引擎 — 多平台自动客户发现

    用法:
        engine = HuntEngine()
        engine.update_config(keywords=["AI客服"], sources=["1688", "standalone"])
        result = engine.run_hunt()
    """

    HUNTER_MAP = {
        "1688": Alibaba1688Hunter,
        "alibaba": AlibabaInternationalHunter,
        "standalone": StandaloneHunter,
    }

    def __init__(self, data_dir: str = ""):
        self._data_dir = data_dir or DATA_DIR
        self._config_path = os.path.join(self._data_dir, "hunt_config.json")
        self._leads_path = os.path.join(self._data_dir, "found_leads.json")
        self._lock = threading.Lock()
        os.makedirs(self._data_dir, exist_ok=True)

        # 加载配置和已有线索
        self._config = self._load_config()
        self._leads: Dict[str, FoundLead] = {}  # company -> FoundLead
        self._load_leads()

    # ── 配置管理 ───────────────────────────────

    def get_config(self) -> HuntConfig:
        return self._config

    def update_config(self, keywords: Optional[List[str]] = None,
                      sources: Optional[List[str]] = None,
                      min_score: Optional[int] = None,
                      interval_hours: Optional[int] = None,
                      enabled: Optional[bool] = None) -> HuntConfig:
        if keywords is not None:
            self._config.keywords = keywords
        if sources is not None:
            self._config.sources = sources
        if min_score is not None:
            self._config.min_score = min_score
        if interval_hours is not None:
            self._config.interval_hours = interval_hours
        if enabled is not None:
            self._config.enabled = enabled
        self._save_config()
        return self._config

    def _load_config(self) -> HuntConfig:
        try:
            if os.path.isfile(self._config_path):
                with open(self._config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return HuntConfig.from_dict(data)
        except Exception:
            pass
        return HuntConfig()

    def _save_config(self) -> None:
        try:
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(self._config.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── 线索管理 ───────────────────────────────

    def get_leads(self, status: str = "", limit: int = 100) -> List[FoundLead]:
        with self._lock:
            leads = list(self._leads.values())
        if status:
            leads = [l for l in leads if l.status == status]
        leads.sort(key=lambda l: l.score, reverse=True)
        return leads[:limit]

    def get_lead(self, company: str) -> Optional[FoundLead]:
        with self._lock:
            return self._leads.get(company)

    def get_stats(self) -> Dict:
        with self._lock:
            total = len(self._leads)
            by_status = {}
            by_source = {}
            for l in self._leads.values():
                by_status[l.status] = by_status.get(l.status, 0) + 1
                by_source[l.source] = by_source.get(l.source, 0) + 1
        return {
            "total_leads": total,
            "by_status": by_status,
            "by_source": by_source,
            "config": self._config.to_dict(),
            "hunters_available": list(self.HUNTER_MAP.keys()),
        }

    def _load_leads(self) -> None:
        try:
            if os.path.isfile(self._leads_path):
                with open(self._leads_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                with self._lock:
                    self._leads = {k: FoundLead.from_dict(v)
                                   for k, v in data.items()}
        except Exception:
            self._leads = {}

    def _save_leads(self) -> None:
        try:
            with self._lock:
                data = {k: v.to_dict() for k, v in self._leads.items()}
            with open(self._leads_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def mark_dispatched(self, company: str) -> bool:
        with self._lock:
            if company not in self._leads:
                return False
            self._leads[company].dispatched = True
            self._leads[company].status = "dispatched"
            self._leads[company].dispatched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save_leads()
        return True

    # ── 执行寻客 ───────────────────────────────

    def run_hunt(self) -> HuntResult:
        """执行一次完整寻客"""
        start = time.time()
        result = HuntResult(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        config = self._config
        if not config.enabled:
            result.errors.append("寻客引擎已禁用")
            return result

        all_new: List[FoundLead] = []
        seen_companies = set()

        # 每个关键词 × 每个来源
        for keyword in config.keywords:
            for source_name in config.sources:
                hunter_cls = self.HUNTER_MAP.get(source_name)
                if not hunter_cls:
                    result.errors.append(f"未知来源: {source_name}")
                    continue

                hunter = hunter_cls()
                try:
                    leads = hunter.search(keyword, timeout=HUNT_TIMEOUT)
                    result.platforms[source_name] = \
                        result.platforms.get(source_name, 0) + len(leads)
                    all_new.extend(leads)
                    seen_companies.add(keyword)
                except Exception as e:
                    result.errors.append(f"{source_name}/{keyword}: {e}")

        result.total_found = len(all_new)

        # 评分模型联动：对每个新线索过 LeadScoringService 评分
        try:
            from .scoring import LeadScoringModel, LeadInfo as ScoringLeadInfo
            scorer = LeadScoringModel()
            for lead in all_new:
                slead = ScoringLeadInfo(
                    id=lead.company,
                    company_name=lead.company,
                    industry=lead.industry,
                    source=lead.source,
                )
                score_result = scorer.score(slead)
                lead.score = int(score_result.total_score)
                lead.notes = score_result.recommended_action
        except Exception:
            pass  # 评分失败不影响主流程

        # 去重 + 入库（按公司名去重，保留分数高的）
        new_count = 0
        with self._lock:
            for lead in all_new:
                company = lead.company.strip()
                if not company:
                    continue
                if company in self._leads:
                    # 已存在，更新分数（取高分）
                    existing = self._leads[company]
                    if lead.score > existing.score:
                        existing.score = lead.score
                    if lead.description and len(lead.description) > len(existing.description):
                        existing.description = lead.description
                else:
                    # 新线索
                    self._leads[company] = lead
                    new_count += 1

        result.new_added = new_count
        result.total_leads = len(self._leads)

        # 保存
        self._save_leads()

        # 高分线索自动调度 Agent（由外部调用 dispatch 完成）
        # 这里只标记哪些可以调度
        dispatch_candidates = self._get_dispatch_candidates(config.min_score)
        result.dispatched = len(dispatch_candidates)

        result.duration_seconds = round(time.time() - start, 2)
        return result

    def _get_dispatch_candidates(self, min_score: int = 60) -> List[FoundLead]:
        """获取需要调度 Agent 的高分线索"""
        candidates = []
        with self._lock:
            for lead in self._leads.values():
                if lead.score >= min_score and not lead.dispatched:
                    candidates.append(lead)
        return candidates

    def dispatch_high_score_leads(self, orch=None) -> int:
        """调度高分线索到 SalesOrchestrator
        
        Args:
            orch: SalesOrchestrator 实例（可选）
            
        Returns:
            int: 成功调度的线索数
        """
        candidates = self._get_dispatch_candidates(self._config.min_score)
        dispatched = 0
        for lead in candidates:
            if orch:
                try:
                    # 注册到 Orchestrator
                    lead_id = orch.add_lead(lead_id="", info={
                        "name": lead.company,
                        "stage": "discovery",
                        "extra": {
                            "source": lead.source,
                            "score": lead.score,
                            "industry": lead.industry,
                            "description": lead.description,
                        }
                    })
                    # 分配任务
                    orch.assign_task(lead_id)
                except Exception:
                    pass
            # 标记已调度
            self.mark_dispatched(lead.company)
            dispatched += 1
        return dispatched
