"""工作流路由"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class WorkflowInfo(BaseModel):
    name: str
    display_name: str
    description: str
    steps: list[dict]

class WorkflowExecuteRequest(BaseModel):
    workflow_name: str
    task: str

class WorkflowExecuteResponse(BaseModel):
    workflow: str
    status: str
    steps: dict
    final_result: str


@router.get("/workflows", response_model=list[WorkflowInfo])
async def list_workflows():
    from app.main import get_workflow_engine
    engine = get_workflow_engine()
    workflows = engine.list_workflows()
    return [
        WorkflowInfo(
            name=w.name,
            display_name=w.display_name,
            description=w.description,
            steps=[{"id": s.id, "agent": s.agent_name, "task": s.task, "depends_on": s.depends_on} for s in w.steps],
        )
        for w in workflows
    ]

@router.post("/workflows/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow(req: WorkflowExecuteRequest):
    from app.main import get_workflow_engine
    engine = get_workflow_engine()
    try:
        result = await engine.execute(req.workflow_name, req.task)
        return WorkflowExecuteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workflows/execute/stream")
async def execute_workflow_stream(req: WorkflowExecuteRequest):
    from app.main import get_workflow_engine
    engine = get_workflow_engine()

    async def event_generator():
        try:
            async for event in engine.execute_stream(req.workflow_name, req.task):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
