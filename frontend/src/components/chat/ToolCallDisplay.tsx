"use client";

import { useState, useMemo } from "react";
import type { ToolCall } from "@/types";
import { cn } from "@/lib/utils";

interface ToolCallDisplayProps {
  toolCall: ToolCall;
}

/** 工具图标映射 */
const TOOL_ICONS: Record<string, string> = {
  web_search: "🔍",
  scrape_web: "🌐",
  python_repl: "💻",
  read_file: "📄",
  write_file: "📝",
  calculator: "🧮",
  data_analyzer: "📊",
  translator: "🌐",
};

/** 获取工具图标 */
function getToolIcon(toolName: string): string {
  return TOOL_ICONS[toolName] || "🔧";
}

/** 格式化 JSON 用于显示 */
function formatJson(obj: Record<string, unknown>): string {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
}

/** 折叠区块组件 */
function CollapsibleSection({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="mt-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-1 text-xs font-medium",
          "text-gray-500 dark:text-gray-400",
          "hover:text-gray-700 dark:hover:text-gray-300",
          "transition-colors duration-150"
        )}
      >
        <span
          className={cn(
            "transition-transform duration-200",
            isOpen && "rotate-90"
          )}
        >
          ▸
        </span>
        {title}
      </button>
      <div
        className={cn(
          "overflow-hidden transition-all duration-200",
          isOpen ? "max-h-[500px] opacity-100 mt-2" : "max-h-0 opacity-0"
        )}
      >
        {children}
      </div>
    </div>
  );
}

/** 状态图标组件 */
function StatusIcon({ status }: { status: ToolCall["status"] }) {
  switch (status) {
    case "calling":
      return (
        <span className="inline-flex items-center justify-center w-5 h-5">
          <span
            className={cn(
              "w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full",
              "animate-spin"
            )}
          />
        </span>
      );
    case "completed":
      return (
        <span className="text-green-500 text-sm font-bold">✓</span>
      );
    case "error":
      return (
        <span className="text-red-500 text-sm font-bold">✕</span>
      );
    default:
      return null;
  }
}

/** 结果内容渲染 */
function ResultContent({ result, toolName }: { result: string; toolName: string }) {
  // 判断是否为代码类工具
  const isCodeTool = ["python_repl", "read_file", "write_file"].includes(toolName);
  
  // 尝试解析 JSON 结果
  const parsedResult = useMemo(() => {
    try {
      return JSON.parse(result);
    } catch {
      return null;
    }
  }, [result]);

  // 搜索结果列表
  if (toolName === "web_search" && Array.isArray(parsedResult)) {
    return (
      <ul className="space-y-2">
        {parsedResult.map((item: { title?: string; snippet?: string; url?: string }, index: number) => (
          <li key={index} className="text-sm">
            <div className="font-medium text-gray-800 dark:text-gray-200">
              {index + 1}. {item.title || "无标题"}
            </div>
            <p className="text-gray-600 dark:text-gray-400 text-xs mt-0.5 line-clamp-2">
              {item.snippet || item.url || ""}
            </p>
          </li>
        ))}
      </ul>
    );
  }

  // 代码类结果
  if (isCodeTool) {
    return (
      <pre
        className={cn(
          "p-3 rounded-md overflow-x-auto",
          "bg-gray-900 text-gray-100",
          "text-xs font-mono leading-relaxed",
          "max-h-60 overflow-y-auto"
        )}
      >
        {result}
      </pre>
    );
  }

  // 普通文本结果
  return (
    <div
      className={cn(
        "p-3 rounded-md",
        "bg-gray-50 dark:bg-gray-800",
        "text-sm text-gray-700 dark:text-gray-300",
        "whitespace-pre-wrap break-words",
        "max-h-60 overflow-y-auto"
      )}
    >
      {result}
    </div>
  );
}

/**
 * 工具调用展示组件
 * 展示单个工具调用的过程和结果
 */
export function ToolCallDisplay({ toolCall }: ToolCallDisplayProps) {
  const { name, arguments: args, result, status } = toolCall;
  const icon = getToolIcon(name);

  return (
    <div
      className={cn(
        "rounded-lg border overflow-hidden my-2",
        "transition-all duration-200",
        status === "error"
          ? "border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20"
          : "border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50"
      )}
    >
      {/* 卡片头部 */}
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-2",
          "border-b",
          status === "error"
            ? "border-red-200 dark:border-red-800 bg-red-100 dark:bg-red-900/30"
            : "border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
        )}
      >
        {/* 工具图标 */}
        <span className="text-lg" role="img" aria-label={name}>
          {icon}
        </span>
        
        {/* 工具名称 */}
        <span className="flex-1 text-sm font-medium text-gray-800 dark:text-gray-200">
          {name}
        </span>
        
        {/* 状态图标 */}
        <StatusIcon status={status} />
      </div>

      {/* 卡片内容 */}
      <div className="px-3 py-2">
        {/* 调用中状态 */}
        {status === "calling" && (
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
            <span>正在调用 {name}...</span>
          </div>
        )}

        {/* 参数展示 */}
        {args && Object.keys(args).length > 0 && (
          <CollapsibleSection title="参数" defaultOpen={false}>
            <pre
              className={cn(
                "p-2 rounded text-xs font-mono",
                "bg-gray-100 dark:bg-gray-900",
                "text-gray-700 dark:text-gray-300",
                "overflow-x-auto"
              )}
            >
              {formatJson(args)}
            </pre>
          </CollapsibleSection>
        )}

        {/* 结果展示 */}
        {result && (
          <CollapsibleSection title="结果" defaultOpen={true}>
            <ResultContent result={result} toolName={name} />
          </CollapsibleSection>
        )}

        {/* 错误状态特殊提示 */}
        {status === "error" && result && (
          <div
            className={cn(
              "mt-2 p-2 rounded",
              "bg-red-100 dark:bg-red-900/40",
              "text-red-700 dark:text-red-300",
              "text-sm"
            )}
          >
            <span className="font-medium">错误：</span>
            {result}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * 工具调用列表展示组件
 * 用于展示多个工具调用
 */
export function ToolCallList({ toolCalls }: { toolCalls: ToolCall[] }) {
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="space-y-2">
      {toolCalls.map((toolCall) => (
        <ToolCallDisplay key={toolCall.id} toolCall={toolCall} />
      ))}
    </div>
  );
}
