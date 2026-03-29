import { create } from "zustand";
import type { WorkflowInfo } from "@/types";
import { workflowApi } from "@/lib/api";

interface StepState {
  id: string;
  agent: string;
  status: "pending" | "running" | "completed" | "error" | "skipped";
  result: string;
  error: string;
}

interface WorkflowState {
  workflows: WorkflowInfo[];
  currentWorkflow: WorkflowInfo | null;
  isExecuting: boolean;
  stepStates: Record<string, StepState>;
  
  fetchWorkflows: () => Promise<void>;
  setCurrentWorkflow: (workflow: WorkflowInfo | null) => void;
  setExecuting: (executing: boolean) => void;
  initStepStates: (workflow: WorkflowInfo) => void;
  updateStepState: (stepId: string, update: Partial<StepState>) => void;
  reset: () => void;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  workflows: [],
  currentWorkflow: null,
  isExecuting: false,
  stepStates: {},

  fetchWorkflows: async () => {
    try {
      const workflows = await workflowApi.list();
      set({ workflows });
    } catch (error) {
      console.error("获取工作流列表失败:", error);
    }
  },

  setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),
  setExecuting: (executing) => set({ isExecuting: executing }),

  initStepStates: (workflow) => {
    const states: Record<string, StepState> = {};
    for (const step of workflow.steps) {
      states[step.id] = {
        id: step.id,
        agent: step.agent,
        status: "pending",
        result: "",
        error: "",
      };
    }
    set({ stepStates: states });
  },

  updateStepState: (stepId, update) =>
    set((state) => ({
      stepStates: {
        ...state.stepStates,
        [stepId]: { ...state.stepStates[stepId], ...update },
      },
    })),

  reset: () => set({ stepStates: {}, isExecuting: false }),
}));
