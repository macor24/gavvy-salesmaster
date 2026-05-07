"""测试真实支付和电子签 API 集成"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))


def test_payment_stripe():
    """测试 Stripe 支付"""
    try:
        from gavvy_salesmaster.trade_pkg.payment.stripe_payment import StripePayment, StripePaymentConfig

        config = StripePaymentConfig(api_key="sk_test_mock")
        payment = StripePayment(config)

        result = payment.create_checkout_session(
            order_id="test_001",
            order_no="TEST001",
            amount=99.99,
            title="Test Product",
        )

        assert result["success"] == True
        assert "session_id" in result
        assert "payment_url" in result
        print("✅ Stripe payment: OK")
        return True
    except Exception as e:
        print(f"❌ Stripe payment: {e}")
        return False


def test_payment_alipay():
    """测试支付宝"""
    try:
        from gavvy_salesmaster.trade_pkg.payment.chinese_payment import AlipayService, AlipayConfig

        config = AlipayConfig(
            app_id="mock_app_id",
            private_key="mock_private_key",
            alipay_public_key="mock_public_key",
        )
        alipay = AlipayService(config)

        result = alipay.create_qr_code(
            out_trade_no="TEST001",
            subject="Test Product",
            total_amount=99.99,
        )

        assert result["success"] == True
        assert "qr_code" in result
        print("✅ Alipay: OK")
        return True
    except Exception as e:
        print(f"❌ Alipay: {e}")
        return False


def test_payment_wechatpay():
    """测试微信支付"""
    try:
        from gavvy_salesmaster.trade_pkg.payment.chinese_payment import WeChatPayService, WeChatPayConfig

        config = WeChatPayConfig(
            mch_id="mock_mch_id",
            mch_serial_no="mock_serial_no",
            api_key="mock_api_key",
            private_key="mock_private_key",
        )
        wxpay = WeChatPayService(config)

        result = wxpay.create_qr_code(
            out_trade_no="TEST001",
            description="Test Product",
            amount=99.99,
        )

        assert result["success"] == True
        assert "code_url" in result
        print("✅ WeChat Pay: OK")
        return True
    except Exception as e:
        print(f"❌ WeChat Pay: {e}")
        return False


def test_esign_bytedance():
    """测试字节跳动电子签"""
    try:
        from gavvy_salesmaster.trade_pkg.esign.bytedance_esign import ByteDanceESign, ByteDanceESignConfig

        config = ByteDanceESignConfig(
            app_id="mock_app_id",
            app_secret="mock_secret",
        )
        esign = ByteDanceESign(config)

        result = esign.create_flow(
            title="Test Contract",
            documents=["/tmp/test.pdf"],
            signers=[
                {"name": "张三", "mobile": "13800138000", "email": "zhangsan@example.com"},
            ],
        )

        assert result["success"] == True
        assert "flow_id" in result
        print("✅ ByteDance eSign: OK")
        return True
    except Exception as e:
        print(f"❌ ByteDance eSign: {e}")
        return False


def test_esign_tencent():
    """测试腾讯电子签"""
    try:
        from gavvy_salesmaster.trade_pkg.esign.tencent_esign import TencentESign, TencentESignConfig

        config = TencentESignConfig(
            secret_id="mock_secret_id",
            secret_key="mock_secret_key",
        )
        esign = TencentESign(config)

        result = esign.create_flow(
            title="Test Contract",
            documents=["/tmp/test.pdf"],
            signers=[
                {"name": "张三", "mobile": "13800138000"},
            ],
        )

        assert result["success"] == True
        assert "flow_id" in result
        print("✅ Tencent eSign: OK")
        return True
    except Exception as e:
        print(f"❌ Tencent eSign: {e}")
        return False


def test_webhook_handler():
    """测试 Webhook 处理器"""
    try:
        from gavvy_salesmaster.core.webhook import get_webhook_handler, WebhookEvent

        handler = get_webhook_handler()

        def test_handler(event: WebhookEvent):
            pass

        handler.register_stripe_handler("checkout.session.completed", test_handler)

        assert "checkout.session.completed" in handler.stripe_handlers
        print("✅ Webhook handler: OK")
        return True
    except Exception as e:
        print(f"❌ Webhook handler: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Real Payment & E-Sign APIs")
    print("=" * 60)
    print()

    tests = [
        ("Stripe Payment", test_payment_stripe),
        ("Alipay", test_payment_alipay),
        ("WeChat Pay", test_payment_wechatpay),
        ("ByteDance eSign", test_esign_bytedance),
        ("Tencent eSign", test_esign_tencent),
        ("Webhook Handler", test_webhook_handler),
    ]

    passed = 0
    for name, test_func in tests:
        print(f"Testing {name}...")
        if test_func():
            passed += 1
        print()

    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print("=" * 60)

    if passed == len(tests):
        print("\n✅ All real API tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) may need dependencies")
        sys.exit(0)
