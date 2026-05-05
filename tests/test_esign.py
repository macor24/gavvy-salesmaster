"""test_esign.py — 电子签章模块测试"""

import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from SentriKit_salesmaster.trade_pkg.esign import (
    ESignProvider, SignStatus, Signer, SignDocument, SignFlow,
    ESignConfig, ByteDanceConfig, TencentConfig,
)


class TestESignTypes(unittest.TestCase):
    """电子签类型枚举测试"""

    def test_provider_values(self):
        self.assertEqual(ESignProvider.BYTEDANCE.value, "bytedance")
        self.assertEqual(ESignProvider.TENCENT.value, "tencent")

    def test_sign_status_values(self):
        self.assertEqual(SignStatus.PENDING.value, "pending")
        self.assertEqual(SignStatus.SIGNED.value, "signed")
        self.assertEqual(SignStatus.REJECTED.value, "rejected")
        self.assertEqual(SignStatus.EXPIRED.value, "expired")


class TestSigner(unittest.TestCase):
    """签署人模型测试"""

    def test_signer_defaults(self):
        s = Signer()
        self.assertNotEqual(s.id, "")
        self.assertEqual(s.status, "pending")

    def test_signer_with_name(self):
        s = Signer(name="张三", mobile="13800138000")
        self.assertEqual(s.name, "张三")
        self.assertEqual(s.mobile, "13800138000")

    def test_signer_with_email(self):
        s = Signer(name="李四", email="lisi@example.com")
        self.assertEqual(s.email, "lisi@example.com")


class TestSignDocument(unittest.TestCase):
    """签署文档测试"""

    def test_document_defaults(self):
        doc = SignDocument()
        self.assertNotEqual(doc.id, "")
        self.assertNotEqual(doc.created_at, "")

    def test_document_with_name(self):
        doc = SignDocument(name="合同.pdf", file_path="/tmp/contract.pdf")
        self.assertEqual(doc.name, "合同.pdf")


class TestSignFlow(unittest.TestCase):
    """签署流程测试"""

    def test_flow_defaults(self):
        flow = SignFlow()
        self.assertNotEqual(flow.id, "")
        self.assertEqual(flow.status, "pending")
        self.assertNotEqual(flow.expires_at, "")

    def test_flow_with_title(self):
        flow = SignFlow(title="销售合同")
        self.assertEqual(flow.title, "销售合同")

    def test_flow_is_completed_empty(self):
        flow = SignFlow()
        self.assertTrue(flow.is_completed)

    def test_flow_pending_signers(self):
        flow = SignFlow(
            signers=[Signer(name="张三", status="signed"), Signer(name="李四", status="pending")]
        )
        self.assertEqual(len(flow.pending_signers), 1)
        self.assertEqual(flow.pending_signers[0].name, "李四")
        self.assertFalse(flow.is_completed)


class TestESignConfigs(unittest.TestCase):
    """电子签配置测试"""

    def test_bytedance_config(self):
        cfg = ByteDanceConfig(app_id="app_001", app_secret="sec_001", corp_name="测试公司")
        self.assertEqual(cfg.provider, "bytedance")
        self.assertEqual(cfg.app_id, "app_001")

    def test_tencent_config(self):
        cfg = TencentConfig(secret_id="ten_001", secret_key="key_001", contract_id="corp_001")
        self.assertEqual(cfg.provider, "tencent")
        self.assertEqual(cfg.secret_id, "ten_001")

    def test_config_defaults(self):
        cfg = ByteDanceConfig()
        self.assertEqual(cfg.provider, "bytedance")


if __name__ == "__main__":
    unittest.main()
