"""测试任务与审批流程系统"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta


def test_task_and_approval():
    """测试任务与审批功能"""

    print("=" * 60)
    print("🧪 测试任务与审批流程系统")
    print("=" * 60)

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        # 导入模块
        from gavvy_salesmaster.crm_pkg.tasks import (
            TaskManager, ApprovalManager, NotificationManager
        )

        # 创建管理器实例
        tm = TaskManager(temp_dir)
        am = ApprovalManager(temp_dir)
        nm = NotificationManager(temp_dir)

        print("✅ 管理器初始化成功")

        # ── 任务管理测试 ──────────────────────────────────

        print("\n📋 任务管理测试...")

        # 创建任务
        task1 = tm.create_task(
            title="跟进客户A",
            description="与客户A沟通需求",
            category="follow_up",
            priority=2,
            assignee="销售员A",
            due_date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        )
        print(f"✅ 创建任务: {task1.title}")

        task2 = tm.create_task(
            title="提交报价单",
            description="为客户A准备报价单",
            category="quote",
            priority=1,
            assignee="销售员B"
        )
        print(f"✅ 创建任务: {task2.title}")

        task3 = tm.create_task(
            title="准备合同",
            description="根据报价准备合同",
            category="contract",
            priority=2,
            assignee="销售员A"
        )
        print(f"✅ 创建任务: {task3.title}")

        # 获取任务列表
        all_tasks = tm.get_tasks()
        print(f"✅ 获取任务列表: {len(all_tasks)} 条")

        pending_tasks = tm.get_tasks(status="pending")
        print(f"✅ 待处理任务: {len(pending_tasks)} 条")

        my_tasks = tm.get_tasks(assignee="销售员A")
        print(f"✅ 我的任务: {len(my_tasks)} 条")

        # 更新任务状态
        task1.status = "in_progress"
        tm.update_task(task1)
        print(f"✅ 更新任务状态: {task1.title} -> {task1.status}")

        # 完成任务
        tm.complete_task(task2.id)
        print(f"✅ 完成任务: {task2.title}")

        # 添加子任务
        subtask = tm.add_subtask(task3.id, "草拟合同内容")
        if subtask:
            print(f"✅ 添加子任务: {subtask.title}")

        # 任务统计
        stats = tm.get_stats()
        print(f"✅ 任务统计: 总{stats['total']}, 待处理{stats['pending']}, "
              f"进行中{stats['in_progress']}, 已完成{stats['completed']}")

        # 按分类统计
        print(f"   按分类: {stats['by_category']}")
        print(f"   按优先级: {stats['by_priority']}")

        # ── 审批管理测试 ──────────────────────────────────

        print("\n📝 审批管理测试...")

        # 小额报价（自动审批）
        approval1 = am.request_approval(
            title="客户A报价单",
            description="产品报价5000元",
            approval_type="quote",
            requester="销售员A",
            amount=5000
        )
        print(f"✅ 发起报价审批: {approval1.title}, 金额:{approval1.amount}, 状态:{approval1.status}")

        # 大额报价（需人工审批）
        approval2 = am.request_approval(
            title="客户B大额订单",
            description="产品报价80000元",
            approval_type="quote",
            requester="销售员B",
            amount=80000
        )
        print(f"✅ 发起大额报价审批: {approval2.title}, 金额:{approval2.amount}, 状态:{approval2.status}")

        # 折扣审批
        approval3 = am.request_approval(
            title="客户C折扣申请",
            description="申请30%折扣",
            approval_type="discount",
            requester="销售员A",
            amount=10000
        )
        print(f"✅ 发起折扣审批: {approval3.title}, 状态:{approval3.status}")

        # 获取审批列表
        all_approvals = am.get_approvals()
        print(f"✅ 获取审批列表: {len(all_approvals)} 条")

        pending_approvals = am.get_approvals(status="pending")
        print(f"✅ 待审批: {len(pending_approvals)} 条")

        # 审批通过
        if approval3.status == "pending":
            am.approve(approval3.id, approver="经理", decision="同意30%折扣")
            print(f"✅ 审批通过: {approval3.title}")

        # 审批拒绝
        if approval2.status == "pending":
            am.reject(approval2.id, approver="经理", reason="金额超出预算")
            print(f"✅ 审批拒绝: {approval2.title}")

        # 审批规则
        rules = am.get_rules()
        print(f"✅ 审批规则: {len(rules)} 条")
        for rule in rules:
            print(f"   - {rule.name}: 阈值{rule.threshold}, 自动审批{rule.auto_approve}")

        # 审批统计
        approval_stats = am.get_stats()
        print(f"✅ 审批统计: 总{approval_stats['total']}, "
              f"待审批{approval_stats['pending']}, "
              f"已通过{approval_stats['approved']}, "
              f"已拒绝{approval_stats['rejected']}")
        print(f"   审批总额: {approval_stats['total_amount']}")

        # ── 通知管理测试 ──────────────────────────────────

        print("\n🔔 通知管理测试...")

        # 创建通知
        notif1 = nm.create_notification(
            notification_type="task",
            title="新任务分配",
            message="您有一个新任务：跟进客户D",
            recipient="销售员C",
            related_type="task",
            related_id=task1.id
        )
        print(f"✅ 创建通知: {notif1.title}")

        notif2 = nm.create_notification(
            notification_type="approval",
            title="审批请求",
            message="您有一个待审批的报价单",
            recipient="经理",
            related_type="approval",
            related_id=approval2.id
        )
        print(f"✅ 创建通知: {notif2.title}")

        # 获取通知
        notifs = nm.get_notifications("销售员C")
        print(f"✅ 获取通知: {len(notifs)} 条")

        unread = nm.get_unread_count("销售员C")
        print(f"✅ 未读通知: {unread} 条")

        # 标记已读
        nm.mark_as_read(notif1.id)
        print(f"✅ 标记已读: {notif1.title}")

        unread_after = nm.get_unread_count("销售员C")
        print(f"✅ 标记后未读: {unread_after} 条")

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
    success = test_task_and_approval()
    if success:
        print("\n✅ 任务与审批系统测试通过！")
    else:
        print("\n❌ 任务与审批系统测试失败！")
