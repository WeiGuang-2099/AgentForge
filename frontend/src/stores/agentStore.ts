import { create } from "zustand";
import type { Agent } from "@/types";
import { agentApi } from "@/lib/api";

interface AgentState {
  agents: Agent[];
  currentAgent: Agent | null;
  isLoading: boolean;

  fetchAgents: () => Promise<void>;
  setCurrentAgent: (agent: Agent) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  currentAgent: null,
  isLoading: false,

  fetchAgents: async () => {
    set({ isLoading: true });
    try {
      const agents = await agentApi.list();
      set({ agents, isLoading: false });
    } catch (error) {
      console.error("获取 Agent 列表失败:", error);
      set({ isLoading: false });
    }
  },

  setCurrentAgent: (agent) => set({ currentAgent: agent }),
}));
