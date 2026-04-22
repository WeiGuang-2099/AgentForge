"use client";

import { useEffect } from "react";
import type { WorkflowInfo } from "@/types";
import { useWorkflowStore } from "@/stores/workflowStore";
import { cn } from "@/lib/utils";

interface WorkflowSelectorProps {
  onSelect: (workflow: WorkflowInfo) => void;
}

/** 工作流图标映射 */
const workflowIcons: Record<string, string> = {
  dev: "💻",
  research: "🔬",
  write: "✍️",
  translate: "🌐",
  analyze: "📊",
  design: "🎨",
  review: "👀",
  test: "🧪",
  default: "⚡",
};

/** 获取工作流图标 */
function getWorkflowIcon(name: string): string {
  const key = name.toLowerCase();
  for (const [k, v] of Object.entries(workflowIcons)) {
    if (key.includes(k)) return v;
  }
  return workflowIcons.default;
}

export function WorkflowSelector({ onSelect }: WorkflowSelectorProps) {
  const { workflows, fetchWorkflows } = useWorkflowStore();

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  if (workflows.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8">
        <div className="w-16 h-16 mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
          <svg
            className="w-8 h-8 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        </div>
        <p className="text-gray-500 dark:text-gray-400 text-center">
          No workflows available
        </p>
        <p className="text-sm text-gray-400 dark:text-gray-500 text-center mt-1">
          Add workflow configurations in the presets/team directory
        </p>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
          Select a Workflow
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Select a predefined workflow for multi-agent collaboration
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {workflows.map((workflow) => (
          <button
            key={workflow.name}
            onClick={() => onSelect(workflow)}
            className={cn(
              "group relative p-5 rounded-xl text-left",
              "bg-white dark:bg-gray-800",
              "border-2 border-gray-200 dark:border-gray-700",
              "hover:border-blue-400 dark:hover:border-blue-500",
              "hover:shadow-lg hover:shadow-blue-500/10",
              "transition-all duration-200"
            )}
          >
            {/* 背景装饰 */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-500/5 to-purple-500/5 rounded-bl-[100px] rounded-tr-xl opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* 图标 */}
            <div
              className={cn(
                "w-12 h-12 rounded-xl mb-3",
                "bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/30 dark:to-purple-900/30",
                "flex items-center justify-center",
                "text-2xl"
              )}
            >
              {getWorkflowIcon(workflow.name)}
            </div>

            {/* 名称 */}
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-1">
              {workflow.display_name}
            </h3>

            {/* 描述 */}
            <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-3">
              {workflow.description}
            </p>

            {/* 步骤数量 */}
            <div className="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500">
              <span className="flex items-center gap-1">
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
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                {workflow.steps.length} steps
              </span>
              <span className="flex items-center gap-1">
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
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                  />
                </svg>
                {new Set(workflow.steps.map((s) => s.agent)).size} agents
              </span>
            </div>

            {/* 箭头指示 */}
            <div className="absolute bottom-5 right-5 opacity-0 group-hover:opacity-100 transition-opacity">
              <svg
                className="w-5 h-5 text-blue-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                />
              </svg>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
