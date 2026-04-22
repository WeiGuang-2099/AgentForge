"""
AgentForge CLI - 命令行交互工具

用法:
    python -m app.cli                    # 默认使用 assistant Agent
    python -m app.cli --agent coder      # 指定 Agent
    python -m app.cli --list             # 列出所有可用 Agent
"""
import asyncio
import argparse
import sys

from app.core.agent import AgentEngine, AgentNotFoundError
from app.core.llm import LLMError


async def list_agents(engine: AgentEngine):
    """列出所有可用的 Agent"""
    agents = engine.list_agents()
    if not agents:
        print("没有可用的 Agent。")
        return
    
    print("\n可用的 Agent:")
    print("-" * 60)
    for agent in agents:
        tools_str = ", ".join(agent.tools) if agent.tools else "无"
        print(f"  {agent.name:<15} {agent.display_name}")
        print(f"  {'':15} {agent.description}")
        print(f"  {'':15} 模型: {agent.model} | 工具: {tools_str}")
        print()


async def chat_loop(engine: AgentEngine, agent_name: str):
    """交互式对话循环"""
    profile = engine.get_agent(agent_name)
    if not profile:
        print(f"错误: Agent '{agent_name}' 未找到。使用 --list 查看可用 Agent。")
        return
    
    print(f"\nAgentForge CLI")
    print(f"当前 Agent: {profile.display_name} ({profile.name})")
    print(f"模型: {profile.model}")
    print(f"输入 'exit' 或 'quit' 退出, 'clear' 清空对话历史")
    print("-" * 60)
    
    messages = []
    
    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("exit", "quit"):
            print("再见!")
            break
        
        if user_input.lower() == "clear":
            messages.clear()
            print("对话历史已清空。")
            continue
        
        messages.append({"role": "user", "content": user_input})
        
        try:
            # 使用流式输出
            print(f"\n{profile.display_name}: ", end="", flush=True)
            full_response = ""
            async for token in engine.run_stream(agent_name, messages):
                print(token, end="", flush=True)
                full_response += token
            print()  # 换行
            
            # 将助手回复加入对话历史
            messages.append({"role": "assistant", "content": full_response})
            
        except LLMError as e:
            print(f"\nLLM 调用错误: {e}")
            # 移除失败的用户消息
            messages.pop()
        except Exception as e:
            print(f"\n发生错误: {e}")
            messages.pop()


async def init_db_cmd():
    """Run database migrations."""
    from app.models.database import init_db, close_db
    print("Initializing database...")
    await init_db()
    await close_db()
    print("Database initialized successfully.")


async def main():
    parser = argparse.ArgumentParser(description="AgentForge CLI - 命令行交互工具")
    parser.add_argument("--agent", "-a", type=str, default="assistant",
                       help="选择 Agent (默认: assistant)")
    parser.add_argument("--list", "-l", action="store_true",
                       help="列出所有可用 Agent")
    parser.add_argument("--init-db", action="store_true",
                       help="初始化数据库表")
    args = parser.parse_args()

    if args.init_db:
        await init_db_cmd()
        return

    # 初始化引擎
    engine = AgentEngine()
    await engine.initialize()

    if args.list:
        await list_agents(engine)
        return

    await chat_loop(engine, args.agent)


if __name__ == "__main__":
    # 为 Windows 终端设置 UTF-8 编码
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    asyncio.run(main())
