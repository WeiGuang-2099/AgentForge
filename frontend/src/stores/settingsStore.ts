import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AppSettings } from "@/types";

interface SettingsState extends AppSettings {
  updateApiKey: (provider: "openai" | "anthropic" | "google", key: string) => void;
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
      },
      defaultModel: "gpt-4-turbo-preview",
      theme: "system",
      language: "zh-CN",

      updateApiKey: (provider, key) =>
        set((state) => ({
          apiKeys: { ...state.apiKeys, [provider]: key },
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
