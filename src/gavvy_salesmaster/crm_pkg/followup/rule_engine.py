"""自动化跟进模块 - 跟进规则引擎"""

import json
import time
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
from collections import defaultdict

class TriggerType(str, Enum):
    """触发类型"""
    TIME = "time"
    EVENT = "event"
    BEHAVIOR = "behavior"

class ActionType(str, Enum):
    """动作类型"""
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_WECHAT = "send_wechat"
    SEND_DINGTALK = "send_dingtalk"
    SEND_FEISHU = "send_feishu"
    CREATE_TASK = "create_task"
    UPDATE_STATUS = "update_status"
    ADD_TAG = "add_tag"
    NOTIFY = "notify"

class EventType(str, Enum):
    """事件类型"""
    LEAD_CREATED = "lead_created"
    LEAD_UPDATED = "lead_updated"
    CONTACT_MADE = "contact_made"
    EMAIL_OPENED = "email_opened"
    LINK_CLICKED = "link_clicked"
    FORM_SUBMITTED = "form_submitted"
    TASK_COMPLETED = "task_completed"
    DEAL_WON = "deal_won"
    DEAL_LOST = "deal_lost"

class BehaviorType(str, Enum):
    """行为类型"""
    VISIT_WEBSITE = "visit_website"
    DOWNLOAD_BROCHURE = "download_brochure"
    VIEW_PRODUCT = "view_product"
    REQUEST_DEMO = "request_demo"
    ATTEND_WEBINAR = "attend_webinar"
    VIEW_PRICING = "view_pricing"

@dataclass
class TriggerCondition:
    """触发条件"""
    type: TriggerType
    event_type: Optional[EventType] = None
    behavior_type: Optional[BehaviorType] = None
    time_delay: Optional[timedelta] = None
    time_schedule: Optional[str] = None
    conditions: Optional[List[Dict]] = None
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []

@dataclass
class Action:
    """执行动作"""
    type: ActionType
    template_id: Optional[str] = None
    content: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}

@dataclass
class FollowupStep:
    """跟进步骤"""
    id: str
    name: str
    trigger: TriggerCondition
    actions: List[Action]
    delay_before: Optional[timedelta] = None
    condition: Optional[Dict] = None

@dataclass
class FollowupSequence:
    """跟进序列"""
    id: str
    name: str
    description: str = ""
    steps: List[FollowupStep] = None
    enabled: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.created_at is None:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

class RuleEngine(ABC):
    """规则引擎抽象基类"""
    
    @abstractmethod
    def evaluate(self, event: Dict, context: Dict) -> bool:
        """评估条件"""
        pass

class TimeRuleEngine(RuleEngine):
    """时间规则引擎"""
    
    def evaluate(self, event: Dict, context: Dict) -> bool:
        """评估时间条件"""
        if "time_delay" in context:
            delay = context["time_delay"]
            if isinstance(delay, timedelta):
                return True
        return False

class EventRuleEngine(RuleEngine):
    """事件规则引擎"""
    
    def evaluate(self, event: Dict, context: Dict) -> bool:
        """评估事件条件"""
        event_type = event.get("type")
        if event_type == context.get("event_type"):
            return self._check_conditions(event, context.get("conditions", []))
        return False
    
    def _check_conditions(self, event: Dict, conditions: List[Dict]) -> bool:
        """检查条件"""
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            event_value = event.get(field)
            
            if not self._compare(event_value, operator, value):
                return False
        
        return True
    
    def _compare(self, event_value, operator, value) -> bool:
        """比较值"""
        if operator == "==":
            return event_value == value
        elif operator == "!=":
            return event_value != value
        elif operator == ">":
            return event_value > value
        elif operator == "<":
            return event_value < value
        elif operator == ">=":
            return event_value >= value
        elif operator == "<=":
            return event_value <= value
        elif operator == "contains":
            return value in str(event_value)
        elif operator == "in":
            return event_value in value
        return False

class BehaviorRuleEngine(RuleEngine):
    """行为规则引擎"""
    
    def evaluate(self, event: Dict, context: Dict) -> bool:
        """评估行为条件"""
        behavior_type = event.get("behavior_type")
        if behavior_type == context.get("behavior_type"):
            return True
        return False

class ActionExecutor(ABC):
    """动作执行器抽象基类"""
    
    @abstractmethod
    def execute(self, action: Action, context: Dict) -> bool:
        """执行动作"""
        pass

class EmailExecutor(ActionExecutor):
    """邮件执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """发送邮件"""
        lead = context.get("lead")
        if lead and lead.contact_email:
            print(f"📧 发送邮件给 {lead.contact_email}: {action.content}")
            return True
        return False

class SMSExecutor(ActionExecutor):
    """短信执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """发送短信"""
        lead = context.get("lead")
        if lead and lead.contact_phone:
            print(f"💬 发送短信给 {lead.contact_phone}: {action.content}")
            return True
        return False

class WeChatExecutor(ActionExecutor):
    """微信执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """发送微信消息"""
        lead = context.get("lead")
        if lead:
            print(f"💬 发送微信消息给 {lead.contact_name}: {action.content}")
            return True
        return False

class DingTalkExecutor(ActionExecutor):
    """钉钉执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """发送钉钉消息"""
        lead = context.get("lead")
        if lead:
            print(f"💬 发送钉钉消息给 {lead.contact_name}: {action.content}")
            return True
        return False

class FeishuExecutor(ActionExecutor):
    """飞书执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """发送飞书消息"""
        lead = context.get("lead")
        if lead:
            print(f"💬 发送飞书消息给 {lead.contact_name}: {action.content}")
            return True
        return False

class TaskExecutor(ActionExecutor):
    """任务执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """创建任务"""
        lead = context.get("lead")
        assignee = action.params.get("assignee", "auto")
        print(f"📋 创建任务: {action.content}")
        if lead:
            print(f"   关联线索: {lead.company_name} - {lead.contact_name}")
        if assignee:
            print(f"   负责人: {assignee}")
        return True

class StatusExecutor(ActionExecutor):
    """状态执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """更新状态"""
        lead = context.get("lead")
        new_status = action.params.get("status")
        if lead and new_status:
            print(f"🔄 更新线索状态: {lead.id} -> {new_status}")
            lead.status = new_status
            return True
        return False

class TagExecutor(ActionExecutor):
    """标签执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """添加标签"""
        lead = context.get("lead")
        tags = action.params.get("tags", [])
        if lead and tags:
            lead.tags.extend(tags)
            print(f"🏷️ 添加标签: {lead.id} -> {tags}")
            return True
        return False

class NotificationExecutor(ActionExecutor):
    """通知执行器"""
    
    def execute(self, action: Action, context: Dict) -> bool:
        """发送通知"""
        target = action.params.get("target", "sales")
        print(f"🔔 发送通知给 {target}: {action.content}")
        return True

class FollowupService:
    """跟进服务"""
    
    def __init__(self):
        self.sequences: List[FollowupSequence] = []
        self.executors: Dict[ActionType, ActionExecutor] = {
            ActionType.SEND_EMAIL: EmailExecutor(),
            ActionType.SEND_SMS: SMSExecutor(),
            ActionType.SEND_WECHAT: WeChatExecutor(),
            ActionType.SEND_DINGTALK: DingTalkExecutor(),
            ActionType.SEND_FEISHU: FeishuExecutor(),
            ActionType.CREATE_TASK: TaskExecutor(),
            ActionType.UPDATE_STATUS: StatusExecutor(),
            ActionType.ADD_TAG: TagExecutor(),
            ActionType.NOTIFY: NotificationExecutor(),
        }
        self.running_tasks: Dict[str, Dict] = {}
        
        # 初始化默认跟进序列
        self._init_default_sequences()
    
    def _init_default_sequences(self):
        """初始化默认跟进序列"""
        # 新线索欢迎序列
        welcome_sequence = FollowupSequence(
            id="seq_welcome",
            name="新线索欢迎序列",
            description="新线索创建后的欢迎跟进流程",
            steps=[
                FollowupStep(
                    id="step1",
                    name="立即发送欢迎邮件",
                    trigger=TriggerCondition(
                        type=TriggerType.EVENT,
                        event_type=EventType.LEAD_CREATED,
                    ),
                    actions=[
                        Action(
                            type=ActionType.SEND_EMAIL,
                            content="欢迎联系我们！感谢您的关注，我们的销售顾问将尽快与您联系。"
                        ),
                        Action(
                            type=ActionType.CREATE_TASK,
                            content="24小时内跟进新线索",
                            params={"assignee": "auto"}
                        )
                    ]
                ),
                FollowupStep(
                    id="step2",
                    name="24小时后未回复提醒",
                    trigger=TriggerCondition(
                        type=TriggerType.TIME,
                        time_delay=timedelta(hours=24)
                    ),
                    actions=[
                        Action(
                            type=ActionType.SEND_WECHAT,
                            content="您好，我是销售顾问小张，看到您之前对我们的产品感兴趣，请问有什么可以帮您的？"
                        )
                    ],
                    condition={"status": "new"}
                ),
                FollowupStep(
                    id="step3",
                    name="72小时后电话跟进",
                    trigger=TriggerCondition(
                        type=TriggerType.TIME,
                        time_delay=timedelta(hours=72)
                    ),
                    actions=[
                        Action(
                            type=ActionType.CREATE_TASK,
                            content="电话跟进线索",
                            params={"assignee": "auto"}
                        ),
                        Action(
                            type=ActionType.NOTIFY,
                            content="线索超过72小时未联系，请及时跟进",
                            params={"target": "manager"}
                        )
                    ],
                    condition={"status": "new"}
                )
            ]
        )
        
        # 报价后跟进序列
        proposal_sequence = FollowupSequence(
            id="seq_proposal",
            name="报价后跟进序列",
            description="发送报价后的跟进流程",
            steps=[
                FollowupStep(
                    id="step1",
                    name="报价发送当天",
                    trigger=TriggerCondition(
                        type=TriggerType.EVENT,
                        event_type=EventType.TASK_COMPLETED,
                        conditions=[{"field": "task_type", "operator": "==", "value": "send_proposal"}]
                    ),
                    actions=[
                        Action(
                            type=ActionType.SEND_EMAIL,
                            content="您好，报价单已发送，请查收附件。如有任何疑问，请随时联系我。"
                        )
                    ]
                ),
                FollowupStep(
                    id="step2",
                    name="3天后跟进",
                    trigger=TriggerCondition(
                        type=TriggerType.TIME,
                        time_delay=timedelta(days=3)
                    ),
                    actions=[
                        Action(
                            type=ActionType.SEND_WECHAT,
                            content="您好，想了解一下报价单您这边看的怎么样了？是否有什么问题需要沟通？"
                        )
                    ],
                    condition={"status": "proposal"}
                ),
                FollowupStep(
                    id="step3",
                    name="7天后催单",
                    trigger=TriggerCondition(
                        type=TriggerType.TIME,
                        time_delay=timedelta(days=7)
                    ),
                    actions=[
                        Action(
                            type=ActionType.SEND_SMS,
                            content="【销售宗师】您的报价单已发送7天，期待您的回复。如有需要调整，请随时联系我们。"
                        ),
                        Action(
                            type=ActionType.NOTIFY,
                            content="报价超过7天未回复，建议电话跟进",
                            params={"target": "sales"}
                        )
                    ],
                    condition={"status": "proposal"}
                )
            ]
        )
        
        self.sequences.extend([welcome_sequence, proposal_sequence])
    
    def add_sequence(self, sequence: FollowupSequence):
        """添加跟进序列"""
        self.sequences.append(sequence)
    
    def get_sequence(self, sequence_id: str) -> Optional[FollowupSequence]:
        """获取跟进序列"""
        for seq in self.sequences:
            if seq.id == sequence_id:
                return seq
        return None
    
    def remove_sequence(self, sequence_id: str):
        """删除跟进序列"""
        self.sequences = [seq for seq in self.sequences if seq.id != sequence_id]
    
    def trigger_event(self, event_type: EventType, **context):
        """触发事件"""
        event = {"type": event_type.value, "timestamp": datetime.now(), **context}

        for sequence in self.sequences:
            if not sequence.enabled:
                continue

            for step in sequence.steps:
                if step.trigger.type == TriggerType.EVENT and \
                   step.trigger.event_type == event_type:
                    self._execute_step(step, context)

        # 桥接到 WorkflowEngine EventBus
        self._bridge_to_workflow(event_type, context)

    def _bridge_to_workflow(self, event_type: EventType, context: Dict) -> None:
        """将 followup 事件桥接到 WorkflowEngine EventBus"""
        try:
            from gavvy_salesmaster.core.workflow import (
                WorkflowEvent, EventType as WFEventType, get_event_bus,
            )
            wf_event_type = self._map_to_workflow_event(event_type)
            if wf_event_type:
                bus = get_event_bus()
                event = WorkflowEvent(
                    type=wf_event_type,
                    source="followup",
                    data=context,
                )
                bus.publish(event)
        except Exception:
            pass  # WorkflowEngine 不可用时静默降级

    @staticmethod
    def _map_to_workflow_event(fup_event: EventType) -> Optional[str]:
        """映射 followup EventType 到 WorkflowEventType"""
        mapping = {
            EventType.LEAD_CREATED: "lead.created",
            EventType.DEAL_WON: "deal.won",
            EventType.DEAL_LOST: "deal.lost",
            EventType.TASK_COMPLETED: "task.completed",
            EventType.CONTACT_MADE: "contact.made",
        }
        return mapping.get(fup_event)
    
    def _execute_step(self, step: FollowupStep, context: Dict):
        """执行步骤"""
        print(f"⚡ 执行跟进步骤: {step.name}")
        
        for action in step.actions:
            executor = self.executors.get(action.type)
            if executor:
                executor.execute(action, context)
    
    def schedule_time_trigger(self, sequence_id: str, step_id: str, delay: timedelta, context: Dict):
        """调度时间触发"""
        task_id = f"{sequence_id}_{step_id}_{time.time()}"
        self.running_tasks[task_id] = {
            "sequence_id": sequence_id,
            "step_id": step_id,
            "context": context,
            "scheduled_time": datetime.now() + delay,
            "status": "pending"
        }
    
    def process_pending_tasks(self):
        """处理待执行任务"""
        now = datetime.now()
        completed_tasks = []
        
        for task_id, task in self.running_tasks.items():
            if task["status"] == "pending" and task["scheduled_time"] <= now:
                sequence = self.get_sequence(task["sequence_id"])
                if sequence:
                    for step in sequence.steps:
                        if step.id == task["step_id"]:
                            self._execute_step(step, task["context"])
                            break
                
                task["status"] = "completed"
                completed_tasks.append(task_id)
        
        # 清理已完成任务
        for task_id in completed_tasks:
            del self.running_tasks[task_id]
    
    def get_pending_tasks(self) -> List[Dict]:
        """获取待执行任务"""
        return [task for task in self.running_tasks.values() if task["status"] == "pending"]

# 全局实例
followup_service = FollowupService()

def get_followup_service() -> FollowupService:
    """获取跟进服务实例"""
    return followup_service