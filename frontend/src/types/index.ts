/** Agent 信息 */
export interface Agent {
  name: string;
  display_name: string;
  description: string;
  model: string;
  tools: string[];
  is_preset: boolean;
}

/** 工具调用信息 */
export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: string;
  status: "calling" | "completed" | "error";
}

/** 对话消息 */
export interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  created_at: string;
  /** 流式消息是否还在接收中 */
  isStreaming?: boolean;
  /** 工具调用列表 */
  tool_calls?: ToolCall[];
}

/** 会话 */
export interface Conversation {
  id: string;
  agent_name: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

/** 聊天请求 */
export interface ChatRequest {
  agent_name: string;
  messages: { role: string; content: string }[];
  conversation_id?: string;
  stream?: boolean;
}

/** 聊天响应 */
export interface ChatResponse {
  conversation_id: string;
  agent_name: string;
  content: string;
  model: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/** SSE 流式事件 */
export interface StreamEvent {
  type?: "token" | "tool_call" | "tool_result" | "done" | "error";
  token?: string;
  done?: boolean;
  error?: string;
  conversation_id?: string;
  /** 工具调用信息 */
  tool_call?: {
    id: string;
    name: string;
    arguments: Record<string, unknown>;
  };
  /** 工具调用结果 */
  tool_result?: {
    id: string;
    result: string;
    status: "completed" | "error";
  };
}

/** 设置 */
export interface AppSettings {
  apiKeys: {
    openai?: string;
    anthropic?: string;
    google?: string;
    zhipuai?: string;
    deepseek?: string;
    moonshot?: string;
  };
  apiEndpoints: {
    openai?: string;
    anthropic?: string;
    google?: string;
    zhipuai?: string;
    deepseek?: string;
    moonshot?: string;
  };
  defaultModel: string;
  theme: "light" | "dark" | "system";
  language: string;
}

/** 工作流步骤 */
export interface WorkflowStep {
  id: string;
  agent: string;
  task: string;
  depends_on: string[];
}

/** 工作流定义 */
export interface WorkflowInfo {
  name: string;
  display_name: string;
  description: string;
  steps: WorkflowStep[];
}

/** 工作流执行事件 */
export interface WorkflowEvent {
  type: "step_start" | "step_token" | "step_complete" | "step_error" | "step_skip" | "workflow_complete" | "error";
  step_id?: string;
  agent?: string;
  token?: string;
  result?: string;
  error?: string;
  message?: string;
  results?: Record<string, { status: string; result: string }>;
}
