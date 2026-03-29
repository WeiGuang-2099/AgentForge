"use client";

import { useCallback, useState } from "react";
import { useChatStore } from "@/stores/chatStore";
import { useAgentStore } from "@/stores/agentStore";
import { streamChat } from "@/lib/api";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { StreamingIndicator } from "./StreamingIndicator";
import { cn } from "@/lib/utils";
import type { ToolCall } from "@/types";

/**
 * 对话主容器
 * 整合 MessageList + ChatInput + StreamingIndicator
 * 使用 SSE 流式聊天
 */
export function ChatWindow() {
  const { currentAgent } = useAgentStore();
  const {
    currentConversationId,
    isStreaming,
    createConversation,
    addMessage,
    updateLastMessage,
    updateLastMessageToolCalls,
    setStreaming,
    getCurrentMessages,
  } = useChatStore();

  const [error, setError] = useState<string | null>(null);

  const messages = getCurrentMessages();

  // 发送消息处理
  const handleSend = useCallback(
    async (content: string) => {
      if (!currentAgent) return;

      setError(null);

      // 获取或创建会话
      let conversationId = currentConversationId;
      if (!conversationId) {
        conversationId = createConversation(currentAgent.name);
      }

      // 1. 添加用户消息
      addMessage(conversationId, {
        role: "user",
        content,
      });

      // 2. 开始流式响应
      setStreaming(true);

      // 3. 添加空的助手消息（流式状态）
      addMessage(conversationId, {
        role: "assistant",
        content: "",
        isStreaming: true,
      });

      try {
        // 4. 调用 streamChat
        const allMessages = useChatStore.getState().conversations
          .find((c) => c.id === conversationId)
          ?.messages.slice(0, -1) // 排除刚添加的空消息
          .map((m) => ({ role: m.role, content: m.content })) || [];

        const stream = streamChat({
          agent_name: currentAgent.name,
          messages: allMessages,
          conversation_id: conversationId,
          stream: true,
        });

        let fullContent = "";
        let currentToolCalls: ToolCall[] = [];

        for await (const event of stream) {
          if (event.error) {
            setError(event.error);
            break;
          }

          // 处理工具调用事件
          if (event.tool_call) {
            const newToolCall: ToolCall = {
              id: event.tool_call.id,
              name: event.tool_call.name,
              arguments: event.tool_call.arguments,
              status: "calling",
            };
            currentToolCalls = [...currentToolCalls, newToolCall];
            updateLastMessageToolCalls(conversationId, currentToolCalls);
          }

          // 处理工具调用结果事件
          if (event.tool_result) {
            currentToolCalls = currentToolCalls.map((tc) =>
              tc.id === event.tool_result!.id
                ? {
                    ...tc,
                    result: event.tool_result!.result,
                    status: event.tool_result!.status,
                  }
                : tc
            );
            updateLastMessageToolCalls(conversationId, currentToolCalls);
          }

          if (event.token) {
            fullContent += event.token;
            updateLastMessage(conversationId, fullContent);
          }

          if (event.done) {
            break;
          }
        }

        // 5. 标记消息完成（移除 isStreaming 标记）
        const finalConv = useChatStore.getState().conversations.find(
          (c) => c.id === conversationId
        );
        if (finalConv && finalConv.messages.length > 0) {
          const lastMsg = finalConv.messages[finalConv.messages.length - 1];
          if (lastMsg.isStreaming) {
            // 更新消息，移除 streaming 标记
            useChatStore.setState((state) => ({
              conversations: state.conversations.map((conv) =>
                conv.id === conversationId
                  ? {
                      ...conv,
                      messages: conv.messages.map((msg, i) =>
                        i === conv.messages.length - 1
                          ? { ...msg, isStreaming: false }
                          : msg
                      ),
                    }
                  : conv
              ),
            }));
          }
        }
      } catch (err) {
        console.error("流式聊天错误:", err);
        setError(err instanceof Error ? err.message : "发送消息失败");
      } finally {
        setStreaming(false);
      }
    },
    [
      currentAgent,
      currentConversationId,
      createConversation,
      addMessage,
      updateLastMessage,
      updateLastMessageToolCalls,
      setStreaming,
    ]
  );

  // 无选中 Agent 时显示提示
  if (!currentAgent) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-6xl mb-4 opacity-20">🤖</div>
          <p className="text-gray-400 dark:text-gray-500 text-lg">
            请先选择一个 Agent
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* 顶部 Agent 信息栏 */}
      <div
        className={cn(
          "flex items-center gap-3 px-6 py-4",
          "border-b border-gray-200 dark:border-gray-800",
          "bg-white dark:bg-gray-900"
        )}
      >
        {/* Agent 头像 */}
        <div
          className={cn(
            "w-10 h-10 rounded-full",
            "bg-gradient-to-br from-blue-500 to-purple-600",
            "flex items-center justify-center",
            "text-white font-semibold text-lg"
          )}
        >
          {currentAgent.display_name.charAt(0).toUpperCase()}
        </div>
        {/* Agent 信息 */}
        <div className="flex-1 min-w-0">
          <h2 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
            {currentAgent.display_name}
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
            {currentAgent.description || `模型: ${currentAgent.model}`}
          </p>
        </div>
        {/* Agent 状态指示 */}
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-gray-500 dark:text-gray-400">在线</span>
        </div>
      </div>

      {/* 消息列表区 */}
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} />
      </div>

      {/* 底部输入区 */}
      <div
        className={cn(
          "border-t border-gray-200 dark:border-gray-800",
          "bg-white dark:bg-gray-900",
          "p-4"
        )}
      >
        {/* 错误提示 */}
        {error && (
          <div
            className={cn(
              "mb-3 px-4 py-2 rounded-lg",
              "bg-red-50 dark:bg-red-900/20",
              "text-red-600 dark:text-red-400",
              "text-sm"
            )}
          >
            <span className="font-medium">错误：</span>
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        )}

        {/* 流式指示器 */}
        {isStreaming && <StreamingIndicator />}

        {/* 输入框 */}
        <ChatInput
          onSend={handleSend}
          disabled={isStreaming}
          placeholder={`向 ${currentAgent.display_name} 发送消息...`}
        />
      </div>
    </div>
  );
}
