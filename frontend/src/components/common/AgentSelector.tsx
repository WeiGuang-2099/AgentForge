"use client";

import { useAgentStore } from "@/stores/agentStore";
import { useChatStore } from "@/stores/chatStore";
import { cn } from "@/lib/utils";
import type { Agent } from "@/types";

/** Agent 图标映射 */
const AGENT_ICONS: Record<string, string> = {
  assistant: "🤖",
  coder: "💻",
  researcher: "🔍",
  translator: "🌐",
  writer: "✍️",
  analyst: "📊",
};

/** 获取 Agent 图标 */
function getAgentIcon(name: string): string {
  const lowerName = name.toLowerCase();
  for (const [key, icon] of Object.entries(AGENT_ICONS)) {
    if (lowerName.includes(key)) {
      return icon;
    }
  }
  return "";
}

/** 获取 Agent 首字母 */
function getAgentInitial(displayName: string): string {
  return displayName.charAt(0).toUpperCase();
}

interface AgentCardProps {
  agent: Agent;
  isSelected: boolean;
  onSelect: () => void;
}

/** Agent 卡片组件 */
function AgentCard({ agent, isSelected, onSelect }: AgentCardProps) {
  const icon = getAgentIcon(agent.name);
  const initial = getAgentInitial(agent.display_name);

  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full p-3 rounded-xl text-left transition-all duration-200",
        "border-2 hover:shadow-md",
        "bg-white dark:bg-gray-800",
        isSelected
          ? "border-blue-500 shadow-md shadow-blue-500/20"
          : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
      )}
    >
      {/* Agent 图标 */}
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0",
            "text-xl",
            isSelected
              ? "bg-blue-100 dark:bg-blue-900/40"
              : "bg-gray-100 dark:bg-gray-700"
          )}
        >
          {icon || (
            <span
              className={cn(
                "font-semibold text-sm",
                isSelected
                  ? "text-blue-600 dark:text-blue-400"
                  : "text-gray-600 dark:text-gray-300"
              )}
            >
              {initial}
            </span>
          )}
        </div>

        <div className="flex-1 min-w-0">
          {/* Agent 名称 */}
          <h3
            className={cn(
              "font-medium truncate",
              isSelected
                ? "text-blue-600 dark:text-blue-400"
                : "text-gray-900 dark:text-gray-100"
            )}
          >
            {agent.display_name}
          </h3>

          {/* Agent 描述 */}
          <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2 mt-0.5">
            {agent.description || "暂无描述"}
          </p>

          {/* 工具数量标签 */}
          {agent.tools && agent.tools.length > 0 && (
            <span
              className={cn(
                "inline-flex items-center mt-1.5 px-2 py-0.5 rounded-full text-xs",
                "bg-gray-100 dark:bg-gray-700",
                "text-gray-600 dark:text-gray-400"
              )}
            >
              🛠 {agent.tools.length} 工具
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

/** Skeleton 加载占位 */
function AgentCardSkeleton() {
  return (
    <div
      className={cn(
        "w-full p-3 rounded-xl",
        "border-2 border-gray-200 dark:border-gray-700",
        "bg-white dark:bg-gray-800",
        "animate-pulse"
      )}
    >
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-gray-200 dark:bg-gray-700" />
        <div className="flex-1">
          <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-3 w-full bg-gray-200 dark:bg-gray-700 rounded mt-2" />
          <div className="h-3 w-2/3 bg-gray-200 dark:bg-gray-700 rounded mt-1" />
        </div>
      </div>
    </div>
  );
}

interface AgentSelectorProps {
  collapsed?: boolean;
}

/**
 * Agent 选择器
 * 展示所有可用 Agent 的卡片列表
 */
export function AgentSelector({ collapsed = false }: AgentSelectorProps) {
  const { agents, currentAgent, isLoading, setCurrentAgent } = useAgentStore();
  const { createConversation } = useChatStore();

  /** 选择 Agent 并创建新会话 */
  const handleSelectAgent = (agent: Agent) => {
    setCurrentAgent(agent);
    // 创建新会话
    createConversation(agent.name);
  };

  if (collapsed) {
    return null;
  }

  return (
    <div className="px-3 py-2">
      <h3 className="px-1 mb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        选择 Agent
      </h3>

      {/* Agent 卡片网格 */}
      <div className="grid grid-cols-2 gap-2">
        {isLoading ? (
          // 加载状态
          <>
            <AgentCardSkeleton />
            <AgentCardSkeleton />
            <AgentCardSkeleton />
            <AgentCardSkeleton />
          </>
        ) : agents.length > 0 ? (
          // Agent 列表
          agents.map((agent) => (
            <AgentCard
              key={agent.name}
              agent={agent}
              isSelected={currentAgent?.name === agent.name}
              onSelect={() => handleSelectAgent(agent)}
            />
          ))
        ) : (
          // 空状态
          <div className="col-span-2 py-8 text-center text-gray-400 dark:text-gray-500">
            <div className="text-3xl mb-2">🤖</div>
            <p className="text-sm">暂无可用 Agent</p>
          </div>
        )}
      </div>
    </div>
  );
}
