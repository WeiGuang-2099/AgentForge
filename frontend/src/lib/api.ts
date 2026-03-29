import axios from "axios";
import type { Agent, ChatRequest, ChatResponse, StreamEvent, WorkflowInfo, WorkflowEvent } from "@/types";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

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
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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

/** 流式执行工作流 */
export async function* streamWorkflow(
  workflowName: string,
  task: string
): AsyncGenerator<WorkflowEvent> {
  const response = await fetch("/api/workflows/execute/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
