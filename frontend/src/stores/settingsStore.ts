import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AppSettings } from "@/types";

type ApiProvider = "openai" | "anthropic" | "google" | "zhipuai" | "deepseek" | "moonshot";

interface SettingsState extends AppSettings {
  updateApiKey: (provider: ApiProvider, key: string) => void;
  updateApiEndpoint: (provider: ApiProvider, endpoint: string) => void;
  setDefaultModel: (model: string) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setLanguage: (language: string) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      apiKeys: {
        openai: "",
        anthropic: "",
        google: "",
        zhipuai: "",
        deepseek: "",
        moonshot: "",
      },
      apiEndpoints: {
        openai: "",
        anthropic: "",
        google: "",
        zhipuai: "",
        deepseek: "",
        moonshot: "",
      },
      defaultModel: "openai/gpt-4-turbo-preview",
      theme: "system",
      language: "zh-CN",

      updateApiKey: (provider, key) =>
        set((state) => ({
          apiKeys: { ...state.apiKeys, [provider]: key },
        })),
      updateApiEndpoint: (provider, endpoint) =>
        set((state) => ({
          apiEndpoints: { ...state.apiEndpoints, [provider]: endpoint },
        })),
      setDefaultModel: (model) => set({ defaultModel: model }),
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
    }),
    {
      name: "agentforge-settings",
    }
  )
);
