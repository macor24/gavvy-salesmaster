"""智能寻客模块 - 线索分配系统"""

import random
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from .scoring import ScoredLead, LeadPriority, LeadStatus

class AssignmentStrategy(str, Enum):
    """分配策略"""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCE = "load_balance"
    SKILL_MATCH = "skill_match"
    TERRITORY = "territory"
    RANDOM = "random"

@dataclass
class Salesperson:
    """销售人员"""
    id: str
    name: str
    email: str
    phone: str
    skills: List[str] = None
    territory: str = ""
    max_leads: int = 50
    current_leads: int = 0
    active: bool = True
    
    def __post_init__(self):
        if self.skills is None:
            self.skills = []

@dataclass
class AssignmentRule:
    """分配规则"""
    id: str
    name: str
    strategy: AssignmentStrategy
    conditions: List[Dict] = None
    priority: int = 100
    enabled: bool = True
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []

class AssignmentEngine(ABC):
    """分配引擎抽象基类"""
    
    @abstractmethod
    def assign(self, lead: ScoredLead, salespersons: List[Salesperson]) -> Optional[Salesperson]:
        """分配线索"""
        pass

class RoundRobinEngine(AssignmentEngine):
    """轮询分配引擎"""
    
    def __init__(self):
        self.last_assigned_index = -1
    
    def assign(self, lead: ScoredLead, salespersons: List[Salesperson]) -> Optional[Salesperson]:
        """轮询分配"""
        active_salespersons = [s for s in salespersons if s.active and s.current_leads < s.max_leads]
        
        if not active_salespersons:
            return None
        
        self.last_assigned_index = (self.last_assigned_index + 1) % len(active_salespersons)
        return active_salespersons[self.last_assigned_index]

class LoadBalanceEngine(AssignmentEngine):
    """负载均衡分配引擎"""
    
    def assign(self, lead: ScoredLead, salespersons: List[Salesperson]) -> Optional[Salesperson]:
        """按负载分配"""
        active_salespersons = [s for s in salespersons if s.active and s.current_leads < s.max_leads]
        
        if not active_salespersons:
            return None
        
        # 选择当前线索数最少的销售
        return min(active_salespersons, key=lambda s: s.current_leads)

class SkillMatchEngine(AssignmentEngine):
    """技能匹配分配引擎"""
    
    def assign(self, lead: ScoredLead, salespersons: List[Salesperson]) -> Optional[Salesperson]:
        """按技能匹配分配"""
        active_salespersons = [s for s in salespersons if s.active and s.current_leads < s.max_leads]
        
        if not active_salespersons:
            return None
        
        # 计算技能匹配度
        best_match = None
        best_score = -1
        
        for salesperson in active_salespersons:
            score = self._calculate_match_score(lead, salesperson)
            if score > best_score:
                best_score = score
                best_match = salesperson
        
        return best_match
    
    def _calculate_match_score(self, lead: ScoredLead, salesperson: Salesperson) -> int:
        """计算匹配分数"""
        score = 0
        
        # 行业匹配
        if lead.industry and salesperson.skills:
            for skill in salesperson.skills:
                if skill.lower() in lead.industry.lower():
                    score += 30
        
        # 来源匹配
        if lead.source and salesperson.skills:
            for skill in salesperson.skills:
                if skill.lower() in lead.source.lower():
                    score += 20
        
        # 优先级加权
        priority_weights = {
            LeadPriority.CRITICAL: 50,
            LeadPriority.HIGH: 30,
            LeadPriority.MEDIUM: 20,
            LeadPriority.LOW: 10,
        }
        score += priority_weights.get(lead.priority, 20)
        
        return score

class TerritoryEngine(AssignmentEngine):
    """区域分配引擎"""
    
    def assign(self, lead: ScoredLead, salespersons: List[Salesperson]) -> Optional[Salesperson]:
        """按区域分配"""
        active_salespersons = [s for s in salespersons if s.active and s.current_leads < s.max_leads]
        
        if not active_salespersons:
            return None
        
        # 优先匹配区域
        matched = [s for s in active_salespersons if s.territory and s.territory.lower() in lead.company_name.lower()]
        
        if matched:
            # 在匹配区域中按负载分配
            return min(matched, key=lambda s: s.current_leads)
        
        # 如果没有区域匹配，使用负载均衡
        return min(active_salespersons, key=lambda s: s.current_leads)

class RandomEngine(AssignmentEngine):
    """随机分配引擎"""
    
    def assign(self, lead: ScoredLead, salespersons: List[Salesperson]) -> Optional[Salesperson]:
        """随机分配"""
        active_salespersons = [s for s in salespersons if s.active and s.current_leads < s.max_leads]
        
        if not active_salespersons:
            return None
        
        return random.choice(active_salespersons)

class LeadAssignmentService:
    """线索分配服务"""
    
    def __init__(self):
        self.salespersons: List[Salesperson] = []
        self.rules: List[AssignmentRule] = []
        self.engines = {
            AssignmentStrategy.ROUND_ROBIN: RoundRobinEngine(),
            AssignmentStrategy.LOAD_BALANCE: LoadBalanceEngine(),
            AssignmentStrategy.SKILL_MATCH: SkillMatchEngine(),
            AssignmentStrategy.TERRITORY: TerritoryEngine(),
            AssignmentStrategy.RANDOM: RandomEngine(),
        }
        
        # 初始化默认销售人员
        self._init_default_salespersons()
    
    def _init_default_salespersons(self):
        """初始化默认销售人员"""
        self.salespersons = [
            Salesperson(
                id="sp001",
                name="张伟",
                email="zhangwei@sales.com",
                phone="13800138001",
                skills=["AI", "SaaS", "北京"],
                territory="北京",
                max_leads=50,
                current_leads=12
            ),
            Salesperson(
                id="sp002",
                name="李明",
                email="liming@sales.com",
                phone="13800138002",
                skills=["制造", "自动化", "上海"],
                territory="上海",
                max_leads=50,
                current_leads=18
            ),
            Salesperson(
                id="sp003",
                name="王芳",
                email="wangfang@sales.com",
                phone="13800138003",
                skills=["金融", "银行", "深圳"],
                territory="深圳",
                max_leads=50,
                current_leads=8
            ),
            Salesperson(
                id="sp004",
                name="刘洋",
                email="liuyang@sales.com",
                phone="13800138004",
                skills=["医疗", "健康", "广州"],
                territory="广州",
                max_leads=50,
                current_leads=25
            ),
            Salesperson(
                id="sp005",
                name="陈静",
                email="chenjing@sales.com",
                phone="13800138005",
                skills=["教育", "培训", "杭州"],
                territory="杭州",
                max_leads=50,
                current_leads=15
            ),
        ]
    
    def add_salesperson(self, salesperson: Salesperson):
        """添加销售人员"""
        self.salespersons.append(salesperson)
    
    def update_salesperson(self, salesperson_id: str, **kwargs):
        """更新销售人员"""
        for s in self.salespersons:
            if s.id == salesperson_id:
                for key, value in kwargs.items():
                    setattr(s, key, value)
                break
    
    def add_rule(self, rule: AssignmentRule):
        """添加分配规则"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)
    
    def remove_rule(self, rule_id: str):
        """删除分配规则"""
        self.rules = [r for r in self.rules if r.id != rule_id]
    
    def assign_lead(self, lead: ScoredLead, strategy: Optional[AssignmentStrategy] = None) -> Optional[str]:
        """分配线索"""
        # 选择分配策略
        if strategy is None:
            # 使用最高优先级的规则
            enabled_rules = [r for r in self.rules if r.enabled]
            if enabled_rules:
                strategy = enabled_rules[0].strategy
            else:
                # 默认使用负载均衡
                strategy = AssignmentStrategy.LOAD_BALANCE
        
        # 获取引擎并分配
        engine = self.engines.get(strategy)
        if engine is None:
            return None
        
        salesperson = engine.assign(lead, self.salespersons)
        
        if salesperson:
            lead.assigned_to = salesperson.id
            salesperson.current_leads += 1
            return salesperson.id
        
        return None
    
    def batch_assign(self, leads: List[ScoredLead], strategy: AssignmentStrategy) -> Dict[str, List[str]]:
        """批量分配线索"""
        result = {}
        engine = self.engines.get(strategy)
        
        if engine is None:
            return result
        
        for lead in leads:
            salesperson = engine.assign(lead, self.salespersons)
            if salesperson:
                lead.assigned_to = salesperson.id
                salesperson.current_leads += 1
                
                if salesperson.id not in result:
                    result[salesperson.id] = []
                result[salesperson.id].append(lead.id)
        
        return result
    
    def get_salesperson_load(self) -> List[Dict]:
        """获取销售人员负载情况"""
        return [
            {
                "id": s.id,
                "name": s.name,
                "current_leads": s.current_leads,
                "max_leads": s.max_leads,
                "load_percent": (s.current_leads / s.max_leads) * 100,
                "active": s.active
            }
            for s in self.salespersons
        ]
    
    def get_salesperson_by_id(self, salesperson_id: str) -> Optional[Salesperson]:
        """根据ID获取销售人员"""
        for s in self.salespersons:
            if s.id == salesperson_id:
                return s
        return None

# 全局实例
lead_assignment_service = LeadAssignmentService()

def get_lead_assignment_service() -> LeadAssignmentService:
    """获取线索分配服务实例"""
    return lead_assignment_service