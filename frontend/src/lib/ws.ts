/**
 * WebSocket 客户端封装
 */

export interface WSMessage {
  type: "token" | "done" | "error" | "pong";
  content?: string;
  message?: string;
}

export interface WSOptions {
  onToken?: (content: string) => void;
  onDone?: () => void;
  onError?: (message: string) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export class AgentForgeWS {
  private ws: WebSocket | null = null;
  private conversationId: string;
  private options: WSOptions;
  private reconnectCount = 0;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private isManualClose = false;

  constructor(conversationId: string, options: WSOptions = {}) {
    this.conversationId = conversationId;
    this.options = {
      reconnectAttempts: 3,
      reconnectInterval: 2000,
      ...options,
    };
  }

  connect(): void {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/chat/${this.conversationId}`;

    this.ws = new WebSocket(url);
    this.isManualClose = false;

    this.ws.onopen = () => {
      this.reconnectCount = 0;
      this.startHeartbeat();
      this.options.onConnect?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const data: WSMessage = JSON.parse(event.data);
        switch (data.type) {
          case "token":
            this.options.onToken?.(data.content || "");
            break;
          case "done":
            this.options.onDone?.();
            break;
          case "error":
            this.options.onError?.(data.message || "未知错误");
            break;
          case "pong":
            // 心跳响应，无需处理
            break;
        }
      } catch {
        console.error("WebSocket 消息解析失败:", event.data);
      }
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      this.options.onDisconnect?.();

      if (!this.isManualClose && this.reconnectCount < (this.options.reconnectAttempts || 3)) {
        this.reconnectCount++;
        setTimeout(() => this.connect(), this.options.reconnectInterval);
      }
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket 错误:", error);
    };
  }

  sendChat(agentName: string, messages: { role: string; content: string }[]): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          type: "chat",
          agent_name: agentName,
          messages,
        })
      );
    } else {
      this.options.onError?.("WebSocket 未连接");
    }
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();
    this.ws?.close();
    this.ws = null;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
