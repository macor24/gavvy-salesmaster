"""跟进通信模块 - 多渠道消息自动回复"""

import json
import time
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod


class ChannelType(str, Enum):
    """消息渠道类型"""
    WEWORK = "wework"
    DINGTALK = "dingtalk"
    FEISHU = "feishu"
    EMAIL = "email"
    SMS = "sms"


@dataclass
class Message:
    """消息数据结构"""
    id: str
    channel: ChannelType
    sender_id: str
    sender_name: str
    receiver_id: str
    content: str
    message_type: str = "text"
    timestamp: datetime = None
    attachments: List[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.attachments is None:
            self.attachments = []
    
    def to_dict(self):
        d = asdict(self)
        d["channel"] = self.channel.value
        d["timestamp"] = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return d


@dataclass
class ReplyTemplate:
    """回复模板"""
    id: str
    name: str
    pattern: str  # 匹配模式（支持正则）
    reply_text: str
    priority: int = 1
    enabled: bool = True
    category: str = "general"
    
    def to_dict(self):
        return asdict(self)


class MessageHandler(ABC):
    """消息处理器抽象基类"""
    
    @abstractmethod
    def receive_message(self, message: Message) -> None:
        """接收消息"""
        pass
    
    @abstractmethod
    def send_message(self, message: Message) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    def auto_reply(self, message: Message) -> Optional[Message]:
        """自动回复"""
        pass


class FAQManager:
    """FAQ管理"""
    
    def __init__(self):
        self.faqs = self._load_faqs()
    
    def _load_faqs(self) -> List[Dict]:
        """加载FAQ数据"""
        return [
            {
                "question": "你好|您好|Hi|Hello",
                "answer": "您好！请问有什么可以帮助您的吗？我是销售宗师智能助手。",
                "category": "greeting"
            },
            {
                "question": "价格|报价|多少钱|费用",
                "answer": "感谢您的关注！我们的产品价格根据需求定制，请问您方便告知具体需求吗？我可以为您安排专业顾问联系您。",
                "category": "pricing"
            },
            {
                "question": "产品|功能|介绍",
                "answer": "销售宗师是一款智能销售自动化平台，提供线索挖掘、智能跟进、销售预测等核心功能。如需详细了解，我可以发送产品手册给您。",
                "category": "product"
            },
            {
                "question": "试用|免费|demo|演示",
                "answer": "当然可以！我们提供14天免费试用，包含全部核心功能。请问您的邮箱是多少？我来为您开通试用账号。",
                "category": "trial"
            },
            {
                "question": "客服|售后|支持",
                "answer": "我们提供7x24小时技术支持服务。您可以拨打客服热线400-xxx-xxxx，或发送邮件至support@salesmaster.com。",
                "category": "support"
            },
            {
                "question": "案例|客户|成功",
                "answer": "我们已服务超过1000家企业客户，覆盖制造、金融、科技等多个行业。如需了解具体案例，我可以发送案例集给您参考。",
                "category": "case"
            },
            {
                "question": "合作|伙伴|渠道",
                "answer": "我们欢迎各类合作伙伴！如需了解合作政策，请留下您的联系方式，渠道经理会尽快与您联系。",
                "category": "partner"
            },
            {
                "question": "谢谢|感谢|再见",
                "answer": "不客气！如有任何问题随时联系我们，祝您工作顺利！",
                "category": "farewell"
            }
        ]
    
    def match_faq(self, message: str) -> Optional[str]:
        """匹配FAQ"""
        import re
        
        for faq in self.faqs:
            patterns = faq["question"].split("|")
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    return faq["answer"]
        return None
    
    def add_faq(self, question: str, answer: str, category: str = "general"):
        """添加FAQ"""
        self.faqs.append({
            "question": question,
            "answer": answer,
            "category": category
        })
    
    def remove_faq(self, question_pattern: str):
        """删除FAQ"""
        self.faqs = [f for f in self.faqs if question_pattern not in f["question"]]


class WeWorkClient:
    """企业微信客户端"""
    
    def __init__(self, corp_id: str = None, corp_secret: str = None, agent_id: str = None):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.access_token = None
        self.token_expire_time = 0
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
        
        if not self.corp_id or not self.corp_secret:
            return "mock_token_for_test"
        
        try:
            url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
            response = requests.get(url, timeout=30)
            data = response.json()
            if data.get("errcode") == 0:
                self.access_token = data["access_token"]
                self.token_expire_time = time.time() + data["expires_in"] - 60
                return self.access_token
        except Exception as e:
            print(f"获取企微token失败: {e}")
        
        return "mock_token_for_test"
    
    def send_text_message(self, user_id: str, content: str) -> bool:
        """发送文本消息"""
        token = self._get_access_token()
        
        if not self.corp_id or not self.corp_secret:
            print(f"[企微Mock] 发送消息给 {user_id}: {content}")
            return True
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        payload = {
            "touser": user_id,
            "agentid": self.agent_id,
            "msgtype": "text",
            "text": {
                "content": content
            },
            "safe": 0
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            return data.get("errcode") == 0
        except Exception as e:
            print(f"发送企微消息失败: {e}")
            return False
    
    def send_image_message(self, user_id: str, media_id: str) -> bool:
        """发送图片消息"""
        token = self._get_access_token()
        
        if not self.corp_id or not self.corp_secret:
            print(f"[企微Mock] 发送图片给 {user_id}: media_id={media_id}")
            return True
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        payload = {
            "touser": user_id,
            "agentid": self.agent_id,
            "msgtype": "image",
            "image": {
                "media_id": media_id
            },
            "safe": 0
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            return data.get("errcode") == 0
        except Exception as e:
            print(f"发送企微图片失败: {e}")
            return False
    
    def send_news_message(self, user_id: str, articles: List[Dict]) -> bool:
        """发送图文消息"""
        token = self._get_access_token()
        
        if not self.corp_id or not self.corp_secret:
            print(f"[企微Mock] 发送图文给 {user_id}: {articles}")
            return True
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        payload = {
            "touser": user_id,
            "agentid": self.agent_id,
            "msgtype": "news",
            "news": {
                "articles": articles
            },
            "safe": 0
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            return data.get("errcode") == 0
        except Exception as e:
            print(f"发送企微图文失败: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        token = self._get_access_token()
        
        if not self.corp_id or not self.corp_secret:
            return {
                "userid": user_id,
                "name": "测试用户",
                "department": ["销售部"],
                "mobile": "13800138000"
            }
        
        url = f"https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={token}&userid={user_id}"
        
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            if data.get("errcode") == 0:
                return data
        except Exception as e:
            print(f"获取企微用户信息失败: {e}")
        
        return None


class WeWorkMessageHandler(MessageHandler):
    """企微消息处理器"""
    
    def __init__(self, client: WeWorkClient = None, faq_manager: FAQManager = None):
        self.client = client or WeWorkClient()
        self.faq_manager = faq_manager or FAQManager()
        self.reply_templates = self._load_templates()
    
    def _load_templates(self) -> List[ReplyTemplate]:
        """加载回复模板"""
        return [
            ReplyTemplate(
                id="temp_greeting",
                name="问候语回复",
                pattern=r"^你好|您好|Hi|Hello|早上好|下午好",
                reply_text="您好！我是销售宗师智能助手，很高兴为您服务。请问有什么可以帮助您的？",
                priority=10
            ),
            ReplyTemplate(
                id="temp_pricing",
                name="价格咨询回复",
                pattern=r"价格|报价|多少钱|费用|收费",
                reply_text="感谢您的关注！我们提供灵活的定价方案，根据企业规模和需求定制。请留下您的联系方式，专业顾问会尽快与您联系。",
                priority=8
            ),
            ReplyTemplate(
                id="temp_trial",
                name="试用咨询回复",
                pattern=r"试用|免费|demo|演示|体验",
                reply_text="我们提供14天免费试用，包含全部核心功能。请告诉我您的邮箱，我来为您开通试用账号。",
                priority=8
            ),
            ReplyTemplate(
                id="temp_urgent",
                name="紧急需求回复",
                pattern=r"紧急|尽快|马上|立刻",
                reply_text="收到！我已标记您的需求为紧急，客服团队会在30分钟内与您联系。",
                priority=15
            )
        ]
    
    def receive_message(self, message: Message) -> None:
        """接收消息"""
        print(f"[企微消息] 收到来自 {message.sender_name}: {message.content}")
    
    def send_message(self, message: Message) -> bool:
        """发送消息"""
        return self.client.send_text_message(message.receiver_id, message.content)
    
    def auto_reply(self, message: Message) -> Optional[Message]:
        """自动回复"""
        # 首先尝试匹配模板
        import re
        for template in sorted(self.reply_templates, key=lambda x: -x.priority):
            if template.enabled and re.search(template.pattern, message.content, re.IGNORECASE):
                reply_content = template.reply_text
                break
        else:
            # 尝试匹配FAQ
            reply_content = self.faq_manager.match_faq(message.content)
        
        if reply_content:
            return Message(
                id=f"reply_{message.id}",
                channel=message.channel,
                sender_id="bot",
                sender_name="销售宗师",
                receiver_id=message.sender_id,
                content=reply_content,
                timestamp=datetime.now()
            )
        
        return None


class DingTalkClient:
    """钉钉客户端"""
    
    def __init__(self, app_key: str = None, app_secret: str = None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = None
    
    def send_text_message(self, user_id: str, content: str) -> bool:
        """发送文本消息"""
        if not self.app_key or not self.app_secret:
            print(f"[钉钉Mock] 发送消息给 {user_id}: {content}")
            return True
        
        try:
            url = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"
            headers = {"Content-Type": "application/json"}
            payload = {
                "agent_id": "123456",
                "userid_list": user_id,
                "msg": {
                    "msgtype": "text",
                    "text": {"content": content}
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            data = response.json()
            return data.get("errcode") == 0
        except Exception as e:
            print(f"发送钉钉消息失败: {e}")
            return False


class FeishuClient:
    """飞书客户端"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id
        self.app_secret = app_secret
    
    def send_text_message(self, user_id: str, content: str) -> bool:
        """发送文本消息"""
        if not self.app_id or not self.app_secret:
            print(f"[飞书Mock] 发送消息给 {user_id}: {content}")
            return True
        
        try:
            url = "https://open.feishu.cn/open-apis/im/v1/messages"
            payload = {
                "receive_id": user_id,
                "content": json.dumps({"text": content}),
                "msg_type": "text"
            }
            response = requests.post(url, json=payload, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"发送飞书消息失败: {e}")
            return False


class CommunicationService:
    """通信服务"""
    
    def __init__(self):
        self.wework_client = WeWorkClient()
        self.wework_handler = WeWorkMessageHandler(self.wework_client)
        self.dingtalk_client = DingTalkClient()
        self.feishu_client = FeishuClient()
        self.faq_manager = FAQManager()
    
    def configure_wework(self, corp_id: str, corp_secret: str, agent_id: str):
        """配置企微"""
        self.wework_client = WeWorkClient(corp_id, corp_secret, agent_id)
        self.wework_handler = WeWorkMessageHandler(self.wework_client, self.faq_manager)
    
    def configure_dingtalk(self, app_key: str, app_secret: str):
        """配置钉钉"""
        self.dingtalk_client = DingTalkClient(app_key, app_secret)
    
    def configure_feishu(self, app_id: str, app_secret: str):
        """配置飞书"""
        self.feishu_client = FeishuClient(app_id, app_secret)
    
    def send_message(self, channel: ChannelType, user_id: str, content: str) -> bool:
        """发送消息"""
        if channel == ChannelType.WEWORK:
            return self.wework_client.send_text_message(user_id, content)
        elif channel == ChannelType.DINGTALK:
            return self.dingtalk_client.send_text_message(user_id, content)
        elif channel == ChannelType.FEISHU:
            return self.feishu_client.send_text_message(user_id, content)
        return False
    
    def handle_message(self, message: Message) -> Optional[Message]:
        """处理消息并自动回复"""
        if message.channel == ChannelType.WEWORK:
            self.wework_handler.receive_message(message)
            return self.wework_handler.auto_reply(message)
        return None
    
    def add_faq(self, question: str, answer: str, category: str = "general"):
        """添加FAQ"""
        self.faq_manager.add_faq(question, answer, category)
    
    def add_reply_template(self, template: ReplyTemplate):
        """添加回复模板"""
        self.wework_handler.reply_templates.append(template)


# 兼容旧版的别名
class CommunicationAssistant(CommunicationService):
    """通信助手（兼容旧版命名）"""
    pass


@dataclass
class FAQItem:
    """FAQ项"""
    question: str
    answer: str
    category: str = "general"
    priority: int = 1


@dataclass
class MessageTemplate:
    """消息模板"""
    id: str
    name: str
    content: str
    category: str = "general"


@dataclass
class ChatMessage:
    """聊天消息"""
    id: str
    sender: str
    content: str
    timestamp: datetime = None
    channel: ChannelType = ChannelType.WEWORK
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FAQMatcher:
    """FAQ匹配器"""
    
    def __init__(self):
        self.faqs = []
    
    def add_faq(self, question: str, answer: str, category: str = "general"):
        """添加FAQ"""
        self.faqs.append({"question": question, "answer": answer, "category": category})
    
    def match(self, query: str) -> Optional[str]:
        """匹配FAQ"""
        import re
        for faq in self.faqs:
            patterns = faq["question"].split("|")
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return faq["answer"]
        return None


class ScriptRecommender:
    """话术推荐器"""
    
    def __init__(self):
        self.scripts = {
            "greeting": "您好！我是销售宗师智能助手，很高兴为您服务。",
            "followup": "您好，请问最近是否有采购计划？",
            "closing": "根据您的需求，我们可以尽快安排合同签署。",
            "objection": "感谢您的反馈，我们可以再沟通看看有没有更好的方案。",
        }
    
    def recommend(self, context: str) -> str:
        """推荐话术"""
        context_lower = context.lower()
        if any(k in context_lower for k in ["你好", "您好", "hi", "hello"]):
            return self.scripts["greeting"]
        elif any(k in context_lower for k in ["跟进", "进展", "计划"]):
            return self.scripts["followup"]
        elif any(k in context_lower for k in ["签", "合同", "付款"]):
            return self.scripts["closing"]
        elif any(k in context_lower for k in ["贵", "不需要", "考虑"]):
            return self.scripts["objection"]
        return self.scripts["greeting"]


# 全局实例
communication_service = CommunicationService()
communication_assistant = CommunicationAssistant()


def get_communication_service() -> CommunicationService:
    """获取通信服务实例"""
    return communication_service


def get_communication_assistant() -> CommunicationAssistant:
    """获取通信助手实例（兼容旧版）"""
    return communication_assistant
