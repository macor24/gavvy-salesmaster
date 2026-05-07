"""tests/test_scripts.py — 话术训练系统测试

覆盖 Script/ScenesEngine/TrainingSession/Rating 的完整 CRUD 和训练流程。
"""

import tempfile


def test_scripts():
    """测试话术训练系统完整功能"""
    temp_dir = tempfile.mkdtemp()
    print(f"   存储目录: {temp_dir}")

    try:
        from gavvy_salesmaster.core.storage.db import set_storage_dir, get_kernel
        set_storage_dir(temp_dir)
        import gavvy_salesmaster.core.storage.db as db
        db._global_kernel = None

        from gavvy_salesmaster.crm_pkg.scripts import (
            ScriptsEngine, Script, TrainingSession, Rating,
        )

        engine = ScriptsEngine()
        print("✅ ScriptsEngine 初始化成功")

        # ── 场景管理 ──────────────────────────────────────
        print("\n📋 场景管理测试...")

        scenarios = engine.list_scenarios()
        assert len(scenarios) > 0  # 有种子场景
        print(f"  ✅ 种子场景: {len(scenarios)} 个")
        for s in scenarios:
            assert "id" in s
            assert "name" in s
            assert "description" in s
        print("  ✅ 场景结构完整")

        # 获取单个场景
        first_id = scenarios[0]["id"]
        scene = engine.get_scenario(first_id)
        assert scene is not None
        assert "name" in scene
        assert engine.get_scenario("nonexistent") is None
        print("  ✅ 获取场景 / 不存在返回 None")

        # ── 话术 CRUD ────────────────────────────────────
        print("\n💬 话术管理测试...")

        # 创建话术
        script = Script(
            title="首次通话开场白",
            content="您好，我是XX公司的销售顾问...",
            scenario=first_id,
            tags=["开场白", "首次接触"],
            difficulty="beginner",
        )
        saved = engine.add_script(script)
        assert saved["id"] == script.id
        assert saved["title"] == "首次通话开场白"
        assert saved["scenario"] == first_id
        print("  ✅ 创建话术")

        script2 = Script(
            title="异议处理话术",
            content="我理解您的顾虑...",
            scenario=first_id,
            tags=["异议处理"],
        )
        engine.add_script(script2)
        print("  ✅ 创建第二个话术")

        # 列出话术
        all_scripts = engine.list_scripts()
        assert len(all_scripts) >= 2

        by_scene = engine.list_scripts(scenario=first_id)
        assert len(by_scene) >= 2

        by_tag = engine.list_scripts(tag="开场白")
        assert len(by_tag) >= 1
        print("  ✅ 按场景/标签列出话术")

        # 获取话术
        got = engine.get_script(script.id)
        assert got is not None
        assert got["title"] == "首次通话开场白"
        assert engine.get_script("nonexistent") is None
        print("  ✅ 获取话术 / 不存在返回 None")

        # 更新话术
        updated = engine.update_script(script.id, {"title": "更新版开场白", "difficulty": "intermediate"})
        assert updated is not None
        assert updated["title"] == "更新版开场白"
        assert updated["difficulty"] == "intermediate"
        assert engine.update_script("nonexistent", {}) is None
        print("  ✅ 更新话术")

        # 搜索话术
        results = engine.search_scripts("开场白")
        assert len(results) >= 1
        results = engine.search_scripts("不存在的内容")
        assert len(results) == 0
        print("  ✅ 搜索话术")

        # ── 话术评分 ────────────────────────────────────
        print("\n⭐ 话术评分测试...")

        rating = engine.rate_script(script.id, score=4, comment="非常实用", rating_user="test_user")
        assert rating is not None
        assert rating["score"] == 4
        assert rating["rating_user"] == "test_user"

        engine.rate_script(script.id, score=5, comment="完美")
        engine.rate_script(script2.id, score=3, comment="一般")

        ratings = engine.get_ratings(script.id)
        assert len(ratings) == 2
        all_ratings = engine.get_ratings()
        assert len(all_ratings) >= 3
        print("  ✅ 话术评分 / 按话术查评分")

        # ── 模拟训练 ────────────────────────────────────
        print("\n🎯 模拟训练测试...")

        # 开始训练
        session = engine.start_training(scenario=first_id, script_id=script.id)
        assert session is not None
        assert "session_id" in session
        assert session["scenario"] == first_id
        assert session["script_id"] == script.id
        session_id = session["session_id"]
        print(f"  ✅ 开始训练: session_id={session_id[:12]}...")

        # 训练步骤（模拟对话）
        step1 = engine.training_step(session_id, "您好，我是XX公司的...")
        assert step1 is not None
        assert "feedback" in step1
        assert "next_suggestion" in step1
        print(f"  ✅ 训练步骤1: 反馈={step1['feedback'][:30]}...")

        step2 = engine.training_step(session_id, "我们的产品可以帮助贵公司降低成本")
        assert step2 is not None
        print(f"  ✅ 训练步骤2: 反馈={step2['feedback'][:30]}...")

        # 无效 session
        bad_step = engine.training_step("bad_session", "test")
        assert "error" in bad_step
        print("  ✅ 无效 session 返回错误")

        # 完成训练
        completed = engine.complete_training(session_id, score=85)
        assert completed is not None
        assert completed.get("score") == 85
        assert "summary" in completed
        print(f"  ✅ 完成训练: 评分={completed['score']}")

        # 再次完成（重复完成）
        double = engine.complete_training(session_id, score=90)
        assert "error" in double
        print("  ✅ 重复完成返回错误")

        # 列出训练记录
        sessions = engine.list_training_sessions()
        assert len(sessions) >= 1
        by_scene = engine.list_training_sessions(scenario=first_id)
        assert len(by_scene) >= 1
        completed_list = engine.list_training_sessions(scenario=first_id, status="completed")
        assert len(completed_list) >= 1
        print("  ✅ 按场景/状态列出训练记录")

        # ── 话术推荐 ────────────────────────────────────
        print("\n🔍 话术推荐测试...")

        recs = engine.recommend_scripts(scenario=first_id, context="价格敏感型客户")
        assert isinstance(recs, list)
        if recs:
            assert "title" in recs[0]
            assert "score" in recs[0]
            print(f"  ✅ 话术推荐: {len(recs)} 条推荐")

        # ── 话术删除 ────────────────────────────────────
        print("\n🗑️ 话术删除测试...")

        assert engine.delete_script(script2.id) is True
        assert engine.delete_script("nonexistent") is False
        after_delete = engine.list_scripts()
        assert len(after_delete) == len(all_scripts) - 1
        print("  ✅ 删除话术")

        # ── 统计 ────────────────────────────────────
        print("\n📊 统计测试...")
        stats = engine.get_stats()
        assert "total_scripts" in stats
        assert "total_sessions" in stats
        assert "avg_score" in stats
        assert "scenario_count" in stats
        print(f"  ✅ 统计: 话术={stats['total_scripts']}, 训练={stats['total_sessions']}, 均分={stats['avg_score']}")

        print("\n" + "=" * 60)
        print("🎉 所有话术训练测试通过！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print(f"\n清理临时目录: {temp_dir}")
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
