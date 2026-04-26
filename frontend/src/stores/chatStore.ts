import { create } from "zustand";
import type { Message, Conversation, ToolCall } from "@/types";
import { generateId } from "@/lib/utils";
import { conversationApi } from "@/lib/api";

interface ChatState {
  conversations: Conversation[];
  currentConversationId: string | null;
  isStreaming: boolean;

  // Actions
  createConversation: (agentName: string) => string;
  setCurrentConversation: (id: string | null) => void;
  addMessage: (conversationId: string, message: Omit<Message, "id" | "created_at">) => void;
  updateLastMessage: (conversationId: string, content: string) => void;
  updateLastMessageToolCalls: (conversationId: string, toolCalls: ToolCall[]) => void;
  setStreaming: (isStreaming: boolean) => void;
  getCurrentMessages: () => Message[];
  deleteConversation: (id: string) => void;
  loadConversations: (agentName?: string) => Promise<void>;
  loadMessages: (conversationId: string) => Promise<void>;
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

  setCurrentConversation: (id: string | null) => {
    set({ currentConversationId: id });
    // Load messages from backend if conversation exists but has no messages
    if (id) {
      const conv = get().conversations.find(c => c.id === id);
      if (conv && conv.messages.length === 0) {
        get().loadMessages(id);
      }
    }
  },

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

  deleteConversation: (id: string) => {
    // Fire and forget backend deletion
    conversationApi.delete(id).catch(() => {});
    // Then do existing local state removal
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversationId:
        state.currentConversationId === id ? null : state.currentConversationId,
    }));
  },

  loadConversations: async (agentName?: string) => {
    try {
      const backendConversations = await conversationApi.list(agentName);
      if (backendConversations && Array.isArray(backendConversations)) {
        // Merge backend conversations with local state
        // Use backend as source of truth, but don't overwrite local messages mid-stream
        set((state) => {
          const existingIds = new Set(state.conversations.map(c => c.id));
          const newConversations = backendConversations
            .filter((c: any) => !existingIds.has(c.id))
            .map((c: any) => ({
              id: c.id,
              agent_name: c.agent_name,
              title: c.title || `Chat with ${c.agent_name}`,
              messages: [],
              created_at: c.created_at,
              updated_at: c.updated_at,
            }));
          return {
            conversations: [...state.conversations, ...newConversations]
          };
        });
      }
    } catch (error) {
      // Silently fail - local conversations still work
      console.warn('Failed to load conversations from backend:', error);
    }
  },

  loadMessages: async (conversationId: string) => {
    try {
      const messages = await conversationApi.getMessages(conversationId);
      if (messages && Array.isArray(messages)) {
        set((state) => ({
          conversations: state.conversations.map(c =>
            c.id === conversationId
              ? { ...c, messages: messages.map((m: any) => ({
                  id: m.id,
                  role: m.role,
                  content: m.content,
                  created_at: m.created_at,
                })) }
              : c
          )
        }));
      }
    } catch (error) {
      console.warn('Failed to load messages:', error);
    }
  },
}));
