"use client";

import { cn } from "@/lib/utils";

/**
 * 流式响应指示器
 * 显示三个点的动画加载效果
 */
export function StreamingIndicator() {
  return (
    <div className="flex items-center gap-2 mb-3 px-1">
      {/* 三点动画 */}
      <div className="flex items-center gap-1">
        <span
          className={cn(
            "w-2 h-2 rounded-full",
            "bg-blue-500 dark:bg-blue-400",
            "animate-bounce"
          )}
          style={{ animationDelay: "0ms" }}
        />
        <span
          className={cn(
            "w-2 h-2 rounded-full",
            "bg-blue-500 dark:bg-blue-400",
            "animate-bounce"
          )}
          style={{ animationDelay: "150ms" }}
        />
        <span
          className={cn(
            "w-2 h-2 rounded-full",
            "bg-blue-500 dark:bg-blue-400",
            "animate-bounce"
          )}
          style={{ animationDelay: "300ms" }}
        />
      </div>
      {/* 文字提示 */}
      <span className="text-sm text-gray-500 dark:text-gray-400">
        Thinking...
      </span>
    </div>
  );
}
