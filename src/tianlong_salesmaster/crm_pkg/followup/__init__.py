"""自动化跟进模块 - 入口"""

from .rule_engine import (
    FollowupService,
    get_followup_service,
    TriggerType,
    ActionType,
    EventType,
    BehaviorType,
    TriggerCondition,
    Action,
    FollowupStep,
    FollowupSequence,
)

from .communication import (
    CommunicationAssistant,
    get_communication_assistant,
    ChannelType,
    FAQItem,
    MessageTemplate,
    ChatMessage,
    FAQMatcher,
    ScriptRecommender,
)

from .task_automation import (
    TaskAutomationService,
    get_task_automation_service,
    Task,
    TaskStatus,
    TaskPriority,
    TaskType,
    ReminderService,
    EscalationRule,
)

__all__ = [
    # 规则引擎
    "FollowupService",
    "get_followup_service",
    "TriggerType",
    "ActionType",
    "EventType",
    "BehaviorType",
    "TriggerCondition",
    "Action",
    "FollowupStep",
    "FollowupSequence",
    
    # 沟通助手
    "CommunicationAssistant",
    "get_communication_assistant",
    "ChannelType",
    "FAQItem",
    "MessageTemplate",
    "ChatMessage",
    "FAQMatcher",
    "ScriptRecommender",
    
    # 任务自动化
    "TaskAutomationService",
    "get_task_automation_service",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskType",
    "ReminderService",
    "EscalationRule",
]

# 服务实例
followup = get_followup_service()
communication = get_communication_assistant()
task_automation = get_task_automation_service()