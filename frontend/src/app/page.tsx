"use client";

import { useEffect } from "react";
import { useAgentStore } from "@/stores/agentStore";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { Sidebar } from "@/components/common/Sidebar";

export default function Home() {
  const { currentAgent, fetchAgents } = useAgentStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  return (
    <>
      <Sidebar />
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {currentAgent ? (
          <ChatWindow />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center px-4">
              <h1 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
                AgentForge
              </h1>
              <p className="text-base md:text-lg text-gray-500 dark:text-gray-400">
                开箱即用的多Agent协作框架
              </p>
              <p className="mt-2 text-sm text-gray-400 dark:text-gray-500 hidden md:block">
                从左侧选择一个 Agent 开始对话
              </p>
              <p className="mt-2 text-sm text-gray-400 dark:text-gray-500 md:hidden">
                点击左上角菜单选择 Agent 开始对话
              </p>
              <div className="mt-8 flex items-center justify-center gap-2 text-sm text-gray-400 dark:text-gray-500">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                准备就绪
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
