"""测试工作流引擎"""

import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir / "src"))


def test_event_bus():
    """测试事件总线"""
    from SentriKit_salesmaster.core.workflow import EventBus, WorkflowEvent, EventType

    bus = EventBus()
    events_received = []

    def handler(event: WorkflowEvent):
        events_received.append(event)

    bus.subscribe(EventType.QUOTE_APPROVED.value, handler)

    event = WorkflowEvent(
        type=EventType.QUOTE_APPROVED.value,
        source="test",
        data={"quote_id": "q001", "amount": 1000},
    )

    bus.publish(event)

    assert len(events_received) == 1
    assert events_received[0].type == EventType.QUOTE_APPROVED.value
    print("✅ EventBus: OK")
    return True


def test_workflow_creation():
    """测试工作流创建"""
    from SentriKit_salesmaster.core.workflow import Workflow, WorkflowStep, StepStatus

    workflow = Workflow(
        name="Test Workflow",
        description="Test workflow description",
    )

    step1 = WorkflowStep(
        id="step1",
        name="Step 1",
        action="test.action1",
    )
    step2 = WorkflowStep(
        id="step2",
        name="Step 2",
        action="test.action2",
    )

    workflow.steps.extend([step1, step2])

    assert len(workflow.steps) == 2
    assert workflow.current_step.id == "step1"
    assert workflow.current_step_index == 0

    print("✅ Workflow creation: OK")
    return True


def test_workflow_engine():
    """测试工作流引擎"""
    from SentriKit_salesmaster.core.workflow.engine import WorkflowEngine, get_workflow_engine

    engine = get_workflow_engine()

    templates = list(engine._templates.keys())
    assert "quote_to_contract" in templates
    assert "contract_to_payment" in templates
    assert "lead_qualification" in templates

    workflow = engine.start_workflow(
        template_id="quote_to_contract",
        context={
            "quote_id": "q001",
            "quote_title": "测试报价单",
            "amount": 9999,
            "customer_id": "c001",
        },
    )

    assert workflow is not None
    assert workflow.name == "报价转合同"
    assert len(workflow.steps) == 3
    assert workflow.status in ("running", "completed")

    print("✅ Workflow engine: OK")
    return True


def test_workflow_execution():
    """测试工作流执行"""
    from SentriKit_salesmaster.core.workflow.engine import get_workflow_engine
    from SentriKit_salesmaster.core.workflow import FlowStatus, StepStatus

    engine = get_workflow_engine()

    workflow = engine.start_workflow(
        template_id="lead_qualification",
        context={
            "lead_id": "l001",
            "name": "张三",
            "company": "测试公司",
            "email": "zhangsan@example.com",
        },
    )

    assert workflow is not None
    assert workflow.status in (FlowStatus.RUNNING.value, FlowStatus.COMPLETED.value)

    print("✅ Workflow execution: OK")
    return True


def test_workflow_event_publishing():
    """测试工作流事件发布"""
    from SentriKit_salesmaster.core.workflow import get_event_bus, EventType, WorkflowEvent

    bus = get_event_bus()

    workflow_started = []

    def on_workflow_started(event: WorkflowEvent):
        if event.type == EventType.WORKFLOW_STEP.value:
            workflow_started.append(event)

    bus.subscribe_wildcard(on_workflow_started)

    event = WorkflowEvent(
        type=EventType.WORKFLOW_STEP.value,
        source="test",
        data={"workflow_id": "w001", "action": "started"},
    )

    bus.publish(event)

    assert len(workflow_started) == 1
    print("✅ Workflow event publishing: OK")
    return True


def test_workflow_templates():
    """测试工作流模板"""
    from SentriKit_salesmaster.core.workflow.engine import get_workflow_engine
    from SentriKit_salesmaster.core.workflow import EventType

    engine = get_workflow_engine()

    template = engine.get_template("quote_to_contract")
    assert template is not None
    assert template.trigger_event == EventType.QUOTE_APPROVED.value
    assert len(template.steps) == 3

    template = engine.get_template("contract_to_payment")
    assert template is not None
    assert template.trigger_event == EventType.CONTRACT_COMPLETED.value

    print("✅ Workflow templates: OK")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Workflow Engine")
    print("=" * 60)
    print()

    tests = [
        ("EventBus", test_event_bus),
        ("Workflow creation", test_workflow_creation),
        ("Workflow engine", test_workflow_engine),
        ("Workflow execution", test_workflow_execution),
        ("Workflow event publishing", test_workflow_event_publishing),
        ("Workflow templates", test_workflow_templates),
    ]

    passed = 0
    for name, test_func in tests:
        print(f"Testing {name}...")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            import traceback
            traceback.print_exc()
        print()

    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print("=" * 60)

    if passed == len(tests):
        print("\n✅ All workflow tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) failed")
        sys.exit(1)
