#!/usr/bin/env python3
"""gavvy-auto-hunt.py — 自动寻客 + Pipeline 超时检查

被 Cron 调用：每6小时跑一次寻客，每30分钟跑一次超时检查。
用法: python gavvy-auto-hunt.py [hunt|timeout|all]
"""

import json
import os
import sys
import time
from datetime import datetime


def run_hunt():
    """触发寻客引擎"""
    try:
        from gavvy_salesmaster.crm_pkg.lead_gen.hunt_engine import HuntEngine
        from gavvy_salesmaster.crm_pkg.lead_gen.scheduler import AutoScheduler
        from gavvy_salesmaster.team_pkg.team.coordinator import SalesOrchestrator
        
        orch = SalesOrchestrator()
        engine = HuntEngine()
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始寻客...")
        result = engine.run_hunt()
        
        print(f"  寻客完成:")
        print(f"    总发现: {result.total_found}")
        print(f"    新增:   {result.new_added}")
        print(f"    总线索: {result.total_leads}")
        print(f"    耗时:   {result.duration_seconds}s")
        if result.errors:
            print(f"    错误:   {result.errors}")
        
        # 自动调度高分线索
        scheduler = AutoScheduler(hunt_engine=engine, orchestrator=orch)
        dispatched = scheduler.dispatch_from_hunt()
        print(f"    调度:   {dispatched} 个线索已分配Agent")
        
        # 保存 Orchestrator 状态
        orch.persist()
        
        return result
    except Exception as e:
        print(f"[ERROR] 寻客失败: {e}")
        return None


def run_timeout_check():
    """Pipeline 超时检查 + 自动推进"""
    try:
        from gavvy_salesmaster.team_pkg.team.coordinator import PipelineTrigger, SalesOrchestrator
        
        orch = SalesOrchestrator()
        orch.restore()
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pipeline 超时检查...")
        alerts = PipelineTrigger.check_timeouts(orch)
        print(f"  超时线索: {len(alerts)}")
        for a in alerts:
            print(f"    - {a.get('company', '?')} ({a.get('stage', '?')}) 超时 {a.get('overdue_hours', 0):.0f}h")
        
        # 自动推进超时线索
        result = PipelineTrigger.auto_follow_up(orch, external_save_func=orch.persist)
        print(f"  自动推进: {result}")
        
        return alerts
    except Exception as e:
        print(f"[ERROR] 超时检查失败: {e}")
        return []


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if mode == "hunt":
        run_hunt()
    elif mode == "timeout":
        run_timeout_check()
    else:
        print("=== gavvy 自动引擎 ===")
        run_hunt()
        print()
        run_timeout_check()
        print()
        print("=== 完成 ===")
