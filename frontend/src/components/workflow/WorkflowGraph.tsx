"use client";

import { useCallback, useMemo } from "react";
import ReactFlow, {
  Node,
  Edge,
  Position,
  Handle,
  NodeProps,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  Background,
  Controls,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import type { WorkflowInfo } from "@/types";
import { useWorkflowStore } from "@/stores/workflowStore";
import { cn } from "@/lib/utils";

/** Agent 图标映射 */
const agentIcons: Record<string, string> = {
  architect: "🏗️",
  designer: "🎨",
  developer: "💻",
  tester: "🧪",
  reviewer: "👀",
  writer: "✍️",
  researcher: "🔬",
  analyst: "📊",
  translator: "🌐",
  assistant: "🤖",
  coder: "👨‍💻",
  default: "🤖",
};

/** 获取 Agent 图标 */
function getAgentIcon(agent: string): string {
  const key = agent.toLowerCase();
  for (const [k, v] of Object.entries(agentIcons)) {
    if (key.includes(k)) return v;
  }
  return agentIcons.default;
}

/** 状态颜色配置 */
const statusColors = {
  pending: {
    border: "border-gray-300 dark:border-gray-600",
    bg: "bg-gray-50 dark:bg-gray-800",
    indicator: "bg-gray-400",
    text: "text-gray-500",
    label: "等待中",
  },
  running: {
    border: "border-blue-400 dark:border-blue-500",
    bg: "bg-blue-50 dark:bg-blue-900/30",
    indicator: "bg-blue-500",
    text: "text-blue-600 dark:text-blue-400",
    label: "运行中",
  },
  completed: {
    border: "border-green-400 dark:border-green-500",
    bg: "bg-green-50 dark:bg-green-900/30",
    indicator: "bg-green-500",
    text: "text-green-600 dark:text-green-400",
    label: "已完成",
  },
  error: {
    border: "border-red-400 dark:border-red-500",
    bg: "bg-red-50 dark:bg-red-900/30",
    indicator: "bg-red-500",
    text: "text-red-600 dark:text-red-400",
    label: "错误",
  },
  skipped: {
    border: "border-yellow-400 dark:border-yellow-500",
    bg: "bg-yellow-50 dark:bg-yellow-900/30",
    indicator: "bg-yellow-500",
    text: "text-yellow-600 dark:text-yellow-400",
    label: "已跳过",
  },
};

/** 自定义 Agent 节点 */
function AgentNode({ data }: NodeProps) {
  const { stepStates } = useWorkflowStore();
  const stepState = stepStates[data.stepId];
  const status = stepState?.status || "pending";
  const colors = statusColors[status];

  return (
    <div
      className={cn(
        "relative px-4 py-3 rounded-xl border-2 shadow-lg min-w-[180px] max-w-[220px]",
        "transition-all duration-300",
        colors.border,
        colors.bg
      )}
    >
      {/* 输入连接点 */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-gray-400 dark:!bg-gray-500 !border-2 !border-white dark:!border-gray-900"
      />

      {/* Agent 名称和图标 */}
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{getAgentIcon(data.agent)}</span>
        <span className="font-semibold text-gray-800 dark:text-gray-200 truncate">
          {data.agent}
        </span>
      </div>

      {/* 任务描述 */}
      <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
        {data.task}
      </p>

      {/* 状态指示器 */}
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "w-2 h-2 rounded-full",
            colors.indicator,
            status === "running" && "animate-pulse"
          )}
        />
        <span className={cn("text-xs font-medium", colors.text)}>
          {colors.label}
        </span>
      </div>

      {/* 运行中动画边框 */}
      {status === "running" && (
        <div className="absolute inset-0 rounded-xl border-2 border-blue-400 animate-ping opacity-30 pointer-events-none" />
      )}

      {/* 输出连接点 */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-gray-400 dark:!bg-gray-500 !border-2 !border-white dark:!border-gray-900"
      />
    </div>
  );
}

/** 节点类型 */
const nodeTypes = {
  agent: AgentNode,
};

interface WorkflowGraphProps {
  workflow: WorkflowInfo;
}

/** 工作流图核心组件 */
function WorkflowGraphCore({ workflow }: WorkflowGraphProps) {
  // 计算节点和边
  const { initialNodes, initialEdges } = useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const stepMap = new Map<string, number>();

    // 计算每个节点的层级
    const levels: Map<string, number> = new Map();
    const visited = new Set<string>();

    function calculateLevel(stepId: string): number {
      if (levels.has(stepId)) return levels.get(stepId)!;
      if (visited.has(stepId)) return 0;
      visited.add(stepId);

      const step = workflow.steps.find((s) => s.id === stepId);
      if (!step || step.depends_on.length === 0) {
        levels.set(stepId, 0);
        return 0;
      }

      const maxDep = Math.max(
        ...step.depends_on.map((dep) => calculateLevel(dep))
      );
      const level = maxDep + 1;
      levels.set(stepId, level);
      return level;
    }

    workflow.steps.forEach((step) => calculateLevel(step.id));

    // 按层级分组
    const levelGroups: Map<number, string[]> = new Map();
    workflow.steps.forEach((step) => {
      const level = levels.get(step.id) || 0;
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(step.id);
    });

    // 创建节点
    const nodeSpacingY = 150;
    const nodeSpacingX = 250;

    workflow.steps.forEach((step, idx) => {
      stepMap.set(step.id, idx);
      const level = levels.get(step.id) || 0;
      const siblings = levelGroups.get(level) || [];
      const siblingIndex = siblings.indexOf(step.id);
      const totalSiblings = siblings.length;

      // 水平居中
      const offsetX = (siblingIndex - (totalSiblings - 1) / 2) * nodeSpacingX;

      nodes.push({
        id: step.id,
        type: "agent",
        position: {
          x: 400 + offsetX,
          y: 50 + level * nodeSpacingY,
        },
        data: {
          stepId: step.id,
          agent: step.agent,
          task: step.task,
        },
      });
    });

    // 创建边
    workflow.steps.forEach((step) => {
      step.depends_on.forEach((depId) => {
        edges.push({
          id: `${depId}-${step.id}`,
          source: depId,
          target: step.id,
          type: "smoothstep",
          animated: false,
          style: { stroke: "#94a3b8", strokeWidth: 2 },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: "#94a3b8",
          },
        });
      });
    });

    return { initialNodes: nodes, initialEdges: edges };
  }, [workflow]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-full h-full bg-gray-100 dark:bg-gray-900 rounded-xl overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.3}
        maxZoom={1.5}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#94a3b8" gap={20} size={1} />
        <Controls
          className="!bg-white dark:!bg-gray-800 !border-gray-200 dark:!border-gray-700 !shadow-lg"
          showInteractive={false}
        />
      </ReactFlow>
    </div>
  );
}

/** 工作流图组件（含 Provider） */
export function WorkflowGraph({ workflow }: WorkflowGraphProps) {
  return (
    <ReactFlowProvider>
      <WorkflowGraphCore workflow={workflow} />
    </ReactFlowProvider>
  );
}
