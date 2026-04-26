"""Tests for workflow engine (app.core.workflow)."""
import os
import pytest

from app.core.workflow import (
    StepStatus,
    WorkflowStep,
    WorkflowDefinition,
    WorkflowEngine,
)
from app.core.agent import AgentEngine


# --- StepStatus tests ---

def test_workflow_step_status():
    """StepStatus enum has expected values."""
    assert StepStatus.PENDING == "pending"
    assert StepStatus.RUNNING == "running"
    assert StepStatus.COMPLETED == "completed"
    assert StepStatus.FAILED == "failed"
    assert StepStatus.SKIPPED == "skipped"


# --- WorkflowDefinition tests ---

def test_workflow_definition_creation():
    """WorkflowDefinition can be created with steps."""
    step1 = WorkflowStep(id="step1", agent_name="assistant", task="Do task 1")
    step2 = WorkflowStep(id="step2", agent_name="coder", task="Do task 2")
    
    definition = WorkflowDefinition(
        name="test_wf",
        display_name="Test Workflow",
        description="A test workflow",
        agents=[{"role": "assistant"}, {"role": "coder"}],
        steps=[step1, step2],
    )
    
    assert definition.name == "test_wf"
    assert len(definition.steps) == 2
    assert definition.steps[0].id == "step1"
    assert definition.steps[1].agent_name == "coder"


def test_workflow_step_dependencies():
    """Steps with depends_on properly defined."""
    step1 = WorkflowStep(id="analyze", agent_name="assistant", task="Analyze")
    step2 = WorkflowStep(
        id="implement", agent_name="coder", task="Implement",
        depends_on=["analyze"]
    )
    
    assert step2.depends_on == ["analyze"]
    assert step1.depends_on == []
    assert step1.status == StepStatus.PENDING


# --- WorkflowEngine.load_team_presets tests ---

def test_workflow_engine_load_presets():
    """WorkflowEngine.load_team_presets() finds team YAML files."""
    engine = AgentEngine()
    wf_engine = WorkflowEngine(engine)
    
    # Use the actual presets directory
    presets_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "presets"
    )
    presets_dir = os.path.normpath(presets_dir)
    
    count = wf_engine.load_team_presets(presets_dir)
    # There should be at least some team YAML files in presets/team/
    assert count >= 1
    assert len(wf_engine.list_workflows()) >= 1
