"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@/types";
import { MessageBubble } from "./MessageBubble";
import { cn } from "@/lib/utils";

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 新消息自动滚动到底部
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 空状态
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-6xl mb-4 opacity-20">💬</div>
          <p className="text-gray-400 dark:text-gray-500 text-lg">
            Start a conversation with the Agent...
          </p>
          <p className="text-gray-300 dark:text-gray-600 text-sm mt-2">
            Enter your question below
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        "h-full overflow-y-auto",
        "px-4 py-6",
        "scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-700"
      )}
    >
      <div className="max-w-3xl mx-auto space-y-1">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {/* 滚动锚点 */}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
