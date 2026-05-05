"""test_compliance.py — 数据合规模块测试

覆盖：
  1. 脱敏函数 — 所有 PII 字段脱敏正确性
  2. ComplianceGuard — sanitize_lead/session/log 集成
  3. PII 检测 — contains_pii / pii_fields_exposed
  4. 留存策略 — is_expired / purge_expired
  5. 审计日志 — log_access / log_export / log_delete
  6. 集成测试 — DataRepository + 合规自动脱敏
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from SentriKit_salesmaster.core.storage.compliance import (
    ComplianceGuard, mask_pii, PII_CLASSIFICATION,
    RetentionPolicy, get_compliance_guard,
)
from SentriKit_salesmaster.core.storage import (
    DatabaseKernel, DataRepository,
)


# ═══════════════════════════════════════════════════════
# 脱敏函数测试
# ═══════════════════════════════════════════════════════

class TestMaskPII(unittest.TestCase):
    """PII 脱敏函数单元测试"""

    def test_mask_middle_phone(self):
        """手机号中间脱敏"""
        result = mask_pii("13812345678", "mask_middle")
        self.assertEqual(result, "138****5678")

    def test_mask_middle_short(self):
        """短字符串防崩溃"""
        result = mask_pii("12", "mask_middle")
        self.assertTrue("*" in result)

    def test_mask_middle_empty(self):
        """空字符串原样返回"""
        result = mask_pii("", "mask_middle")
        self.assertEqual(result, "")

    def test_mask_middle_non_string(self):
        """非字符串原样返回"""
        result = mask_pii(12345, "mask_middle")
        self.assertEqual(result, 12345)

    def test_mask_email(self):
        """邮箱脱敏"""
        result = mask_pii("user@example.com", "mask_email")
        self.assertEqual(result, "u***@example.com")

    def test_mask_email_short(self):
        """短邮箱名脱敏"""
        result = mask_pii("ab@test.com", "mask_email")
        self.assertEqual(result, "a***@test.com")

    def test_mask_name_two_chars(self):
        """两字姓名"""
        result = mask_pii("张三", "mask_name")
        self.assertEqual(result, "张*")

    def test_mask_name_three_chars(self):
        """三字姓名"""
        result = mask_pii("王小明", "mask_name")
        self.assertEqual(result, "王**")

    def test_mask_name_single(self):
        """单字"""
        result = mask_pii("李", "mask_name")
        self.assertEqual(result, "李*")

    def test_mask_id_card(self):
        """身份证脱敏"""
        result = mask_pii("110101199001011234", "mask_id_card")
        self.assertEqual(result, "110101********1234")

    def test_mask_address(self):
        """地址脱敏"""
        result = mask_pii("北京市海淀区中关村大街1号", "mask_address")
        self.assertEqual(result, "北京市海淀区**")

    def test_mask_wechat(self):
        """微信号脱敏"""
        result = mask_pii("wechat_abc123", "mask_prefix")
        self.assertIn("*", result)
        self.assertTrue(result.startswith("wec"))

    def test_mask_partial(self):
        """企业名部分脱敏"""
        result = mask_pii("深圳腾讯科技有限公司", "partial")
        self.assertIn("*", result)
        self.assertTrue(result.startswith("深圳"))

    def test_mask_partial_short(self):
        """短企业名脱敏"""
        result = mask_pii("某公司", "partial")
        self.assertEqual(result, "某**")

    def test_none_method(self):
        """none 方法原样返回"""
        result = mask_pii("hello world", "none")
        self.assertEqual(result, "hello world")

    def test_unknown_method(self):
        """未知方法原样返回"""
        result = mask_pii("test", "unknown_method")
        self.assertEqual(result, "test")


# ═══════════════════════════════════════════════════════
# ComplianceGuard 测试
# ═══════════════════════════════════════════════════════

class TestComplianceGuard(unittest.TestCase):
    """合规守卫集成测试"""

    def setUp(self):
        self.guard = ComplianceGuard()

    def test_sanitize_lead_masks_phone(self):
        """sanitize_lead 脱敏手机号"""
        lead = {"id": "L1", "company": "测试公司", "phone": "13812345678"}
        clean = self.guard.sanitize_lead(lead)
        self.assertEqual(clean["phone"], "138****5678")

    def test_sanitize_lead_masks_email(self):
        """sanitize_lead 脱敏邮箱"""
        lead = {"id": "L1", "email": "user@example.com"}
        clean = self.guard.sanitize_lead(lead)
        self.assertIn("***", clean["email"])
        self.assertNotIn("user@", clean["email"])

    def test_sanitize_lead_masks_contact(self):
        """sanitize_lead 脱敏联系方式"""
        lead = {"id": "L1", "contact": "wechat_abc"}
        clean = self.guard.sanitize_lead(lead)
        self.assertIn("*", clean["contact"])

    def test_sanitize_lead_keeps_business(self):
        """sanitize_lead 保留业务字段"""
        lead = {"id": "L1", "company": "测试公司", "industry": "AI"}
        clean = self.guard.sanitize_lead(lead)
        self.assertEqual(clean["company"], "测试公司")  # L1 级别
        self.assertEqual(clean["industry"], "AI")

    def test_sanitize_lead_no_mutation(self):
        """sanitize_lead 不修改原数据"""
        original = {"id": "L1", "phone": "13812345678"}
        clean = self.guard.sanitize_lead(original)
        self.assertEqual(original["phone"], "13812345678")
        self.assertNotEqual(clean["phone"], original["phone"])

    def test_sanitize_session_masks_name(self):
        """sanitize_session 脱敏客户名"""
        session = {"session_id": "S1", "lead_name": "张三"}
        clean = self.guard.sanitize_session(session)
        self.assertEqual(clean["lead_name"], "张*")

    def test_sanitize_session_masks_customer_name(self):
        """sanitize_session 脱敏 customer_name"""
        session = {"session_id": "S1", "customer_name": "李四"}
        clean = self.guard.sanitize_session(session)
        self.assertEqual(clean["customer_name"], "李*")

    def test_sanitize_session_adds_flag(self):
        """sanitize_session 添加脱敏标记"""
        clean = self.guard.sanitize_session({"session_id": "S1"})
        self.assertTrue(clean.get("_pii_checked"))

    def test_sanitize_safety_log_masks_customer(self):
        """sanitize_safety_log 脱敏客户名"""
        log = {"agent": "presales", "customer": "王小明", "action": "quote"}
        clean = self.guard.sanitize_safety_log(log)
        self.assertEqual(clean["customer"], "王**")
        self.assertIn("*", clean["agent"])  # agent 名也会脱敏

    def test_sanitize_value_by_hint(self):
        """sanitize_value 按字段名脱敏"""
        result = self.guard.sanitize_value("13812345678", "phone")
        self.assertEqual(result, "138****5678")

    def test_sanitize_value_no_hint(self):
        """sanitize_value 无匹配则原样"""
        result = self.guard.sanitize_value("hello", "unknown_field")
        self.assertEqual(result, "hello")

    # ── PII 检测 ──

    def test_contains_pii_detects(self):
        """contains_pii 检测到 PII"""
        data = {"id": "L1", "phone": "13812345678", "email": "test@test.com"}
        found = ComplianceGuard.contains_pii(data)
        self.assertIn("phone", found)
        self.assertIn("email", found)

    def test_contains_pii_ignores_low_level(self):
        """contains_pii 忽略 L1 级别字段"""
        data = {"company": "测试公司", "industry": "AI"}
        found = ComplianceGuard.contains_pii(data)
        # company 是 L1，不返回
        self.assertEqual(found, [])

    def test_pii_fields_exposed(self):
        """pii_fields_exposed 检测未脱敏字段"""
        data = {"phone": "13812345678", "name": "张三*"}  # name 已脱敏
        exposed = ComplianceGuard.pii_fields_exposed(data)
        self.assertIn("phone", exposed)
        self.assertNotIn("name", exposed)

    # ── 留存策略 ──

    def test_is_expired(self):
        """is_expired 检测过期"""
        from datetime import datetime, timedelta
        old_ts = (datetime.now() - timedelta(days=400)).isoformat()
        self.assertTrue(self.guard.is_expired(old_ts, 365))
        recent_ts = (datetime.now() - timedelta(days=30)).isoformat()
        self.assertFalse(self.guard.is_expired(recent_ts, 365))

    def test_is_expired_zero_keeps_forever(self):
        """0 天 = 永久"""
        old_ts = "2020-01-01T00:00:00"
        self.assertFalse(self.guard.is_expired(old_ts, 0))

    def test_is_expired_empty(self):
        """空时间戳不视为过期"""
        self.assertFalse(self.guard.is_expired("", 30))

    def test_purge_expired_dict(self):
        """purge_expired 清理 dict 中过期项"""
        from datetime import datetime, timedelta
        old_ts = (datetime.now() - timedelta(days=400)).isoformat()
        data = {
            "fresh": {"updated_at": datetime.now().isoformat()},
            "stale": {"updated_at": old_ts},
        }
        cleaned = self.guard.purge_expired("leads", data)
        self.assertIn("fresh", cleaned)
        self.assertNotIn("stale", cleaned)

    def test_purge_expired_list(self):
        """purge_expired 清理 list 中过期项"""
        from datetime import datetime, timedelta
        old_ts = (datetime.now() - timedelta(days=400)).isoformat()
        data = [
            {"timestamp": datetime.now().isoformat()},
            {"timestamp": old_ts},
        ]
        cleaned = self.guard.purge_expired("sessions", data)
        self.assertEqual(len(cleaned), 1)

    def test_purge_expired_permanent(self):
        """永久保留的集合不清除"""
        from datetime import datetime, timedelta
        old_ts = (datetime.now() - timedelta(days=400)).isoformat()
        data = {"a": {"updated_at": old_ts}, "b": {"updated_at": old_ts}}
        cleaned = self.guard.purge_expired("product_config", data)
        self.assertEqual(len(cleaned), 2)

    def test_purge_bad_timestamp(self):
        """无效时间戳不清除"""
        data = [{"timestamp": "invalid-date"}]
        cleaned = self.guard.purge_expired("sessions", data)
        self.assertEqual(len(cleaned), 1)

    # ── 审计日志 ──

    def test_log_access(self):
        """log_access 记录访问"""
        self.guard.log_access("read", "leads", "L1", user="admin")
        logs = self.guard.get_audit_log()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["operation"], "read")
        self.assertEqual(logs[0]["collection"], "leads")

    def test_log_export(self):
        """log_export 记录导出"""
        self.guard.log_export("leads", 10, user="admin")
        logs = self.guard.get_audit_log()
        self.assertEqual(logs[0]["operation"], "export")
        self.assertIn("10", logs[0]["detail"])

    def test_log_delete(self):
        """log_delete 记录删除"""
        self.guard.log_delete("sessions", "S1", user="user1", reason="用户请求")
        logs = self.guard.get_audit_log()
        self.assertEqual(logs[0]["operation"], "delete")
        self.assertIn("用户请求", logs[0]["detail"])

    def test_get_audit_log_limit(self):
        """get_audit_log 限制数量"""
        for i in range(200):
            self.guard.log_access("read", "leads", f"L{i}")
        logs = self.guard.get_audit_log(limit=50)
        self.assertLessEqual(len(logs), 50)

    def test_clear_audit_log(self):
        """clear_audit_log 清空"""
        self.guard.log_access("read", "leads", "L1")
        self.guard.clear_audit_log()
        logs = self.guard.get_audit_log()
        self.assertEqual(len(logs), 0)

    # ── 合规报告 ──

    def test_compliance_report_structure(self):
        """compliance_report 返回完整结构"""
        report = self.guard.compliance_report()
        self.assertIn("pii_classification_count", report)
        self.assertIn("retention_policy", report)
        self.assertIn("compliance_basis", report)
        self.assertIn("generated_at", report)


# ═══════════════════════════════════════════════════════
# PII 分类定义测试
# ═══════════════════════════════════════════════════════

class TestPIIClassification(unittest.TestCase):
    """PII 分类定义完整性测试"""

    def test_all_fields_have_method(self):
        """所有分类字段都有脱敏方法"""
        for field, info in PII_CLASSIFICATION.items():
            self.assertIn("method", info, f"{field} 缺少 method")
            self.assertIn("level", info, f"{field} 缺少 level")

    def test_level_range(self):
        """分级在 1-3 范围内"""
        for field, info in PII_CLASSIFICATION.items():
            self.assertGreaterEqual(info["level"], 1)
            self.assertLessEqual(info["level"], 3)

    def test_l3_fields_direct_identifiers(self):
        """L3 字段包含直接标识符"""
        l3_fields = [f for f, v in PII_CLASSIFICATION.items() if v["level"] == 3]
        self.assertIn("phone", l3_fields)
        self.assertIn("email", l3_fields)
        self.assertIn("id_card", l3_fields)
        self.assertIn("address", l3_fields)

    def test_no_duplicate_classifications(self):
        """无重复字段名"""
        field_names = list(PII_CLASSIFICATION.keys())
        self.assertEqual(len(field_names), len(set(field_names)))


# ═══════════════════════════════════════════════════════
# 集成测试：DataRepository + 合规自动脱敏
# ═══════════════════════════════════════════════════════

class TestRepositoryCompliance(unittest.TestCase):
    """DataRepository 自动合规脱敏集成测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.kernel = DatabaseKernel(self.tmpdir)
        self.repo = DataRepository(self.kernel)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_lead_auto_masks_phone(self):
        """save_lead 自动脱敏手机号"""
        self.repo.save_lead({
            "id": "L1", "company": "某科技",
            "phone": "13812345678",
        })
        stored = self.repo.get_lead("L1")
        self.assertIsNotNone(stored)
        self.assertEqual(stored["phone"], "138****5678")

    def test_save_lead_auto_masks_email(self):
        """save_lead 自动脱敏邮箱"""
        self.repo.save_lead({
            "id": "L2", "email": "user@example.com",
        })
        stored = self.repo.get_lead("L2")
        self.assertIn("***", stored["email"])

    def test_save_lead_keeps_business_fields(self):
        """save_lead 保留业务字段"""
        self.repo.save_lead({
            "id": "L3", "company": "测试公司",
            "industry": "AI Agent", "stage": "discovery",
        })
        stored = self.repo.get_lead("L3")
        self.assertEqual(stored["company"], "测试公司")
        self.assertEqual(stored["stage"], "discovery")

    def test_save_session_auto_masks_name(self):
        """save_session 自动脱敏客户名"""
        self.repo.save_session({
            "session_id": "S1", "lead_name": "张三",
        })
        stored = self.repo.get_session("S1")
        self.assertEqual(stored["lead_name"], "张*")

    def test_save_safety_log_auto_masks_customer(self):
        """save_safety_log 自动脱敏客户名"""
        self.repo.save_safety_log({
            "agent": "presales", "customer": "王小明",
            "action": "quote", "approved": False,
        })
        logs = self.repo.list_safety_logs()
        self.assertEqual(len(logs), 1)
        self.assertIn("*", logs[0]["customer"])
        self.assertIn("*", logs[0]["agent"])

    def test_product_config_not_affected(self):
        """product_config 不含 PII"""
        cfg = {"name": "测试产品", "price_max": 999}
        self.repo.save_product_config(cfg)
        loaded = self.repo.get_product_config()
        self.assertEqual(loaded["name"], "测试产品")


# ═══════════════════════════════════════════════════════
# RetentionPolicy 测试
# ═══════════════════════════════════════════════════════

class TestRetentionPolicy(unittest.TestCase):
    """留存策略测试"""

    def test_default_values(self):
        p = RetentionPolicy.default()
        self.assertEqual(p.leads, 365)
        self.assertEqual(p.sessions, 180)
        self.assertEqual(p.safety_logs, 90)
        self.assertEqual(p.product_config, 0)

    def test_get_days(self):
        p = RetentionPolicy.default()
        self.assertEqual(p.get_days("leads"), 365)
        self.assertEqual(p.get_days("unknown"), 0)  # 不存在的集合返回 0

    def test_to_dict(self):
        p = RetentionPolicy.default()
        d = p.to_dict()
        self.assertIn("leads", d)
        self.assertIn("sessions", d)


# ═══════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main()
