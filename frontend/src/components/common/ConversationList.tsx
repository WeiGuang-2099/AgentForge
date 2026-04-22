"use client";

import { useState } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useAgentStore } from "@/stores/agentStore";
import { cn, formatDate } from "@/lib/utils";

interface ConversationItemProps {
  id: string;
  title: string;
  agentName: string;
  updatedAt: string;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
}

/** 会话项组件 */
function ConversationItem({
  title,
  agentName,
  updatedAt,
  isActive,
  onSelect,
  onDelete,
}: ConversationItemProps) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={cn(
        "group relative px-3 py-2.5 rounded-lg cursor-pointer",
        "transition-all duration-150",
        isActive
          ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300"
          : "hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
      )}
      onClick={onSelect}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 标题行 */}
      <div className="flex items-center gap-2">
        <span className="text-sm">💬</span>
        <span className="flex-1 truncate text-sm font-medium">{title}</span>
      </div>

      {/* 信息行 */}
      <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
        <span className="truncate">{agentName}</span>
        <span>·</span>
        <span className="flex-shrink-0">{formatDate(updatedAt)}</span>
      </div>

      {/* 删除按钮 - hover 时显示 */}
      {isHovered && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className={cn(
            "absolute right-2 top-1/2 -translate-y-1/2",
            "w-6 h-6 rounded flex items-center justify-center",
            "text-gray-400 hover:text-red-500",
            "hover:bg-red-50 dark:hover:bg-red-900/20",
            "transition-colors duration-150"
          )}
          title="Delete conversation"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      )}
    </div>
  );
}

interface ConversationListProps {
  collapsed?: boolean;
}

/**
 * 会话列表
 * 显示当前 Agent 的所有会话历史
 */
export function ConversationList({ collapsed = false }: ConversationListProps) {
  const { currentAgent } = useAgentStore();
  const {
    conversations,
    currentConversationId,
    setCurrentConversation,
    deleteConversation,
    createConversation,
  } = useChatStore();

  // 过滤当前 Agent 的会话
  const filteredConversations = currentAgent
    ? conversations.filter((c) => c.agent_name === currentAgent.name)
    : conversations;

  /** 新建会话 */
  const handleCreateConversation = () => {
    if (currentAgent) {
      createConversation(currentAgent.name);
    }
  };

  /** 切换会话 */
  const handleSelectConversation = (id: string) => {
    setCurrentConversation(id);
  };

  /** 删除会话 */
  const handleDeleteConversation = (id: string) => {
    if (confirm("Are you sure you want to delete this conversation?")) {
      deleteConversation(id);
    }
  };

  if (collapsed) {
    return null;
  }

  return (
    <div className="flex flex-col h-full">
      {/* 标题栏 */}
      <div className="flex items-center justify-between px-4 py-2">
        <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Chat History
        </h3>
        <button
          onClick={handleCreateConversation}
          disabled={!currentAgent}
          className={cn(
            "w-6 h-6 rounded flex items-center justify-center",
            "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
            "hover:bg-gray-100 dark:hover:bg-gray-800",
            "transition-colors duration-150",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
          title="New chat"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </button>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto px-2 pb-2">
        {filteredConversations.length > 0 ? (
          <div className="space-y-1">
            {filteredConversations.map((conv) => (
              <ConversationItem
                key={conv.id}
                id={conv.id}
                title={conv.title}
                agentName={conv.agent_name}
                updatedAt={conv.updated_at}
                isActive={conv.id === currentConversationId}
                onSelect={() => handleSelectConversation(conv.id)}
                onDelete={() => handleDeleteConversation(conv.id)}
              />
            ))}
          </div>
        ) : (
          // 空状态
          <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
            <div className="text-3xl mb-2">📭</div>
            <p className="text-sm">No conversations yet</p>
            {currentAgent && (
              <button
                onClick={handleCreateConversation}
                className={cn(
                  "mt-4 px-4 py-2 rounded-lg text-sm",
                  "bg-blue-500 hover:bg-blue-600 text-white",
                  "transition-colors duration-150"
                )}
              >
                Start a new chat
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
