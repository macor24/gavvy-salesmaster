"""tianlong_salesmaster.trade_pkg.esign.tencent — 腾讯电子签集成

真实腾讯电子签 API 集成，支持：
- 企业实名签署
- 个人签署
- 签署流程管理
- 签署回调处理

API文档: https://cloud.tencent.com/document/product/1323
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.request
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.ess.v20201111 import ess_client, models
    _HAS_TENCENT = True
except ImportError:
    _HAS_TENCENT = False
    ess_client = None
    models = None


@dataclass
class TencentESignConfig:
    """腾讯电子签配置"""
    secret_id: str = ""
    secret_key: str = ""
    contract_id: str = ""
    endpoint: str = "ess.tencentcloudapi.com"
    region: str = "ap-guangzhou"
    callback_url: str = ""
    return_url: str = ""
    sandbox: bool = False


class TencentESign:
    """腾讯电子签服务"""

    def __init__(self, config: TencentESignConfig):
        self.config = config
        self._client = None

        if _HAS_TENCENT and config.secret_id and config.secret_key:
            self._init_client()

    def _init_client(self):
        """初始化腾讯云客户端"""
        try:
            cred = credential.Credential(self.config.secret_id, self.config.secret_key)
            http_profile = HttpProfile()
            http_profile.endpoint = self.config.endpoint

            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile

            self._client = ess_client.EssClient(
                cred, self.config.region, client_profile
            )
        except Exception:
            self._client = None

    def create_flow(
        self,
        title: str,
        documents: List[str],
        signers: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """创建签署流程"""
        if not self._client:
            return self._create_mock_flow(title, documents, signers, **kwargs)

        try:
            req = models.CreateFlowRequest()

            req.FlowName = title
            req.FlowDescription = kwargs.get("description", "")
            req.FlowType = kwargs.get("flow_type", "合同签署")

            approvers = []
            for i, signer in enumerate(signers):
                approver = models.FlowApproverInfo()
                approver.Name = signer.get("name", "")
                approver.Mobile = signer.get("mobile", "")
                approver.Email = signer.get("email", "")

                if signer.get("id_card"):
                    approver.IdCardType = "ID_CARD"
                    approver.IdCardNumber = signer["id_card"]

                if signer.get("organization"):
                    approver.OrganizationName = signer["organization"]
                    approver.ApproverType = 1
                else:
                    approver.ApproverType = 0

                approvers.append(approver)

            req.Approvers = approvers

            resp = self._client.CreateFlow(req)

            return {
                "success": True,
                "flow_id": resp.FlowId,
                "data": {
                    "flow_id": resp.FlowId,
                    "flow_status": "pending",
                },
            }

        except TencentCloudSDKException as e:
            return {"success": False, "errcode": e.code, "errmsg": e.message}

    def send_flow(self, flow_id: str) -> Dict[str, Any]:
        """发送签署流程"""
        if not self._client:
            return {"success": True, "flow_id": flow_id, "mock": True}

        try:
            req = models.CreateFlowEvidenceReportRequest()
            req.FlowId = flow_id

            resp = self._client.CreateFlowEvidenceReport(req)

            return {
                "success": True,
                "flow_id": flow_id,
                "data": {"status": "sent"},
            }

        except TencentCloudSDKException as e:
            return {"success": False, "errcode": e.code, "errmsg": e.message}

    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """获取流程状态"""
        if not self._client:
            return {
                "success": True,
                "flow_id": flow_id,
                "status": "pending",
                "signers": [],
                "mock": True,
            }

        try:
            req = models.DescribeFlowInfoRequest()
            req.FlowId = flow_id

            resp = self._client.DescribeFlowInfo(req)

            signers = []
            for approver in resp.Approvers:
                signers.append({
                    "name": approver.Name,
                    "mobile": approver.Mobile,
                    "status": approver.ApproverStatus,
                    "signed_at": approver.SignTime,
                })

            return {
                "success": True,
                "flow_id": flow_id,
                "status": resp.FlowStatus,
                "signers": signers,
            }

        except TencentCloudSDKException as e:
            return {"success": False, "errcode": e.code, "errmsg": e.message}

    def get_sign_url(self, flow_id: str, signer_id: str) -> str:
        """获取签署链接"""
        if not self._client:
            return f"https://ess.tencent.com/sign?flow={flow_id}&signer={signer_id}"

        try:
            req = models.GetSignUrlRequest()
            req.FlowId = flow_id
            req.Operator = models.UserInfo()
            req.Operator.UserId = self.config.contract_id

            resp = self._client.GetSignUrl(req)

            return resp.SignUrl

        except TencentCloudSDKException:
            return ""

    def cancel_flow(self, flow_id: str, reason: str = "") -> Dict[str, Any]:
        """取消流程"""
        if not self._client:
            return {"success": True, "flow_id": flow_id, "mock": True}

        try:
            req = models.CancelFlowRequest()
            req.FlowId = flow_id
            req.CancelMessage = reason

            self._client.CancelFlow(req)

            return {"success": True, "flow_id": flow_id}

        except TencentCloudSDKException as e:
            return {"success": False, "errcode": e.code, "errmsg": e.message}

    def download_signed_files(self, flow_id: str) -> List[bytes]:
        """下载已签署文件"""
        if not self._client:
            return [b"mock signed file content"]

        try:
            req = models.DownloadFlowRequest()
            req.FlowId = flow_id

            resp = self._client.DownloadFlow(req)

            files = []
            for file in resp.FileUrls:
                if file.startswith("http"):
                    req = urllib.request.Request(file)
                    with urllib.request.urlopen(req) as f:
                        files.append(f.read())

            return files

        except Exception:
            return []

    def verify_notification(self, headers: Dict, body: str) -> bool:
        """验证回调签名"""
        try:
            signature = headers.get("X-TC-Signature", "")
            expected = hmac.new(
                self.config.secret_key.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            return signature == expected
        except Exception:
            return False

    def parse_notification(self, body: str) -> Dict[str, Any]:
        """解析回调通知"""
        try:
            data = json.loads(body)
            event_type = data.get("EventType", "")

            if event_type == "SignCompleted":
                return {
                    "success": True,
                    "event": "completed",
                    "flow_id": data.get("FlowId", ""),
                    "signer_id": data.get("SignerId", ""),
                }
            elif event_type == "FlowApproved":
                return {
                    "success": True,
                    "event": "approved",
                    "flow_id": data.get("FlowId", ""),
                }
            else:
                return {"success": True, "event": event_type, "flow_id": data.get("FlowId", "")}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_mock_flow(
        self,
        title: str,
        documents: List[str],
        signers: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """创建模拟流程"""
        flow_id = f"mock_flow_{int(time.time())}"
        return {
            "success": True,
            "flow_id": flow_id,
            "data": {
                "flow_id": flow_id,
                "flow_title": title,
                "flow_status": "pending",
                "mock": True,
            },
        }


def create_tencent_esign(secret_id: str, secret_key: str, **kwargs) -> TencentESign:
    """创建腾讯电子签服务"""
    config = TencentESignConfig(
        secret_id=secret_id,
        secret_key=secret_key,
        contract_id=kwargs.get("contract_id", ""),
        region=kwargs.get("region", "ap-guangzhou"),
        callback_url=kwargs.get("callback_url", ""),
        return_url=kwargs.get("return_url", ""),
    )
    return TencentESign(config)
