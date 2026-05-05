"""SentriKit_salesmaster.core.workflow.routes — 工作流 API 路由

提供工作流和事件的 REST API：
- 工作流模板管理
- 工作流实例管理
- 事件历史查询
- 流程可视化数据
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from . import EventType, FlowStatus, StepStatus, WorkflowEvent, WorkflowTemplate
from .engine import get_workflow_engine, WorkflowEngine


router = APIRouter(prefix="/api/workflows", tags=["workflows"])


class WorkflowStartRequest(BaseModel):
    template_id: str
    context: Optional[Dict[str, Any]] = None


class WorkflowCancelRequest(BaseModel):
    reason: str = ""


@router.get("/templates")
async def list_templates():
    """列出工作流模板"""
    engine = get_workflow_engine()
    templates = []
    for t in engine._templates.values():
        templates.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "trigger_event": t.trigger_event,
            "steps_count": len(t.steps),
            "is_active": t.is_active,
        })
    return {"templates": templates}


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """获取模板详情"""
    engine = get_workflow_engine()
    template = engine.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "trigger_event": template.trigger_event,
        "steps": template.steps,
        "is_active": template.is_active,
    }


@router.post("/templates/{template_id}/toggle")
async def toggle_template(template_id: str, is_active: bool):
    """启用/停用模板"""
    engine = get_workflow_engine()
    template = engine.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.is_active = is_active
    return {"success": True, "is_active": is_active}


@router.post("/start")
async def start_workflow(req: WorkflowStartRequest):
    """启动工作流"""
    engine = get_workflow_engine()
    workflow = engine.start_workflow(
        template_id=req.template_id,
        context=req.context,
    )
    if not workflow:
        raise HTTPException(status_code=400, detail="Failed to start workflow")
    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "status": workflow.status,
        "started_at": workflow.started_at,
    }


@router.get("/")
async def list_workflows(
    status: Optional[str] = None,
    limit: int = 100,
):
    """列出工作流实例"""
    engine = get_workflow_engine()
    workflows = engine.list_workflows(status=status, limit=limit)
    return {
        "workflows": [
            {
                "id": w.id,
                "name": w.name,
                "status": w.status,
                "current_step": w.current_step_index,
                "total_steps": len(w.steps),
                "started_at": w.started_at,
                "completed_at": w.completed_at,
                "error": w.error,
            }
            for w in workflows
        ],
        "count": len(workflows),
    }


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """获取工作流详情"""
    engine = get_workflow_engine()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "context": workflow.context,
        "started_at": workflow.started_at,
        "completed_at": workflow.completed_at,
        "error": workflow.error,
        "steps": [
            {
                "id": s.id,
                "name": s.name,
                "action": s.action,
                "status": s.status,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
                "result": s.result,
                "error": s.error,
            }
            for s in workflow.steps
        ],
    }


@router.get("/{workflow_id}/visualize")
async def visualize_workflow(workflow_id: str):
    """获取工作流可视化数据"""
    engine = get_workflow_engine()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    nodes = []
    edges = []

    for i, step in enumerate(workflow.steps):
        node_id = f"step_{i}"
        nodes.append({
            "id": node_id,
            "type": "step",
            "data": {
                "id": step.id,
                "name": step.name,
                "action": step.action,
                "status": step.status,
                "is_current": i == workflow.current_step_index,
            },
        })

        if i > 0:
            edges.append({
                "id": f"edge_{i-1}_{i}",
                "source": f"step_{i-1}",
                "target": node_id,
            })

    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "status": workflow.status,
        "nodes": nodes,
        "edges": edges,
    }


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str, req: WorkflowCancelRequest):
    """取消工作流"""
    engine = get_workflow_engine()
    success = engine.cancel_workflow(workflow_id, req.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"success": True}


@router.get("/{workflow_id}/retry")
async def retry_workflow(workflow_id: str):
    """重试失败的工作流"""
    engine = get_workflow_engine()
    workflow = engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status != FlowStatus.FAILED.value:
        raise HTTPException(status_code=400, detail="Can only retry failed workflows")

    workflow.status = FlowStatus.RUNNING.value
    workflow.error = None
    workflow.current_step_index = 0

    for step in workflow.steps:
        if step.status == StepStatus.FAILED.value:
            step.status = StepStatus.PENDING.value
            step.error = None

    engine._executors[workflow_id].execute_next_step()

    return {"success": True, "workflow_id": workflow.id}


@router.get("/events")
async def list_events(
    event_type: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 100,
):
    """获取事件历史"""
    from . import get_event_bus

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except Exception:
            since_dt = datetime.now() - timedelta(hours=1)

    event_bus = get_event_bus()
    events = event_bus.get_history(event_type=event_type, since=since_dt, limit=limit)

    return {
        "events": [
            {
                "id": e.id,
                "type": e.type,
                "source": e.source,
                "timestamp": e.timestamp,
                "correlation_id": e.correlation_id,
            }
            for e in events
        ],
        "count": len(events),
    }


@router.post("/events/publish")
async def publish_event(
    event_type: str,
    source: str,
    data: Dict[str, Any],
    correlation_id: Optional[str] = None,
):
    """手动发布事件"""
    from . import get_event_bus

    event = WorkflowEvent(
        type=event_type,
        source=source,
        data=data,
        correlation_id=correlation_id or "",
    )

    event_bus = get_event_bus()
    event_bus.publish(event)

    return {"success": True, "event_id": event.id}


@router.get("/stats")
async def get_workflow_stats():
    """获取工作流统计"""
    engine = get_workflow_engine()

    total = len(engine._workflows)
    running = len([w for w in engine._workflows.values() if w.status == FlowStatus.RUNNING.value])
    completed = len([w for w in engine._workflows.values() if w.status == FlowStatus.COMPLETED.value])
    failed = len([w for w in engine._workflows.values() if w.status == FlowStatus.FAILED.value])

    return {
        "total": total,
        "running": running,
        "completed": completed,
        "failed": failed,
        "templates_count": len(engine._templates),
    }
