"use client";

import { useState, useRef, useEffect } from "react";
import type { WorkflowInfo } from "@/types";
import { useWorkflowStore } from "@/stores/workflowStore";
import { streamWorkflow } from "@/lib/api";
import { WorkflowGraph } from "./WorkflowGraph";
import { cn } from "@/lib/utils";

interface WorkflowPanelProps {
  workflow: WorkflowInfo;
  onBack: () => void;
}

interface StepOutput {
  stepId: string;
  agent: string;
  tokens: string[];
  result: string;
  error: string;
  isExpanded: boolean;
}

export function WorkflowPanel({ workflow, onBack }: WorkflowPanelProps) {
  const [task, setTask] = useState("");
  const [stepOutputs, setStepOutputs] = useState<Record<string, StepOutput>>({});
  const { isExecuting, setExecuting, initStepStates, updateStepState, reset } =
    useWorkflowStore();
  const outputRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // 初始化步骤状态
  useEffect(() => {
    initStepStates(workflow);
    // 初始化输出
    const outputs: Record<string, StepOutput> = {};
    workflow.steps.forEach((step) => {
      outputs[step.id] = {
        stepId: step.id,
        agent: step.agent,
        tokens: [],
        result: "",
        error: "",
        isExpanded: true,
      };
    });
    setStepOutputs(outputs);
  }, [workflow, initStepStates]);

  // 切换步骤输出展开
  const toggleStepExpanded = (stepId: string) => {
    setStepOutputs((prev) => ({
      ...prev,
      [stepId]: {
        ...prev[stepId],
        isExpanded: !prev[stepId]?.isExpanded,
      },
    }));
  };

  // 执行工作流
  const handleExecute = async () => {
    if (!task.trim() || isExecuting) return;

    setExecuting(true);
    initStepStates(workflow);

    // 重置输出
    const outputs: Record<string, StepOutput> = {};
    workflow.steps.forEach((step) => {
      outputs[step.id] = {
        stepId: step.id,
        agent: step.agent,
        tokens: [],
        result: "",
        error: "",
        isExpanded: true,
      };
    });
    setStepOutputs(outputs);

    try {
      for await (const event of streamWorkflow(workflow.name, task)) {
        switch (event.type) {
          case "step_start":
            if (event.step_id) {
              updateStepState(event.step_id, { status: "running" });
            }
            break;

          case "step_token":
            if (event.step_id && event.token) {
              setStepOutputs((prev) => ({
                ...prev,
                [event.step_id!]: {
                  ...prev[event.step_id!],
                  tokens: [...(prev[event.step_id!]?.tokens || []), event.token!],
                },
              }));
              // 滚动到底部
              const ref = outputRefs.current[event.step_id];
              if (ref) {
                ref.scrollTop = ref.scrollHeight;
              }
            }
            break;

          case "step_complete":
            if (event.step_id) {
              updateStepState(event.step_id, {
                status: "completed",
                result: event.result || "",
              });
              setStepOutputs((prev) => ({
                ...prev,
                [event.step_id!]: {
                  ...prev[event.step_id!],
                  result: event.result || "",
                },
              }));
            }
            break;

          case "step_error":
            if (event.step_id) {
              updateStepState(event.step_id, {
                status: "error",
                error: event.error || "",
              });
              setStepOutputs((prev) => ({
                ...prev,
                [event.step_id!]: {
                  ...prev[event.step_id!],
                  error: event.error || "",
                },
              }));
            }
            break;

          case "step_skip":
            if (event.step_id) {
              updateStepState(event.step_id, { status: "skipped" });
            }
            break;

          case "workflow_complete":
            // 工作流完成
            break;

          case "error":
            console.error("工作流错误:", event.message);
            break;
        }
      }
    } catch (error) {
      console.error("执行工作流失败:", error);
    } finally {
      setExecuting(false);
    }
  };

  // 重置
  const handleReset = () => {
    reset();
    initStepStates(workflow);
    const outputs: Record<string, StepOutput> = {};
    workflow.steps.forEach((step) => {
      outputs[step.id] = {
        stepId: step.id,
        agent: step.agent,
        tokens: [],
        result: "",
        error: "",
        isExpanded: true,
      };
    });
    setStepOutputs(outputs);
    setTask("");
  };

  return (
    <div className="flex flex-col lg:flex-row h-full gap-4 p-4">
      {/* 左侧：工作流图 */}
      <div className="flex-1 min-h-[300px] lg:min-h-0">
        <div className="h-full flex flex-col">
          {/* 顶部操作栏 */}
          <div className="flex items-center justify-between mb-3">
            <button
              onClick={onBack}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-lg",
                "text-sm text-gray-600 dark:text-gray-400",
                "hover:bg-gray-100 dark:hover:bg-gray-800",
                "transition-colors"
              )}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              返回
            </button>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
              {workflow.display_name}
            </h2>
            <div className="w-16" /> {/* 占位 */}
          </div>

          {/* 工作流图 */}
          <div className="flex-1 rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
            <WorkflowGraph workflow={workflow} />
          </div>
        </div>
      </div>

      {/* 右侧：执行面板 */}
      <div className="w-full lg:w-[400px] flex flex-col bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* 任务输入 */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            任务描述
          </label>
          <textarea
            value={task}
            onChange={(e) => setTask(e.target.value)}
            placeholder="输入要执行的任务..."
            className={cn(
              "w-full h-24 px-3 py-2 rounded-lg resize-none",
              "bg-gray-50 dark:bg-gray-800",
              "border border-gray-200 dark:border-gray-700",
              "text-gray-800 dark:text-gray-200",
              "placeholder-gray-400 dark:placeholder-gray-500",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
              "transition-all"
            )}
            disabled={isExecuting}
          />
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleExecute}
              disabled={!task.trim() || isExecuting}
              className={cn(
                "flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg",
                "font-medium text-white",
                "bg-blue-600 hover:bg-blue-700",
                "disabled:bg-gray-400 disabled:cursor-not-allowed",
                "transition-colors"
              )}
            >
              {isExecuting ? (
                <>
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  执行中...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  开始执行
                </>
              )}
            </button>
            <button
              onClick={handleReset}
              disabled={isExecuting}
              className={cn(
                "px-4 py-2 rounded-lg",
                "text-gray-600 dark:text-gray-400",
                "bg-gray-100 dark:bg-gray-800",
                "hover:bg-gray-200 dark:hover:bg-gray-700",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "transition-colors"
              )}
            >
              重置
            </button>
          </div>
        </div>

        {/* 步骤输出列表 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">
            执行详情
          </h3>
          {workflow.steps.map((step) => {
            const output = stepOutputs[step.id];
            const content = output?.tokens.join("") || output?.result || "";
            const hasContent = content.length > 0 || output?.error;

            return (
              <div
                key={step.id}
                className={cn(
                  "rounded-lg border",
                  output?.error
                    ? "border-red-300 dark:border-red-700"
                    : "border-gray-200 dark:border-gray-700"
                )}
              >
                {/* 步骤标题 */}
                <button
                  onClick={() => toggleStepExpanded(step.id)}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2",
                    "bg-gray-50 dark:bg-gray-800 rounded-t-lg",
                    "hover:bg-gray-100 dark:hover:bg-gray-700",
                    "transition-colors"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {step.agent}
                    </span>
                    {hasContent && (
                      <span className="w-2 h-2 rounded-full bg-green-500" />
                    )}
                  </div>
                  <svg
                    className={cn(
                      "w-4 h-4 text-gray-500 transition-transform",
                      output?.isExpanded ? "rotate-180" : ""
                    )}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* 步骤输出内容 */}
                {output?.isExpanded && (
                  <div
                    ref={(el) => { outputRefs.current[step.id] = el; }}
                    className={cn(
                      "px-3 py-2 max-h-[200px] overflow-y-auto",
                      "bg-white dark:bg-gray-900",
                      "text-sm text-gray-700 dark:text-gray-300",
                      "font-mono whitespace-pre-wrap break-words"
                    )}
                  >
                    {output?.error ? (
                      <span className="text-red-500">{output.error}</span>
                    ) : content ? (
                      content
                    ) : (
                      <span className="text-gray-400 dark:text-gray-500 italic">
                        等待执行...
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
