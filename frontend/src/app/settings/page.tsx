"use client";

import { useState } from "react";
import Link from "next/link";
import { useSettingsStore } from "@/stores/settingsStore";
import { cn } from "@/lib/utils";

// Model groups by provider
const modelGroups = [
  {
    provider: "OpenAI",
    models: [
      { value: "openai/gpt-4-turbo-preview", label: "GPT-4 Turbo" },
      { value: "openai/gpt-4o", label: "GPT-4o" },
      { value: "openai/gpt-4o-mini", label: "GPT-4o Mini" },
      { value: "openai/gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
      { value: "openai/o1-preview", label: "o1 Preview" },
      { value: "openai/o1-mini", label: "o1 Mini" },
    ],
  },
  {
    provider: "Anthropic",
    models: [
      { value: "anthropic/claude-3-opus-20240229", label: "Claude 3 Opus" },
      { value: "anthropic/claude-3-sonnet-20240229", label: "Claude 3 Sonnet" },
      { value: "anthropic/claude-3-haiku-20240307", label: "Claude 3 Haiku" },
      { value: "anthropic/claude-3.5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
    ],
  },
  {
    provider: "Google",
    models: [
      { value: "gemini/gemini-pro", label: "Gemini Pro" },
      { value: "gemini/gemini-1.5-pro", label: "Gemini 1.5 Pro" },
      { value: "gemini/gemini-1.5-flash", label: "Gemini 1.5 Flash" },
    ],
  },
  {
    provider: "智谱 AI / Zhipu AI",
    providerId: "zhipuai",
    models: [
      { value: "zhipuai/glm-4", label: "GLM-4" },
      { value: "zhipuai/glm-4-flash", label: "GLM-4 Flash" },
      { value: "zhipuai/glm-4-plus", label: "GLM-4 Plus" },
      { value: "openai/glm-4.7", label: "GLM-4.7 (Reasoning)" },
    ],
  },
  {
    provider: "DeepSeek",
    models: [
      { value: "deepseek/deepseek-chat", label: "DeepSeek Chat" },
      { value: "deepseek/deepseek-coder", label: "DeepSeek Coder" },
      { value: "deepseek/deepseek-reasoner", label: "DeepSeek Reasoner" },
    ],
  },
  {
    provider: "Moonshot",
    models: [
      { value: "openai/moonshot-v1-8k", label: "Moonshot v1 8K" },
      { value: "openai/moonshot-v1-32k", label: "Moonshot v1 32K" },
      { value: "openai/moonshot-v1-128k", label: "Moonshot v1 128K" },
    ],
  },
];

// API Providers configuration
const apiProviders = [
  {
    id: "openai" as const,
    name: "OpenAI",
    placeholder: "sk-...",
    defaultEndpoint: "https://api.openai.com/v1",
  },
  {
    id: "anthropic" as const,
    name: "Anthropic",
    placeholder: "sk-ant-...",
    defaultEndpoint: "https://api.anthropic.com",
  },
  {
    id: "google" as const,
    name: "Google",
    placeholder: "AIza...",
    defaultEndpoint: "",
  },
  {
    id: "zhipuai" as const,
    name: "智谱 AI / Zhipu AI",
    placeholder: "your-api-key",
    defaultEndpoint: "https://open.bigmodel.cn/api/paas/v4",
  },
  {
    id: "deepseek" as const,
    name: "DeepSeek",
    placeholder: "sk-...",
    defaultEndpoint: "https://api.deepseek.com/v1",
  },
  {
    id: "moonshot" as const,
    name: "Moonshot",
    placeholder: "sk-...",
    defaultEndpoint: "https://api.moonshot.cn/v1",
  },
];

const LANGUAGES = [
  { value: "zh-CN", label: "简体中文" },
  { value: "en", label: "English" },
];

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

// Chevron icons
function ChevronDown({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

function ChevronUp({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  );
}

// Eye icons
function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  );
}

function EyeOffIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
    </svg>
  );
}

interface ProviderBlockProps {
  provider: typeof apiProviders[0];
  apiKey: string;
  apiEndpoint: string;
  onApiKeyChange: (key: string) => void;
  onEndpointChange: (endpoint: string) => void;
  onTest: () => void;
  t: (zh: string, en: string) => string;
}

function ProviderBlock({ 
  provider, 
  apiKey, 
  apiEndpoint, 
  onApiKeyChange, 
  onEndpointChange, 
  onTest,
  t 
}: ProviderBlockProps) {
  const [expanded, setExpanded] = useState(false);
  const [showKey, setShowKey] = useState(false);

  return (
    <div className={cn(
      "border rounded-lg overflow-hidden",
      "border-gray-200 dark:border-gray-700"
    )}>
      {/* Header - clickable to expand/collapse */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className={cn(
          "w-full flex items-center justify-between px-4 py-3",
          "bg-gray-50 dark:bg-gray-800/50",
          "hover:bg-gray-100 dark:hover:bg-gray-800",
          "transition-colors text-left"
        )}
      >
        <div className="flex items-center gap-3">
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {provider.name}
          </span>
          {apiKey && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
              {t("已配置", "Configured")}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>

      {/* Expandable content */}
      {expanded && (
        <div className="px-4 py-4 space-y-4 bg-white dark:bg-gray-900">
          {/* API Key input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              API Key
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => onApiKeyChange(e.target.value)}
                  placeholder={provider.placeholder || t("请输入 API Key", "Enter API Key")}
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
                  title={showKey ? t("隐藏", "Hide") : t("显示", "Show")}
                >
                  {showKey ? (
                    <EyeOffIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
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
                {t("测试连接", "Test Connection")}
              </button>
            </div>
          </div>

          {/* Custom Endpoint input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {t("API 端点（可选）", "API Endpoint (Optional)")}
            </label>
            <input
              type="text"
              value={apiEndpoint}
              onChange={(e) => onEndpointChange(e.target.value)}
              placeholder={provider.defaultEndpoint || t("使用默认端点", "Use default endpoint")}
              className={cn(
                "w-full px-3 py-2 rounded-lg border",
                "bg-white dark:bg-gray-800",
                "border-gray-300 dark:border-gray-600",
                "text-gray-900 dark:text-gray-100",
                "placeholder-gray-400 dark:placeholder-gray-500",
                "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
                "transition-colors text-sm"
              )}
            />
            {provider.defaultEndpoint && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {t("默认", "Default")}: {provider.defaultEndpoint}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function SettingsPage() {
  const {
    apiKeys,
    apiEndpoints,
    defaultModel,
    theme,
    language,
    updateApiKey,
    updateApiEndpoint,
    setDefaultModel,
    setTheme,
    setLanguage,
  } = useSettingsStore();

  const [toast, setToast] = useState<string | null>(null);

  // Simple i18n function
  const t = (zh: string, en: string) => language === "zh-CN" ? zh : en;

  // Theme options with i18n
  const THEMES = [
    { value: "system" as const, label: t("跟随系统", "System") },
    { value: "light" as const, label: t("亮色", "Light") },
    { value: "dark" as const, label: t("暗色", "Dark") },
  ];

  const showToast = (message: string) => {
    setToast(message);
    setTimeout(() => setToast(null), 3000);
  };

  const handleTestConnection = (providerName: string) => {
    showToast(t(
      `正在测试 ${providerName} 连接...（功能开发中）`,
      `Testing ${providerName} connection... (Feature in Development)`
    ));
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
            {t("返回首页", "Back to Home")}
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {t("设置", "Settings")}
          </h1>
        </div>

        {/* Settings Cards */}
        <div className="flex flex-col gap-6">
          {/* API Key Configuration */}
          <Card title={t("API 密钥配置", "API Key Configuration")}>
            <div className="flex flex-col gap-3">
              {apiProviders.map((provider) => (
                <ProviderBlock
                  key={provider.id}
                  provider={provider}
                  apiKey={apiKeys[provider.id] || ""}
                  apiEndpoint={apiEndpoints[provider.id] || ""}
                  onApiKeyChange={(key) => updateApiKey(provider.id, key)}
                  onEndpointChange={(endpoint) => updateApiEndpoint(provider.id, endpoint)}
                  onTest={() => handleTestConnection(provider.name)}
                  t={t}
                />
              ))}
            </div>
          </Card>

          {/* Default Model */}
          <Card title={t("默认模型", "Default Model")}>
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
              <option value="" disabled>
                {t("选择默认模型", "Select Default Model")}
              </option>
              {modelGroups.map((group) => (
                <optgroup key={group.provider} label={group.provider}>
                  {group.models.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </Card>

          {/* Theme */}
          <Card title={t("主题", "Theme")}>
            <div className="flex flex-wrap gap-2">
              {THEMES.map((themeOption) => (
                <label
                  key={themeOption.value}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2 rounded-lg cursor-pointer",
                    "border transition-all",
                    theme === themeOption.value
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                  )}
                >
                  <input
                    type="radio"
                    name="theme"
                    value={themeOption.value}
                    checked={theme === themeOption.value}
                    onChange={() => setTheme(themeOption.value)}
                    className="sr-only"
                  />
                  <span
                    className={cn(
                      "w-4 h-4 rounded-full border-2 flex items-center justify-center",
                      theme === themeOption.value
                        ? "border-blue-500"
                        : "border-gray-400 dark:border-gray-500"
                    )}
                  >
                    {theme === themeOption.value && (
                      <span className="w-2 h-2 rounded-full bg-blue-500" />
                    )}
                  </span>
                  <span className="text-sm font-medium">{themeOption.label}</span>
                </label>
              ))}
            </div>
          </Card>

          {/* Language */}
          <Card title={t("语言", "Language")}>
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
