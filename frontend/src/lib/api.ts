import axios from "axios";
import type { Agent, ChatRequest, ChatResponse, StreamEvent, WorkflowInfo, WorkflowEvent } from "@/types";
import { useAuthStore } from "@/stores/authStore";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for auth token
apiClient.interceptors.request.use((config) => {
  // Access zustand store outside React components
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for 401 handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth state and let the UI handle redirect
      useAuthStore.getState().logout();
      // Only redirect if in browser
      if (typeof window !== 'undefined') {
        window.location.href = '/auth';
      }
    }
    return Promise.reject(error);
  }
);

/** Agent API */
export const agentApi = {
  list: () => apiClient.get<Agent[]>("/agents").then((r) => r.data),
  get: (name: string) => apiClient.get<Agent>(`/agents/${name}`).then((r) => r.data),
  create: (data: Partial<Agent> & { system_prompt: string }) =>
    apiClient.post("/agents", data).then((r) => r.data),
};

/** Chat API (非流式) */
export const chatApi = {
  send: (data: ChatRequest) =>
    apiClient.post<ChatResponse>("/chat", data).then((r) => r.data),
};

/** 流式聊天 - 使用 fetch + SSE */
export async function* streamChat(
  data: ChatRequest
): AsyncGenerator<StreamEvent> {
  const token = useAuthStore.getState().accessToken;
  const chatHeaders: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    chatHeaders["Authorization"] = `Bearer ${token}`;
  }
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: chatHeaders,
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch {
          // 忽略解析错误
        }
      }
    }
  }
}

/** Workflow API */
export const workflowApi = {
  list: () => apiClient.get<WorkflowInfo[]>("/workflows").then((r) => r.data),
};

/** Conversation API */
export interface ConversationInfo {
  id: string;
  agent_name: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageInfo {
  id: string;
  role: string;
  content: string;
  created_at: string;
}

export const conversationApi = {
  list: (agentName?: string) => {
    const params = new URLSearchParams();
    if (agentName) params.set("agent_name", agentName);
    return apiClient
      .get<ConversationInfo[]>(`/conversations?${params.toString()}`)
      .then((r) => r.data);
  },
  getMessages: (conversationId: string) =>
    apiClient
      .get<MessageInfo[]>(`/conversations/${conversationId}/messages`)
      .then((r) => r.data),
  delete: (conversationId: string) =>
    apiClient
      .delete(`/conversations/${conversationId}`)
      .then((r) => r.data),
};

/** 流式执行工作流 */
export async function* streamWorkflow(
  workflowName: string,
  task: string
): AsyncGenerator<WorkflowEvent> {
  const wfToken = useAuthStore.getState().accessToken;
  const wfHeaders: Record<string, string> = { "Content-Type": "application/json" };
  if (wfToken) {
    wfHeaders["Authorization"] = `Bearer ${wfToken}`;
  }
  const response = await fetch("/api/workflows/execute/stream", {
    method: "POST",
    headers: wfHeaders,
    body: JSON.stringify({ workflow_name: workflowName, task }),
  });

  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          yield JSON.parse(line.slice(6));
        } catch { /* ignore */ }
      }
    }
  }
}

export default apiClient;
