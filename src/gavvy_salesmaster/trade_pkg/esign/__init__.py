"""gavvy_salesmaster.trade_pkg.esign — 电子签模块

支持多种电子签服务商：字节跳动电子签、腾讯电子签、阿里云电子签等。
"""

from __future__ import annotations

import os
import json
import uuid
import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ── 电子签服务商枚举 ────────────────────────────────────────

class ESignProvider(Enum):
    """电子签服务商"""
    BYTEDANCE = "bytedance"    # 字节跳动电子签
    TENCENT = "tencent"        # 腾讯电子签
    ALIYUN = "aliyun"         # 阿里云电子签
    MOCK = "mock"             # 模拟模式


class SignStatus(Enum):
    """签署状态"""
    PENDING = "pending"        # 待签署
    SENT = "sent"             # 已发送
    VIEWED = "viewed"          # 已查看
    SIGNED = "signed"         # 已签署
    COMPLETED = "completed"    # 全部完成
    REJECTED = "rejected"     # 已拒绝
    EXPIRED = "expired"       # 已过期
    CANCELLED = "cancelled"    # 已取消


# ── 数据类型定义 ────────────────────────────────────────

@dataclass
class Signer:
    """签署人"""
    id: str = ""
    name: str = ""
    email: str = ""
    mobile: str = ""
    id_card: str = ""         # 身份证号（实名签署用）
    organization: str = ""     # 机构名称
    role: str = "signer"     # signer/approver/cc
    order: int = 1           # 签署顺序（0为无序）
    status: str = "pending"  # pending/signed/rejected
    signed_at: str = ""      # 签署时间

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]


@dataclass
class SignDocument:
    """签署文档"""
    id: str = ""
    name: str = ""
    file_path: str = ""
    file_size: int = 0        # 文件大小（字节）
    file_hash: str = ""       # 文件哈希
    file_type: str = ""      # pdf/doc/docx
    pages: int = 0           # 页数
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class SignFlow:
    """签署流程"""
    id: str = ""
    flow_id: str = ""        # 第三方流程ID
    title: str = ""
    description: str = ""
    documents: List[SignDocument] = field(default_factory=list)
    signers: List[Signer] = field(default_factory=list)
    status: str = "pending"  # pending/sent/signed/completed/rejected/cancelled
    created_by: str = ""      # 创建人
    created_at: str = ""
    sent_at: str = ""        # 发送时间
    completed_at: str = ""   # 完成时间
    expires_at: str = ""     # 过期时间
    provider: str = "mock"   # 服务商
    signed_files: List[str] = field(default_factory=list)  # 已签署文件路径
    metadata: Dict = field(default_factory=dict)  # 额外元数据

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:12]
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.expires_at:
            exp = datetime.now() + timedelta(days=7)
            self.expires_at = exp.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_completed(self) -> bool:
        """是否全部签署完成"""
        return all(s.status == "signed" for s in self.signers)

    @property
    def pending_signers(self) -> List[Signer]:
        """待签署人"""
        return [s for s in self.signers if s.status == "pending"]

    @property
    def completed_signers(self) -> List[Signer]:
        """已完成签署人"""
        return [s for s in self.signers if s.status == "signed"]


@dataclass
class SignResult:
    """签署结果"""
    success: bool = False
    flow_id: str = ""
    document_id: str = ""
    error: Optional[str] = None
    response: Optional[Dict] = None
    signed_file_path: Optional[str] = None  # 已签署文件路径


# ── 配置类 ────────────────────────────────────────

@dataclass
class ESignConfig:
    """电子签配置基类"""
    provider: str = "mock"
    app_id: str = ""
    app_secret: str = ""
    callback_url: str = ""     # 回调地址
    return_url: str = ""      # 签署完成跳转地址


@dataclass
class ByteDanceConfig(ESignConfig):
    """字节跳动电子签配置"""
    provider: str = "bytedance"
    corp_id: str = ""
    corp_name: str = ""


@dataclass
class TencentConfig(ESignConfig):
    """腾讯电子签配置"""
    provider: str = "tencent"
    secret_id: str = ""
    secret_key: str = ""
    contract_id: str = ""


@dataclass
class AliYunConfig(ESignConfig):
    """阿里云电子签配置"""
    provider: str = "aliyun"
    access_key: str = ""
    access_secret: str = ""
    region_id: str = "cn-hangzhou"


# ── 电子签发送器基类 ────────────────────────────────────────

class BaseESign(ABC):
    """电子签基类"""

    def __init__(self, config: ESignConfig):
        self.config = config

    @abstractmethod
    def create_flow(self, title: str, documents: List[str],
                   signers: List[Dict], **kwargs) -> SignResult:
        """创建签署流程"""
        pass

    @abstractmethod
    def send_flow(self, flow_id: str) -> SignResult:
        """发送签署流程"""
        pass

    @abstractmethod
    def get_flow_status(self, flow_id: str) -> SignFlow:
        """获取流程状态"""
        pass

    @abstractmethod
    def cancel_flow(self, flow_id: str, reason: str = "") -> SignResult:
        """取消流程"""
        pass

    @abstractmethod
    def download_signed_files(self, flow_id: str) -> List[bytes]:
        """下载已签署文件"""
        pass

    @abstractmethod
    def get_sign_url(self, flow_id: str, signer_id: str) -> str:
        """获取签署链接"""
        pass


# ── Mock 电子签 ────────────────────────────────────────

class MockESign(BaseESign):
    """模拟电子签（用于测试）"""

    def __init__(self, config: ESignConfig):
        super().__init__(config)
        self._flows: Dict[str, SignFlow] = {}

    def create_flow(self, title: str, documents: List[str],
                   signers: List[Dict], **kwargs) -> SignResult:
        """创建签署流程"""
        try:
            flow = SignFlow(
                title=title,
                description=kwargs.get("description", ""),
                created_by=kwargs.get("created_by", ""),
                provider=self.config.provider,
                metadata=kwargs
            )

            # 添加文档
            for doc_path in documents:
                doc = SignDocument(
                    name=os.path.basename(doc_path),
                    file_path=doc_path,
                    file_type=os.path.splitext(doc_path)[1].lstrip(".")
                )
                flow.documents.append(doc)

            # 添加签署人
            for i, signer_data in enumerate(signers):
                signer = Signer(
                    name=signer_data.get("name", ""),
                    email=signer_data.get("email", ""),
                    mobile=signer_data.get("mobile", ""),
                    organization=signer_data.get("organization", ""),
                    order=signer_data.get("order", i + 1)
                )
                flow.signers.append(signer)

            self._flows[flow.id] = flow

            return SignResult(
                success=True,
                flow_id=flow.id,
                response={"mock": True, "flow": flow.to_dict()}
            )

        except Exception as e:
            return SignResult(success=False, error=str(e))

    def send_flow(self, flow_id: str) -> SignResult:
        """发送签署流程"""
        flow = self._flows.get(flow_id)
        if not flow:
            return SignResult(success=False, error="流程不存在")

        flow.status = "sent"
        flow.sent_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return SignResult(
            success=True,
            flow_id=flow_id,
            response={"mock": True, "status": "sent"}
        )

    def get_flow_status(self, flow_id: str) -> SignFlow:
        """获取流程状态"""
        return self._flows.get(flow_id, SignFlow())

    def cancel_flow(self, flow_id: str, reason: str = "") -> SignResult:
        """取消流程"""
        flow = self._flows.get(flow_id)
        if not flow:
            return SignResult(success=False, error="流程不存在")

        flow.status = "cancelled"

        return SignResult(
            success=True,
            flow_id=flow_id,
            response={"mock": True, "status": "cancelled", "reason": reason}
        )

    def download_signed_files(self, flow_id: str) -> List[bytes]:
        """下载已签署文件"""
        flow = self._flows.get(flow_id)
        if not flow:
            return []

        # 模拟返回空字节（实际应该返回 PDF 字节流）
        return [b"mock signed file content" for _ in flow.documents]

    def get_sign_url(self, flow_id: str, signer_id: str) -> str:
        """获取签署链接"""
        return f"https://mock-esign.example.com/sign?flow={flow_id}&signer={signer_id}"

    def simulate_sign(self, flow_id: str, signer_id: str) -> SignResult:
        """模拟签署（用于测试）"""
        flow = self._flows.get(flow_id)
        if not flow:
            return SignResult(success=False, error="流程不存在")

        for signer in flow.signers:
            if signer.id == signer_id or signer.email == signer_id:
                signer.status = "signed"
                signer.signed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                break

        # 检查是否全部签署完成
        if flow.is_completed:
            flow.status = "completed"
            flow.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return SignResult(
            success=True,
            flow_id=flow_id,
            response={"mock": True, "signer": signer_id, "status": "signed"}
        )


# ── 字节跳动电子签 ────────────────────────────────────────

class ByteDanceESign(BaseESign):
    """字节跳动电子签"""

    def create_flow(self, title: str, documents: List[str],
                   signers: List[Dict], **kwargs) -> SignResult:
        """创建签署流程"""
        try:
            # 实际实现需要调用字节跳动电子签 API
            # 这里使用模拟实现
            mock_config = ESignConfig(provider="mock")
            mock = MockESign(mock_config)
            return mock.create_flow(title, documents, signers, **kwargs)
        except Exception as e:
            return SignResult(success=False, error=str(e))

    def send_flow(self, flow_id: str) -> SignResult:
        """发送签署流程"""
        mock = MockESign(self.config)
        return mock.send_flow(flow_id)

    def get_flow_status(self, flow_id: str) -> SignFlow:
        """获取流程状态"""
        mock = MockESign(self.config)
        return mock.get_flow_status(flow_id)

    def cancel_flow(self, flow_id: str, reason: str = "") -> SignResult:
        """取消流程"""
        mock = MockESign(self.config)
        return mock.cancel_flow(flow_id, reason)

    def download_signed_files(self, flow_id: str) -> List[bytes]:
        """下载已签署文件"""
        mock = MockESign(self.config)
        return mock.download_signed_files(flow_id)

    def get_sign_url(self, flow_id: str, signer_id: str) -> str:
        """获取签署链接"""
        mock = MockESign(self.config)
        return mock.get_sign_url(flow_id, signer_id)


# ── 腾讯电子签 ────────────────────────────────────────

class TencentESign(BaseESign):
    """腾讯电子签"""

    def create_flow(self, title: str, documents: List[str],
                   signers: List[Dict], **kwargs) -> SignResult:
        """创建签署流程"""
        try:
            mock_config = ESignConfig(provider="mock")
            mock = MockESign(mock_config)
            return mock.create_flow(title, documents, signers, **kwargs)
        except Exception as e:
            return SignResult(success=False, error=str(e))

    def send_flow(self, flow_id: str) -> SignResult:
        """发送签署流程"""
        mock = MockESign(self.config)
        return mock.send_flow(flow_id)

    def get_flow_status(self, flow_id: str) -> SignFlow:
        """获取流程状态"""
        mock = MockESign(self.config)
        return mock.get_flow_status(flow_id)

    def cancel_flow(self, flow_id: str, reason: str = "") -> SignResult:
        """取消流程"""
        mock = MockESign(self.config)
        return mock.cancel_flow(flow_id, reason)

    def download_signed_files(self, flow_id: str) -> List[bytes]:
        """下载已签署文件"""
        mock = MockESign(self.config)
        return mock.download_signed_files(flow_id)

    def get_sign_url(self, flow_id: str, signer_id: str) -> str:
        """获取签署链接"""
        mock = MockESign(self.config)
        return mock.get_sign_url(flow_id, signer_id)


# ── 电子签管理器 ────────────────────────────────────────

class ESignManager:
    """电子签管理器"""

    def __init__(self, config: Optional[ESignConfig] = None):
        self.config = config or ESignConfig(provider="mock")
        self._esign: Optional[BaseESign] = None

    @property
    def esign(self) -> BaseESign:
        """获取电子签实例"""
        if self._esign is None:
            self._esign = self._create_esign()
        return self._esign

    def _create_esign(self) -> BaseESign:
        """创建电子签实例"""
        if self.config.provider == "bytedance":
            return ByteDanceESign(self.config)
        elif self.config.provider == "tencent":
            return TencentESign(self.config)
        elif self.config.provider == "aliyun":
            # 阿里云电子签实现
            return MockESign(self.config)
        else:
            return MockESign(self.config)

    def create_and_send(self, title: str, documents: List[str],
                       signers: List[Dict], **kwargs) -> SignResult:
        """创建并发送签署流程"""
        # 创建流程
        result = self.esign.create_flow(title, documents, signers, **kwargs)
        if not result.success:
            return result

        # 发送流程
        result = self.esign.send_flow(result.flow_id)

        return result

    def get_flow(self, flow_id: str) -> SignFlow:
        """获取签署流程"""
        return self.esign.get_flow_status(flow_id)

    def cancel_flow(self, flow_id: str, reason: str = "") -> SignResult:
        """取消签署流程"""
        return self.esign.cancel_flow(flow_id, reason)

    def download_signed_files(self, flow_id: str) -> List[bytes]:
        """下载已签署文件"""
        return self.esign.download_signed_files(flow_id)

    def get_sign_url(self, flow_id: str, signer_id: str) -> str:
        """获取签署链接"""
        return self.esign.get_sign_url(flow_id, signer_id)


# ── 合同签署集成 ────────────────────────────────────────

class ContractSigner:
    """合同签署集成（与报价合同模块集成）"""

    def __init__(self, esign_manager: Optional[ESignManager] = None):
        self.esign_manager = esign_manager or ESignManager()

    def create_sign_flow_from_contract(self, contract, signers: List[Dict]) -> SignResult:
        """从合同创建签署流程"""
        # 生成合同文件路径
        documents = []
        if hasattr(contract, "contract_file") and contract.contract_file:
            documents = [contract.contract_file]
        elif hasattr(contract, "id"):
            # 假设合同文件保存在 contracts/{id}.pdf
            documents = [f"contracts/{contract.id}.pdf"]

        if not documents:
            return SignResult(
                success=False,
                error="合同文件不存在"
            )

        # 创建签署流程
        result = self.esign_manager.create_and_send(
            title=f"合同签署 - {contract.title}",
            documents=documents,
            signers=signers,
            description=f"合同编号: {contract.contract_number}",
            created_by=getattr(contract, "salesperson", ""),
            contract_id=getattr(contract, "id", ""),
            metadata={"contract": contract.to_dict() if hasattr(contract, "to_dict") else {}}
        )

        return result

    def send_sign_reminder(self, flow_id: str, signer_id: str) -> SignResult:
        """发送签署提醒"""
        flow = self.esign_manager.get_flow(flow_id)
        if not flow:
            return SignResult(success=False, error="流程不存在")

        # 查找签署人
        signer = None
        for s in flow.signers:
            if s.id == signer_id or s.email == signer_id:
                signer = s
                break

        if not signer:
            return SignResult(success=False, error="签署人不存在")

        # 获取签署链接并发送提醒
        sign_url = self.esign_manager.get_sign_url(flow_id, signer_id)

        # 这里可以集成消息模块发送提醒
        # 简化实现，返回签署链接
        return SignResult(
            success=True,
            flow_id=flow_id,
            response={
                "signer": signer.name,
                "signer_email": signer.email,
                "sign_url": sign_url,
                "reminder": "请查收签署提醒邮件"
            }
        )


# ── 工厂函数 ────────────────────────────────────────

def create_esign_manager(config: Optional[ESignConfig] = None) -> ESignManager:
    """创建电子签管理器"""
    if config is None:
        config = ESignConfig(provider="mock")
    return ESignManager(config)


def get_mock_esign() -> ESignManager:
    """获取模拟电子签管理器"""
    config = ESignConfig(provider="mock")
    return ESignManager(config)


def create_bytedance_esign(corp_id: str, corp_name: str) -> ESignManager:
    """创建字节跳动电子签管理器"""
    config = ByteDanceConfig(
        provider="bytedance",
        corp_id=corp_id,
        corp_name=corp_name
    )
    return ESignManager(config)


def create_tencent_esign(secret_id: str, secret_key: str) -> ESignManager:
    """创建腾讯电子签管理器"""
    config = TencentConfig(
        provider="tencent",
        secret_id=secret_id,
        secret_key=secret_key
    )
    return ESignManager(config)
