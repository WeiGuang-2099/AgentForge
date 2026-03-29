"use client";

import { useState } from "react";
import Link from "next/link";
import { useSettingsStore } from "@/stores/settingsStore";
import { cn } from "@/lib/utils";

const MODELS = [
  { value: "gpt-4-turbo-preview", label: "GPT-4 Turbo" },
  { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  { value: "claude-3-opus-20240229", label: "Claude 3 Opus" },
  { value: "claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
  { value: "gemini-pro", label: "Gemini Pro" },
  { value: "zhipuai/glm-4", label: "智谱 GLM-4" },
  { value: "zhipuai/glm-4-flash", label: "智谱 GLM-4 Flash" },
  { value: "zhipuai/glm-4-plus", label: "智谱 GLM-4 Plus" },
];

const LANGUAGES = [
  { value: "zh-CN", label: "简体中文" },
  { value: "en", label: "English" },
];

const THEMES = [
  { value: "system", label: "跟随系统" },
  { value: "light", label: "亮色" },
  { value: "dark", label: "暗色" },
] as const;

interface ApiKeyInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  onTest: () => void;
}

function ApiKeyInput({ label, value, onChange, onTest }: ApiKeyInputProps) {
  const [showKey, setShowKey] = useState(false);

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
      <label className="w-full sm:w-40 text-sm font-medium text-gray-700 dark:text-gray-300 shrink-0">
        {label}
      </label>
      <div className="flex flex-1 gap-2">
        <div className="relative flex-1">
          <input
            type={showKey ? "text" : "password"}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="sk-..."
            className={cn(
              "w-full px-3 py-2 pr-10 rounded-lg border",
              "bg-white dark:bg-gray-800",
              "border-gray-300 dark:border-gray-600",
              "text-gray-900 dark:text-gray-100",
              "placeholder-gray-400 dark:placeholder-gray-500",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
              "transition-colors"
            )}
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className={cn(
              "absolute right-2 top-1/2 -translate-y-1/2",
              "p-1 rounded text-gray-500 hover:text-gray-700 dark:hover:text-gray-300",
              "transition-colors"
            )}
            title={showKey ? "隐藏" : "显示"}
          >
            {showKey ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            )}
          </button>
        </div>
        <button
          type="button"
          onClick={onTest}
          className={cn(
            "px-3 py-2 rounded-lg text-sm font-medium shrink-0",
            "bg-gray-100 dark:bg-gray-700",
            "text-gray-700 dark:text-gray-300",
            "hover:bg-gray-200 dark:hover:bg-gray-600",
            "transition-colors"
          )}
        >
          测试
        </button>
      </div>
    </div>
  );
}

interface CardProps {
  title: string;
  children: React.ReactNode;
}

function Card({ title, children }: CardProps) {
  return (
    <div className={cn(
      "rounded-xl border p-6",
      "bg-white dark:bg-gray-900",
      "border-gray-200 dark:border-gray-800",
      "shadow-sm"
    )}>
      <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
        {title}
      </h2>
      {children}
    </div>
  );
}

function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className={cn(
      "fixed bottom-6 right-6 z-50",
      "px-4 py-3 rounded-lg shadow-lg",
      "bg-gray-900 dark:bg-gray-100",
      "text-white dark:text-gray-900",
      "animate-fade-in"
    )}>
      <div className="flex items-center gap-3">
        <span>{message}</span>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white dark:hover:text-gray-900 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const {
    apiKeys,
    defaultModel,
    theme,
    language,
    updateApiKey,
    setDefaultModel,
    setTheme,
    setLanguage,
  } = useSettingsStore();

  const [toast, setToast] = useState<string | null>(null);

  const showToast = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  };

  const handleTestConnection = (provider: string) => {
    showToast(`正在测试 ${provider} 连接...（功能开发中）`);
  };

  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/"
            className={cn(
              "flex items-center gap-1 text-sm",
              "text-gray-600 dark:text-gray-400",
              "hover:text-gray-900 dark:hover:text-gray-100",
              "transition-colors"
            )}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            返回
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            设置
          </h1>
        </div>

        {/* Settings Cards */}
        <div className="flex flex-col gap-6">
          {/* API Key 配置 */}
          <Card title="API Key 配置">
            <div className="flex flex-col gap-4">
              <ApiKeyInput
                label="OpenAI API Key"
                value={apiKeys.openai || ""}
                onChange={(key) => updateApiKey("openai", key)}
                onTest={() => handleTestConnection("OpenAI")}
              />
              <ApiKeyInput
                label="Anthropic API Key"
                value={apiKeys.anthropic || ""}
                onChange={(key) => updateApiKey("anthropic", key)}
                onTest={() => handleTestConnection("Anthropic")}
              />
              <ApiKeyInput
                label="Google API Key"
                value={apiKeys.google || ""}
                onChange={(key) => updateApiKey("google", key)}
                onTest={() => handleTestConnection("Google")}
              />
            </div>
          </Card>

          {/* 默认模型 */}
          <Card title="默认模型">
            <select
              value={defaultModel}
              onChange={(e) => setDefaultModel(e.target.value)}
              className={cn(
                "w-full px-3 py-2 rounded-lg border",
                "bg-white dark:bg-gray-800",
                "border-gray-300 dark:border-gray-600",
                "text-gray-900 dark:text-gray-100",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "transition-colors cursor-pointer"
              )}
            >
              {MODELS.map((model) => (
                <option key={model.value} value={model.value}>
                  {model.label}
                </option>
              ))}
            </select>
          </Card>

          {/* 主题 */}
          <Card title="主题">
            <div className="flex flex-wrap gap-2">
              {THEMES.map((t) => (
                <label
                  key={t.value}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer",
                    "border transition-all",
                    theme === t.value
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                  )}
                >
                  <input
                    type="radio"
                    name="theme"
                    value={t.value}
                    checked={theme === t.value}
                    onChange={() => setTheme(t.value)}
                    className="sr-only"
                  />
                  <span
                    className={cn(
                      "w-4 h-4 rounded-full border-2 flex items-center justify-center",
                      theme === t.value
                        ? "border-blue-500"
                        : "border-gray-400 dark:border-gray-500"
                    )}
                  >
                    {theme === t.value && (
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                    )}
                  </span>
                  <span className="text-sm font-medium">{t.label}</span>
                </label>
              ))}
            </div>
          </Card>

          {/* 语言 */}
          <Card title="语言">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className={cn(
                "w-full px-3 py-2 rounded-lg border",
                "bg-white dark:bg-gray-800",
                "border-gray-300 dark:border-gray-600",
                "text-gray-900 dark:text-gray-100",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "transition-colors cursor-pointer"
              )}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.value} value={lang.value}>
                  {lang.label}
                </option>
              ))}
            </select>
          </Card>
        </div>
      </div>

      {/* Toast */}
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}

      {/* Animation styles */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fadeIn 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}
