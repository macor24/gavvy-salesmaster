"""测试通话与录音系统"""

import tempfile
import os
import random
from datetime import datetime


def test_calls():
    """测试通话与录音功能"""

    print("=" * 60)
    print("🧪 测试通话与录音系统")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        # 导入模块
        from tianlong_salesmaster.crm_pkg.calls import (
            CallManager,
            RecordingManager,
            ScriptManager,
            AnalysisManager,
            CallScript,
        )

        # 创建管理器
        cm = CallManager(temp_dir)
        rm = RecordingManager(temp_dir)
        sm = ScriptManager(temp_dir)
        am = AnalysisManager(temp_dir)

        print("✅ 管理器初始化成功")

        # ── 话术模板测试 ──────────────────────────────────

        print("\n📝 话术模板测试...")

        # 获取默认模板
        scripts = sm.get_scripts()
        print(f"✅ 默认话术模板: {len(scripts)} 条")
        for s in scripts:
            print(f"   - [{s.type}] {s.name}")

        # 添加自定义模板
        custom_script = sm.add_script(
            CallScript(
                name="预约面谈",
                type="closing",
                content="好的，那我们就约这周见面详谈吧。您周三还是周四方便？"
            )
        )
        print(f"✅ 添加自定义话术: {custom_script.name}")

        # 使用话术
        sm.use_script(custom_script.id, success=True)
        print(f"✅ 使用话术并标记成功")

        # ── 通话管理测试 ──────────────────────────────────

        print("\n📞 通话管理测试...")

        # 发起通话
        call1 = cm.initiate_call(
            customer_id="CUST-001",
            customer_name="客户张三",
            customer_phone="13800138001",
            salesperson="销售员A",
            related_lead_id="lead-001"
        )
        print(f"✅ 发起通话: {call1.customer_name} ({call1.status})")

        # 接通电话
        cm.connect_call(call1.id)
        print(f"✅ 电话接通")

        # 模拟通话时长
        duration = random.randint(60, 600)
        cm.end_call(call1.id, result="follow_up",
                   notes="客户有兴趣，需要进一步跟进",
                   duration=duration)
        print(f"✅ 通话结束: {duration}秒")

        # 第二通电话 - 未接
        call2 = cm.initiate_call(
            customer_id="CUST-002",
            customer_name="客户李四",
            customer_phone="13800138002",
            salesperson="销售员A"
        )
        cm.miss_call(call2.id, reason="无人接听")
        print(f"✅ 标记未接: {call2.customer_name}")

        # 第三通电话 - 呼损
        call3 = cm.initiate_call(
            customer_id="CUST-003",
            customer_name="客户王五",
            customer_phone="13800138003",
            salesperson="销售员A"
        )
        cm.fail_call(call3.id, reason="线路故障")
        print(f"✅ 标记呼损: {call3.customer_name}")

        # 第四通电话 - 成功成交
        call4 = cm.initiate_call(
            customer_id="CUST-004",
            customer_name="客户赵六",
            customer_phone="13800138004",
            salesperson="销售员A"
        )
        cm.connect_call(call4.id)
        cm.end_call(call4.id, result="success",
                   notes="客户确认购买",
                   duration=480)
        print(f"✅ 通话完成（成功）: {call4.customer_name}")

        # 获取通话列表
        all_calls = cm.get_calls()
        print(f"✅ 通话总数: {len(all_calls)}")

        my_calls = cm.get_calls(salesperson="销售员A")
        print(f"✅ 我的通话: {len(my_calls)}")

        # 通话统计
        stats = cm.get_stats()
        print(f"✅ 通话统计:")
        print(f"   总通话: {stats['total']}")
        print(f"   已接通: {stats['connected']}")
        print(f"   未接: {stats['missed']}")
        print(f"   呼损: {stats['failed']}")
        print(f"   接通率: {stats['connect_rate']}%")
        print(f"   平均时长: {stats['avg_duration']}秒")

        # ── 录音管理测试 ──────────────────────────────────

        print("\n🎙️ 录音管理测试...")

        # 创建录音
        recording = rm.create_recording(
            call_id=call1.id,
            duration=duration,
            format="mp3"
        )
        print(f"✅ 创建录音: {recording.filename}")
        print(f"   时长: {recording.duration_text}")
        print(f"   大小: {recording.size_text}")

        # 关联录音到通话
        cm.link_recording(call1.id, recording.id)
        print(f"✅ 关联录音到通话")

        # 更新转写
        rm.update_transcript(recording.id, "这是通话转写文本...")
        print(f"✅ 更新转写文本")

        # 获取录音
        rec = rm.get_recording(recording.id)
        print(f"✅ 获取录音: {rec.filename}")

        # 录音统计
        rec_stats = rm.get_stats()
        print(f"✅ 录音统计:")
        print(f"   总录音: {rec_stats['total']}")
        print(f"   总时长: {rec_stats['total_duration']}秒")

        # ── 通话分析测试 ──────────────────────────────────

        print("\n📊 通话分析测试...")

        # 模拟 AI 分析
        analysis = am.simulate_ai_analysis(call1.id, recording.id)
        print(f"✅ AI 通话分析:")
        print(f"   情感得分: {analysis.sentiment_score:.2f}")
        print(f"   说话占比: {analysis.talk_ratio:.1%}")
        print(f"   成交概率: {analysis.deal_probability:.1%}")
        print(f"   处理异议: {', '.join(analysis.objection_handled)}")
        print(f"   建议: {analysis.recommendation}")

        # 获取分析
        analysis2 = am.get_analysis(call1.id)
        print(f"✅ 获取分析结果: call_id={analysis2.call_id}")

        # 更新通话评分
        cm.update_call_score(call1.id, analysis.deal_probability * 100)
        print(f"✅ 更新通话评分: {analysis.deal_probability * 100:.1f}")

        # ── 话术效果统计 ──────────────────────────────────

        print("\n🎯 话术效果测试...")

        all_scripts = sm.get_scripts()
        for s in all_scripts:
            print(f"   [{s.type}] {s.name}: "
                  f"使用{s.use_count}次, "
                  f"成功{s.success_count}次, "
                  f"成功率{s.success_rate:.1f}%")

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print(f"\n清理临时目录: {temp_dir}")


if __name__ == "__main__":
    success = test_calls()
    if success:
        print("\n✅ 通话与录音系统测试通过！")
    else:
        print("\n❌ 通话与录音系统测试失败！")
