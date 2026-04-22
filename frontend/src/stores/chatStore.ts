import { create } from "zustand";
import type { Message, Conversation, ToolCall } from "@/types";
import { generateId } from "@/lib/utils";

interface ChatState {
  conversations: Conversation[];
  currentConversationId: string | null;
  isStreaming: boolean;

  // Actions
  createConversation: (agentName: string) => string;
  setCurrentConversation: (id: string) => void;
  addMessage: (conversationId: string, message: Omit<Message, "id" | "created_at">) => void;
  updateLastMessage: (conversationId: string, content: string) => void;
  updateLastMessageToolCalls: (conversationId: string, toolCalls: ToolCall[]) => void;
  setStreaming: (isStreaming: boolean) => void;
  getCurrentMessages: () => Message[];
  deleteConversation: (id: string) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversationId: null,
  isStreaming: false,

  createConversation: (agentName: string) => {
    const id = generateId();
    const conversation: Conversation = {
      id,
      agent_name: agentName,
      title: "New Conversation",
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    set((state) => ({
      conversations: [conversation, ...state.conversations],
      currentConversationId: id,
    }));
    return id;
  },

  setCurrentConversation: (id) => set({ currentConversationId: id }),

  addMessage: (conversationId, message) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: [
                ...conv.messages,
                { ...message, id: generateId(), created_at: new Date().toISOString() },
              ],
              updated_at: new Date().toISOString(),
            }
          : conv
      ),
    })),

  updateLastMessage: (conversationId, content) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: conv.messages.map((msg, i) =>
                i === conv.messages.length - 1 ? { ...msg, content } : msg
              ),
            }
          : conv
      ),
    })),

  updateLastMessageToolCalls: (conversationId, toolCalls) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.id === conversationId
          ? {
              ...conv,
              messages: conv.messages.map((msg, i) =>
                i === conv.messages.length - 1 ? { ...msg, tool_calls: toolCalls } : msg
              ),
            }
          : conv
      ),
    })),

  setStreaming: (isStreaming) => set({ isStreaming }),

  getCurrentMessages: () => {
    const state = get();
    const conv = state.conversations.find((c) => c.id === state.currentConversationId);
    return conv?.messages || [];
  },

  deleteConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversationId:
        state.currentConversationId === id ? null : state.currentConversationId,
    })),
}));
