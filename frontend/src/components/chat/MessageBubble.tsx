"use client";

import { useState, useCallback, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { Message } from "@/types";
import { cn, formatDate } from "@/lib/utils";
import { ToolCallList } from "./ToolCallDisplay";

interface MessageBubbleProps {
  message: Message;
}

/** 代码块组件 */
function CodeBlock({
  language,
  children,
}: {
  language: string;
  children: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [children]);

  return (
    <div className="relative group my-3 rounded-lg overflow-hidden">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 dark:bg-gray-900 border-b border-gray-700">
        <span className="text-xs text-gray-400 font-mono">
          {language || "text"}
        </span>
        <button
          onClick={handleCopy}
          className={cn(
            "text-xs px-2 py-1 rounded transition-all duration-200",
            "hover:bg-gray-700",
            copied
              ? "text-green-400"
              : "text-gray-400 hover:text-gray-200"
          )}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      {/* 代码内容 */}
      <SyntaxHighlighter
        style={oneDark}
        language={language || "text"}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: 0,
          fontSize: "14px",
        }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
}

/** Markdown 渲染器 */
function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      components={{
        // 代码块
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const codeString = String(children).replace(/\n$/, "");

          // 判断是否为代码块（而非行内代码）
          const isCodeBlock = match || codeString.includes("\n");

          if (isCodeBlock) {
            return (
              <CodeBlock language={match?.[1] || ""}>
                {codeString}
              </CodeBlock>
            );
          }

          // 行内代码
          return (
            <code
              className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-sm font-mono"
              {...props}
            >
              {children}
            </code>
          );
        },
        // 段落
        p({ children }) {
          return <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>;
        },
        // 标题
        h1({ children }) {
          return <h1 className="text-2xl font-bold mb-4 mt-6 first:mt-0">{children}</h1>;
        },
        h2({ children }) {
          return <h2 className="text-xl font-bold mb-3 mt-5 first:mt-0">{children}</h2>;
        },
        h3({ children }) {
          return <h3 className="text-lg font-bold mb-2 mt-4 first:mt-0">{children}</h3>;
        },
        // 列表
        ul({ children }) {
          return <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>;
        },
        ol({ children }) {
          return <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>;
        },
        li({ children }) {
          return <li className="leading-relaxed">{children}</li>;
        },
        // 引用
        blockquote({ children }) {
          return (
            <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 my-3 italic text-gray-600 dark:text-gray-400">
              {children}
            </blockquote>
          );
        },
        // 链接
        a({ href, children }) {
          return (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600 underline"
            >
              {children}
            </a>
          );
        },
        // 分割线
        hr() {
          return <hr className="my-4 border-gray-200 dark:border-gray-700" />;
        },
        // 表格
        table({ children }) {
          return (
            <div className="overflow-x-auto my-3">
              <table className="min-w-full border border-gray-200 dark:border-gray-700">
                {children}
              </table>
            </div>
          );
        },
        th({ children }) {
          return (
            <th className="px-4 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 font-semibold text-left">
              {children}
            </th>
          );
        },
        td({ children }) {
          return (
            <td className="px-4 py-2 border border-gray-200 dark:border-gray-700">
              {children}
            </td>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { role, content, created_at, isStreaming, tool_calls } = message;

  // 系统消息样式
  if (role === "system") {
    return (
      <div className="flex justify-center my-2">
        <div
          className={cn(
            "px-4 py-2 max-w-[80%]",
            "text-sm text-gray-500 dark:text-gray-400",
            "bg-gray-100 dark:bg-gray-800/50",
            "rounded-lg",
            "text-center"
          )}
        >
          {content}
        </div>
      </div>
    );
  }

  // tool 角色消息 - 使用内联工具卡片样式
  if (role === "tool") {
    // 解析 tool 消息中的工具调用信息
    const toolCall = tool_calls?.[0];
    if (toolCall) {
      return (
        <div className="flex justify-start my-2 px-4">
          <div className="max-w-[85%]">
            <ToolCallList toolCalls={[toolCall]} />
          </div>
        </div>
      );
    }
    // 如果没有 tool_calls，显示普通工具消息
    return (
      <div className="flex justify-center my-2">
        <div
          className={cn(
            "px-4 py-2 max-w-[80%]",
            "text-sm text-gray-500 dark:text-gray-400",
            "bg-gray-100 dark:bg-gray-800/50",
            "rounded-lg",
            "text-center"
          )}
        >
          {content}
        </div>
      </div>
    );
  }

  const isUser = role === "user";

  return (
    <div
      className={cn(
        "flex w-full mb-4",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          "transition-all duration-200",
          isUser
            ? "bg-blue-500 text-white rounded-br-md"
            : "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-md shadow-sm border border-gray-100 dark:border-gray-700"
        )}
      >
        {/* 助手消息中的工具调用展示（在文本内容之前） */}
        {!isUser && tool_calls && tool_calls.length > 0 && (
          <div className="mb-3">
            <ToolCallList toolCalls={tool_calls} />
          </div>
        )}

        {/* 消息内容 */}
        <div className={cn("prose prose-sm max-w-none", isUser && "prose-invert")}>
          {isUser ? (
            // 用户消息直接显示文本
            <p className="whitespace-pre-wrap mb-0">{content}</p>
          ) : (
            // 助手消息渲染 Markdown
            <>
              {content && <MarkdownContent content={content} />}
              {/* 流式消息光标 */}
              {isStreaming && (
                <span className="inline-block w-2 h-5 ml-0.5 bg-current animate-pulse">
                  ▊
                </span>
              )}
            </>
          )}
        </div>

        {/* 时间戳 */}
        <div
          className={cn(
            "mt-2 text-xs",
            isUser
              ? "text-blue-100"
              : "text-gray-400 dark:text-gray-500"
          )}
        >
          {formatDate(created_at)}
        </div>
      </div>
    </div>
  );
}
