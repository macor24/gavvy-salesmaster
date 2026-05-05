"""SentriKit_salesmaster.trade_pkg.esign.bytedance — 字节跳动电子签集成

真实字节跳动电子签 API 集成，支持：
- 企业实名签署
- 个人签署
- 签署流程管理
- 签署回调处理

API文档: https://open.douyin.com/docs/ebook/e-sign
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import jwt
    _HAS_JWT = True
except ImportError:
    jwt = None
    _HAS_JWT = False


@dataclass
class ByteDanceESignConfig:
    """字节跳动电子签配置"""
    app_id: str = ""
    app_secret: str = ""
    corp_id: str = ""
    corp_name: str = ""
    callback_url: str = ""
    return_url: str = ""
    sandbox: bool = False

    @property
    def api_base_url(self) -> str:
        if self.sandbox:
            return "https://sandbox.douyin.com"
        return "https://open.douyin.com"


class ByteDanceESign:
    """字节跳动电子签服务"""

    def __init__(self, config: ByteDanceESignConfig):
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_access_token(self) -> Optional[str]:
        """获取 access_token"""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        try:
            url = f"{self.config.api_base_url}/oauth/access_token/"
            params = {
                "client_key": self.config.app_id,
                "client_secret": self.config.app_secret,
                "grant_type": "client_credential",
            }

            req = urllib.request.Request(
                url + "?" + urllib.parse.urlencode(params),
                method="GET"
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                if data.get("errcode") == 0:
                    self._access_token = data["data"]["access_token"]
                    self._token_expires_at = time.time() + data["data"]["expires_in"] - 60
                    return self._access_token

        except Exception:
            pass

        return None

    def _make_request(self, method: str, path: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送 API 请求"""
        token = self._get_access_token()
        if not token:
            return {"errcode": 40001, "errmsg": "failed to get access token"}

        url = f"{self.config.api_base_url}{path}"
        headers = {
            "Content-Type": "application/json",
            "Access-Token": token,
        }

        try:
            body = json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=body, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                if result.get("errcode") == 0:
                    return {"success": True, "data": result.get("data", {})}
                return {"success": False, "errcode": result.get("errcode"), "errmsg": result.get("errmsg")}

        except urllib.error.HTTPError as e:
            try:
                error_data = json.loads(e.read().decode())
                return {"success": False, "errcode": e.code, "errmsg": error_data.get("errmsg", str(e))}
            except Exception:
                return {"success": False, "errcode": e.code, "errmsg": str(e)}
        except Exception as e:
            return {"success": False, "errcode": -1, "errmsg": str(e)}

    def create_flow(
        self,
        title: str,
        documents: List[str],
        signers: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """创建签署流程"""
        if not self.config.app_id or self.config.app_id.startswith("mock"):
            return self._create_mock_flow(title, documents, signers, **kwargs)

        signers_data = []
        for i, signer in enumerate(signers):
            signer_info = {
                "signer_mobile": signer.get("mobile", ""),
                "signer_name": signer.get("name", ""),
                "signer_email": signer.get("email", ""),
                "order": i + 1,
            }
            if signer.get("id_card"):
                signer_info["signer_id_card"] = signer["id_card"]
            signers_data.append(signer_info)

        docs_data = []
        for doc_path in documents:
            with open(doc_path, "rb") as f:
                file_content = base64.b64encode(f.read()).decode()
                file_hash = hashlib.sha256(f.read()).hexdigest()

            docs_data.append({
                "file_name": doc_path.split("/")[-1],
                "file_content": file_content,
                "file_hash": file_hash,
            })

        request_data = {
            "flow_title": title,
            "flow_description": kwargs.get("description", ""),
            "signers": signers_data,
            "documents": docs_data,
            "callback_url": self.config.callback_url,
        }

        if self.config.return_url:
            request_data["redirect_url"] = self.config.return_url

        return self._make_request("POST", "/e-sign/cloudapi/flow/create", request_data)

    def send_flow(self, flow_id: str) -> Dict[str, Any]:
        """发送签署流程"""
        if not self.config.app_id:
            return {"success": True, "flow_id": flow_id, "mock": True}

        return self._make_request("POST", "/e-sign/cloudapi/flow/send", {"flow_id": flow_id})

    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """获取流程状态"""
        if not self.config.app_id:
            return {
                "success": True,
                "flow_id": flow_id,
                "status": "pending",
                "signers": [],
                "mock": True,
            }

        result = self._make_request("GET", f"/e-sign/cloudapi/flow/{flow_id}")
        if result.get("success"):
            data = result["data"]
            return {
                "success": True,
                "flow_id": flow_id,
                "status": data.get("flow_status", ""),
                "signers": data.get("signers", []),
            }
        return result

    def get_sign_url(self, flow_id: str, signer_id: str) -> str:
        """获取签署链接"""
        if not self.config.app_id:
            return f"https://bytedance-esign.example.com/sign?flow={flow_id}&signer={signer_id}"

        result = self._make_request(
            "POST",
            "/e-sign/cloudapi/flow/getSignUrl",
            {"flow_id": flow_id, "signer_id": signer_id}
        )

        if result.get("success"):
            return result.get("data", {}).get("sign_url", "")
        return ""

    def cancel_flow(self, flow_id: str, reason: str = "") -> Dict[str, Any]:
        """取消流程"""
        if not self.config.app_id:
            return {"success": True, "flow_id": flow_id, "mock": True}

        return self._make_request(
            "POST",
            "/e-sign/cloudapi/flow/cancel",
            {"flow_id": flow_id, "cancel_reason": reason}
        )

    def download_signed_files(self, flow_id: str) -> List[bytes]:
        """下载已签署文件"""
        if not self.config.app_id:
            return [b"mock signed file content"]

        result = self._make_request("GET", f"/e-sign/cloudapi/flow/{flow_id}/documents")
        if result.get("success"):
            files = []
            for doc in result.get("data", {}).get("documents", []):
                if doc.get("file_content"):
                    files.append(base64.b64decode(doc["file_content"]))
            return files
        return []

    def verify_notification(self, headers: Dict, body: str) -> bool:
        """验证回调签名"""
        if not self.config.app_secret:
            return True

        try:
            signature = headers.get("X-Signature", "")
            expected = hmac.new(
                self.config.app_secret.encode(),
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
            event_type = data.get("event_type", "")
            flow_id = data.get("flow_id", "")

            if event_type == "flow.completed":
                return {
                    "success": True,
                    "event": "completed",
                    "flow_id": flow_id,
                    "signed_files": data.get("signed_files", []),
                }
            elif event_type == "signer.signed":
                return {
                    "success": True,
                    "event": "signed",
                    "flow_id": flow_id,
                    "signer_id": data.get("signer_id", ""),
                }
            else:
                return {"success": True, "event": event_type, "flow_id": flow_id}

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


def create_bytedance_esign(app_id: str, app_secret: str, corp_id: str = "", **kwargs) -> ByteDanceESign:
    """创建字节跳动电子签服务"""
    config = ByteDanceESignConfig(
        app_id=app_id,
        app_secret=app_secret,
        corp_id=corp_id,
        corp_name=kwargs.get("corp_name", ""),
        callback_url=kwargs.get("callback_url", ""),
        return_url=kwargs.get("return_url", ""),
        sandbox=kwargs.get("sandbox", False),
    )
    return ByteDanceESign(config)
