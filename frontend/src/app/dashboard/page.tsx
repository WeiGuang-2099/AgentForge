"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface UsageSummary {
  total_requests: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
}

interface UsageByAgent {
  agent_name: string;
  request_count: number;
  total_tokens: number;
}

interface UsageByModel {
  model: string;
  request_count: number;
  total_tokens: number;
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<UsageSummary | null>(null);
  const [byAgent, setByAgent] = useState<UsageByAgent[]>([]);
  const [byModel, setByModel] = useState<UsageByModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [summaryRes, agentRes, modelRes] = await Promise.all([
          fetch("/api/usage/summary"),
          fetch("/api/usage/by-agent"),
          fetch("/api/usage/by-model"),
        ]);

        if (!summaryRes.ok || !agentRes.ok || !modelRes.ok) {
          throw new Error("获取数据失败");
        }

        setSummary(await summaryRes.json());
        setByAgent(await agentRes.json());
        setByModel(await modelRes.json());
      } catch (err) {
        setError(err instanceof Error ? err.message : "未知错误");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const avgTokensPerRequest =
    summary && summary.total_requests > 0
      ? Math.round(summary.total_tokens / summary.total_requests)
      : 0;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* 顶部导航 */}
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link
              href="/"
              className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              <span>返回首页</span>
            </Link>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              使用量仪表板
            </h1>
            <div className="w-24" />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-700 dark:text-red-400">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            {/* 统计卡片 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* 总请求数 */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-blue-600 dark:text-blue-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 10V3L4 14h7v7l9-11h-7z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      总请求数
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {summary?.total_requests.toLocaleString() ?? 0}
                    </p>
                  </div>
                </div>
              </div>

              {/* 总 Token 数 */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-green-600 dark:text-green-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      总 Token 数
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {summary?.total_tokens.toLocaleString() ?? 0}
                    </p>
                  </div>
                </div>
              </div>

              {/* 平均每请求 Token */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                    <svg
                      className="w-6 h-6 text-purple-600 dark:text-purple-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      平均每请求 Token
                    </p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {avgTokensPerRequest.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 按 Agent 使用量 */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 mb-8">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  按 Agent 使用量
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50">
                      <th className="px-6 py-3 font-medium">Agent 名称</th>
                      <th className="px-6 py-3 font-medium">请求次数</th>
                      <th className="px-6 py-3 font-medium">总 Token 数</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                    {byAgent.length === 0 ? (
                      <tr>
                        <td
                          colSpan={3}
                          className="px-6 py-8 text-center text-gray-500 dark:text-gray-400"
                        >
                          暂无数据
                        </td>
                      </tr>
                    ) : (
                      byAgent.map((item) => (
                        <tr
                          key={item.agent_name}
                          className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
                        >
                          <td className="px-6 py-4 text-gray-900 dark:text-gray-100 font-medium">
                            {item.agent_name}
                          </td>
                          <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                            {item.request_count.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                            {item.total_tokens.toLocaleString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 按模型使用量 */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  按模型使用量
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50">
                      <th className="px-6 py-3 font-medium">模型</th>
                      <th className="px-6 py-3 font-medium">请求次数</th>
                      <th className="px-6 py-3 font-medium">总 Token 数</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                    {byModel.length === 0 ? (
                      <tr>
                        <td
                          colSpan={3}
                          className="px-6 py-8 text-center text-gray-500 dark:text-gray-400"
                        >
                          暂无数据
                        </td>
                      </tr>
                    ) : (
                      byModel.map((item) => (
                        <tr
                          key={item.model}
                          className="hover:bg-gray-50 dark:hover:bg-gray-800/50"
                        >
                          <td className="px-6 py-4 text-gray-900 dark:text-gray-100 font-medium">
                            {item.model}
                          </td>
                          <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                            {item.request_count.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-gray-600 dark:text-gray-400">
                            {item.total_tokens.toLocaleString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
