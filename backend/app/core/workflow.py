"""
工作流引擎 - 解析和执行多 Agent 协作工作流。

支持：
- 顺序执行
- 并行执行
- 依赖关系管理（depends_on）
- 工作流状态管理
- 步骤间上下文共享
"""
import asyncio
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Optional

import yaml

from app.core.agent import AgentEngine, AgentProfile
from app.core.protocol import MultiAgentOrchestrator, AgentStatus

logger = logging.getLogger(__name__)


class StepStatus(str, Enum):
    """工作流步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """工作流步骤定义"""
    id: str                          # 步骤 ID（通常是 agent 名称/角色）
    agent_name: str                  # 执行该步骤的 Agent 名称
    task: str                        # 任务描述
    depends_on: list[str] = field(default_factory=list)  # 依赖的步骤 ID
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    name: str
    display_name: str
    description: str
    agents: list[dict]               # Agent 角色列表
    steps: list[WorkflowStep] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    id: str
    definition: WorkflowDefinition
    status: str = "pending"          # pending, running, completed, failed
    context: dict = field(default_factory=dict)  # 步骤间共享上下文
    current_step_index: int = 0


class WorkflowEngine:
    """
    工作流引擎 - 解析和执行多 Agent 工作流。
    """
    
    def __init__(self, agent_engine: AgentEngine):
        self.agent_engine = agent_engine
        self.orchestrator = MultiAgentOrchestrator(agent_engine)
        self._workflows: dict[str, WorkflowDefinition] = {}
    
    def load_workflow_from_yaml(self, yaml_path: str) -> WorkflowDefinition:
        """
        从 YAML 文件加载工作流定义。
        
        YAML 格式参考 presets/team/dev_team.yaml:
        ```yaml
        name: dev_team
        display_name: 开发团队
        mode: team
        agents:
          - role: architect
            name: 架构师
            responsibility: 系统设计
        workflow:
          - agent: architect
            task: "分析需求"
          - agent: developer
            task: "实现代码"
            depends_on: [architect]
        ```
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        if data.get("mode") != "team":
            raise ValueError(f"非团队模式工作流: {yaml_path}")
        
        # 解析步骤
        steps = []
        for step_data in data.get("workflow", []):
            agent_role = step_data["agent"]
            step = WorkflowStep(
                id=agent_role,
                agent_name=self._resolve_agent_name(agent_role, data.get("agents", [])),
                task=step_data.get("task", ""),
                depends_on=step_data.get("depends_on", []),
            )
            steps.append(step)
        
        definition = WorkflowDefinition(
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            description=data.get("description", ""),
            agents=data.get("agents", []),
            steps=steps,
        )
        
        self._workflows[definition.name] = definition
        return definition
    
    def _resolve_agent_name(self, role: str, agents_config: list[dict]) -> str:
        """
        将角色名映射到实际的 Agent 名称。
        
        团队中的角色可能对应预置 Agent 或使用通用 assistant。
        """
        # 尝试从 agents 配置中找到角色
        for agent in agents_config:
            if agent.get("role") == role:
                # 检查是否有对应的预置 Agent
                # 角色名映射：architect->assistant, developer->coder, reviewer->assistant 等
                role_to_preset = {
                    "architect": "assistant",
                    "developer": "coder",
                    "reviewer": "assistant",
                    "searcher": "researcher",
                    "analyst": "analyst",
                    "writer": "writer",
                }
                return role_to_preset.get(role, "assistant")
        return "assistant"
    
    def load_team_presets(self, presets_dir: str) -> int:
        """加载 presets/team/ 目录下的所有团队工作流"""
        team_dir = os.path.join(presets_dir, "team")
        if not os.path.isdir(team_dir):
            return 0
        
        count = 0
        for filename in os.listdir(team_dir):
            if filename.endswith((".yaml", ".yml")):
                try:
                    filepath = os.path.join(team_dir, filename)
                    self.load_workflow_from_yaml(filepath)
                    count += 1
                    logger.info(f"已加载团队工作流: {filename}")
                except Exception as e:
                    logger.warning(f"加载工作流 {filename} 失败: {e}")
        return count
    
    def get_workflow(self, name: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return self._workflows.get(name)
    
    def list_workflows(self) -> list[WorkflowDefinition]:
        """列出所有工作流"""
        return list(self._workflows.values())
    
    async def execute(self, workflow_name: str, user_task: str) -> dict:
        """
        执行工作流（非流式）。
        
        Args:
            workflow_name: 工作流名称
            user_task: 用户的原始任务描述
            
        Returns:
            dict: 执行结果，包含每个步骤的输出
        """
        definition = self._workflows.get(workflow_name)
        if not definition:
            raise ValueError(f"工作流 '{workflow_name}' 不存在")
        
        # 创建步骤副本（避免修改原定义）
        steps = [
            WorkflowStep(
                id=s.id,
                agent_name=s.agent_name,
                task=s.task,
                depends_on=s.depends_on.copy(),
            )
            for s in definition.steps
        ]
        
        context = {"user_task": user_task}
        results = {}
        
        self.orchestrator.reset()
        
        while True:
            # 找到所有可执行的步骤（依赖都已完成）
            runnable = [
                s for s in steps
                if s.status == StepStatus.PENDING
                and all(
                    any(done.id == dep and done.status == StepStatus.COMPLETED for done in steps)
                    for dep in s.depends_on
                )
            ]
            
            if not runnable:
                # 检查是否所有步骤都完成
                if all(s.status in (StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED) for s in steps):
                    break
                # 死锁检测
                pending = [s for s in steps if s.status == StepStatus.PENDING]
                if pending:
                    logger.error(f"工作流死锁: {[s.id for s in pending]} 无法执行")
                    for s in pending:
                        s.status = StepStatus.SKIPPED
                break
            
            # 并行执行可运行的步骤
            tasks = []
            for step in runnable:
                step.status = StepStatus.RUNNING
                # 构建步骤任务：原始任务 + 步骤特定任务 + 上下文
                full_task = f"用户需求: {user_task}\n\n你的任务: {step.task}"
                
                # 传递依赖步骤的结果作为上下文
                step_context = {}
                for dep_id in step.depends_on:
                    if dep_id in results:
                        step_context[dep_id] = results[dep_id]
                
                tasks.append(self._execute_step(step, full_task, step_context))
            
            # 并行等待所有可执行步骤完成
            step_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for step, result in zip(runnable, step_results):
                if isinstance(result, Exception):
                    step.status = StepStatus.FAILED
                    step.error = str(result)
                    logger.error(f"步骤 '{step.id}' 执行失败: {result}")
                else:
                    step.status = StepStatus.COMPLETED
                    step.result = result
                    results[step.id] = result
                    context[step.id] = result
        
        return {
            "workflow": workflow_name,
            "status": "completed" if all(s.status == StepStatus.COMPLETED for s in steps) else "partial",
            "steps": {
                s.id: {
                    "status": s.status.value,
                    "agent": s.agent_name,
                    "result": s.result,
                    "error": s.error,
                }
                for s in steps
            },
            "final_result": results.get(steps[-1].id, "") if steps else "",
        }
    
    async def _execute_step(self, step: WorkflowStep, task: str, context: dict) -> str:
        """执行单个工作流步骤"""
        logger.info(f"执行步骤: {step.id} (Agent: {step.agent_name})")
        return await self.orchestrator.execute_agent_task(step.agent_name, task, context)
    
    async def execute_stream(self, workflow_name: str, user_task: str) -> AsyncGenerator[dict, None]:
        """
        流式执行工作流，逐步返回状态更新。
        
        Yields:
            dict: 状态更新事件
            - {"type": "step_start", "step_id": "...", "agent": "..."}
            - {"type": "step_token", "step_id": "...", "token": "..."}
            - {"type": "step_complete", "step_id": "...", "result": "..."}
            - {"type": "step_error", "step_id": "...", "error": "..."}
            - {"type": "workflow_complete", "results": {...}}
        """
        definition = self._workflows.get(workflow_name)
        if not definition:
            yield {"type": "error", "message": f"工作流 '{workflow_name}' 不存在"}
            return
        
        steps = [
            WorkflowStep(
                id=s.id, agent_name=s.agent_name, task=s.task, depends_on=s.depends_on.copy()
            )
            for s in definition.steps
        ]
        
        results = {}
        self.orchestrator.reset()
        
        # 逐步执行（流式模式下不并行，方便逐步展示）
        for step in steps:
            # 等待依赖完成
            deps_met = all(
                any(s.id == dep and s.status == StepStatus.COMPLETED for s in steps)
                for dep in step.depends_on
            )
            if not deps_met:
                step.status = StepStatus.SKIPPED
                yield {"type": "step_skip", "step_id": step.id, "reason": "依赖未满足"}
                continue
            
            step.status = StepStatus.RUNNING
            yield {"type": "step_start", "step_id": step.id, "agent": step.agent_name}
            
            full_task = f"用户需求: {user_task}\n\n你的任务: {step.task}"
            step_context = {dep: results[dep] for dep in step.depends_on if dep in results}
            
            try:
                full_content = ""
                async for token in self.orchestrator.execute_agent_task_stream(
                    step.agent_name, full_task, step_context
                ):
                    full_content += token
                    yield {"type": "step_token", "step_id": step.id, "token": token}
                
                step.status = StepStatus.COMPLETED
                step.result = full_content
                results[step.id] = full_content
                yield {"type": "step_complete", "step_id": step.id, "result": full_content}
                
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                yield {"type": "step_error", "step_id": step.id, "error": str(e)}
        
        yield {
            "type": "workflow_complete",
            "results": {s.id: {"status": s.status.value, "result": s.result} for s in steps},
        }
