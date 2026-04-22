"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { AgentSelector } from "./AgentSelector";
import { ConversationList } from "./ConversationList";
import { cn } from "@/lib/utils";

interface SidebarProps {
  defaultCollapsed?: boolean;
}

/**
 * 侧边栏
 * 整合品牌标志、Agent 选择器、会话列表、设置按钮
 */
export function Sidebar({ defaultCollapsed = false }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);
  const [isMobile, setIsMobile] = useState(false);
  const [agentSectionCollapsed, setAgentSectionCollapsed] = useState(false);

  // 检测移动端
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setIsCollapsed(true);
      }
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  /** 切换侧边栏 */
  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  /** 切换 Agent 区域折叠 */
  const toggleAgentSection = () => {
    setAgentSectionCollapsed(!agentSectionCollapsed);
  };

  return (
    <>
      {/* 移动端遮罩 */}
      {isMobile && !isCollapsed && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsCollapsed(true)}
        />
      )}

      {/* 侧边栏主体 */}
      <aside
        className={cn(
          "flex flex-col h-full bg-white dark:bg-gray-900",
          "border-r border-gray-200 dark:border-gray-800",
          "transition-all duration-300 ease-in-out",
          "z-50",
          isMobile
            ? cn(
                "fixed left-0 top-0",
                isCollapsed ? "-translate-x-full" : "translate-x-0"
              )
            : isCollapsed
            ? "w-0 overflow-hidden"
            : "w-[280px]",
          !isMobile && !isCollapsed && "flex-shrink-0"
        )}
        style={{ width: isCollapsed && !isMobile ? 0 : isMobile ? 280 : 280 }}
      >
        {/* 顶部：品牌标志 + 收起按钮 */}
        <div
          className={cn(
            "flex items-center justify-between px-4 py-4",
            "border-b border-gray-200 dark:border-gray-800"
          )}
        >
          <div className="flex items-center gap-2">
            <div
              className={cn(
                "w-8 h-8 rounded-lg",
                "bg-gradient-to-br from-blue-500 to-purple-600",
                "flex items-center justify-center",
                "text-white font-bold text-sm"
              )}
            >
              AF
            </div>
            <span className="font-semibold text-gray-900 dark:text-gray-100">
              AgentForge
            </span>
          </div>
          <button
            onClick={toggleSidebar}
            className={cn(
              "w-8 h-8 rounded-lg flex items-center justify-center",
              "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
              "hover:bg-gray-100 dark:hover:bg-gray-800",
              "transition-colors duration-150"
            )}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>

        {/* 中间上半部分：Agent 选择器 */}
        <div
          className={cn(
            "border-b border-gray-200 dark:border-gray-800",
            agentSectionCollapsed ? "pb-0" : "pb-2"
          )}
        >
          {/* Agent 区域标题栏 */}
          <button
            onClick={toggleAgentSection}
            className={cn(
              "w-full flex items-center justify-between px-4 py-2",
              "text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider",
              "hover:bg-gray-50 dark:hover:bg-gray-800/50",
              "transition-colors duration-150"
            )}
          >
            <span>Agent Selection</span>
            <svg
              className={cn(
                "w-4 h-4 transition-transform duration-200",
                agentSectionCollapsed ? "-rotate-90" : "rotate-0"
              )}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>

          {/* Agent 选择器内容 */}
          <div
            className={cn(
              "overflow-hidden transition-all duration-200",
              agentSectionCollapsed ? "max-h-0" : "max-h-[400px]"
            )}
          >
            <div className="overflow-y-auto max-h-[380px]">
              <AgentSelector />
            </div>
          </div>
        </div>

        {/* 中间下半部分：会话列表 */}
        <div className="flex-1 overflow-hidden">
          <ConversationList />
        </div>

        {/* 底部：工作流 + 设置按钮 */}
        <div
          className={cn(
            "px-3 py-3",
            "border-t border-gray-200 dark:border-gray-800"
          )}
        >
          <Link
            href="/workflow"
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg w-full mb-1",
              "text-gray-700 dark:text-gray-300",
              "hover:bg-gray-100 dark:hover:bg-gray-800",
              "transition-colors duration-150"
            )}
          >
            <svg
              className="w-5 h-5 text-gray-500 dark:text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
              />
            </svg>
            <span className="text-sm font-medium">Workflows</span>
          </Link>
          <Link
            href="/dashboard"
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg w-full mb-1",
              "text-gray-700 dark:text-gray-300",
              "hover:bg-gray-100 dark:hover:bg-gray-800",
              "transition-colors duration-150"
            )}
          >
            <svg
              className="w-5 h-5 text-gray-500 dark:text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <span className="text-sm font-medium">Dashboard</span>
          </Link>
          <Link
            href="/marketplace"
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg w-full mb-1",
              "text-gray-700 dark:text-gray-300",
              "hover:bg-gray-100 dark:hover:bg-gray-800",
              "transition-colors duration-150"
            )}
          >
            <svg
              className="w-5 h-5 text-gray-500 dark:text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <span className="text-sm font-medium">Template Marketplace</span>
          </Link>
          <Link
            href="/settings"
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg w-full",
              "text-gray-700 dark:text-gray-300",
              "hover:bg-gray-100 dark:hover:bg-gray-800",
              "transition-colors duration-150"
            )}
          >
            <svg
              className="w-5 h-5 text-gray-500 dark:text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span className="text-sm font-medium">Settings</span>
          </Link>
        </div>
      </aside>

      {/* 收起状态的展开按钮（非移动端） */}
      {!isMobile && isCollapsed && (
        <button
          onClick={toggleSidebar}
          className={cn(
            "fixed left-4 top-4 z-40",
            "w-10 h-10 rounded-lg flex items-center justify-center",
            "bg-white dark:bg-gray-800",
            "border border-gray-200 dark:border-gray-700",
            "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
            "shadow-md hover:shadow-lg",
            "transition-all duration-150"
          )}
          title="Expand sidebar"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      )}

      {/* 移动端汉堡按钮 */}
      {isMobile && isCollapsed && (
        <button
          onClick={toggleSidebar}
          className={cn(
            "fixed left-4 top-4 z-40",
            "w-10 h-10 rounded-lg flex items-center justify-center",
            "bg-white dark:bg-gray-800",
            "border border-gray-200 dark:border-gray-700",
            "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
            "shadow-md",
            "transition-all duration-150"
          )}
          title="Open menu"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      )}
    </>
  );
}
