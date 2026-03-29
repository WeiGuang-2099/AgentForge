"""Code execution tool - 代码执行沙箱"""
import asyncio
import os
import tempfile

from app.tools.base import BaseTool, ToolParameter, ToolResult


class PythonReplTool(BaseTool):
    """
    Python 代码执行工具 - 在安全沙箱中执行 Python 代码。
    
    特性:
    - 使用子进程隔离执行
    - 30 秒超时限制
    - 最小化环境变量
    - 自动清理临时文件
    """
    
    @property
    def name(self) -> str:
        return "python_repl"
    
    @property
    def description(self) -> str:
        return "执行 Python 代码并返回输出结果。可用于数据处理、数学计算、文件操作等。代码会在安全的沙箱环境中运行。"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="要执行的 Python 代码",
                required=True,
            ),
        ]
    
    async def execute(self, code: str = "", **kwargs) -> ToolResult:
        """
        执行 Python 代码。
        
        Args:
            code: 要执行的 Python 代码
            
        Returns:
            ToolResult: 执行结果
        """
        from app.config import settings
        
        # 检查功能开关
        if not settings.ENABLE_CODE_EXECUTION:
            return ToolResult(success=False, output="", error="代码执行功能已禁用")
        
        # 验证代码参数
        if not code or not code.strip():
            return ToolResult(success=False, output="", error="代码不能为空")
        
        # 创建临时文件
        tmp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                tmp_file = f.name
            
            # 在子进程中执行，使用最小化环境变量
            process = await asyncio.create_subprocess_exec(
                "python", tmp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "PYTHONPATH": "",
                    "PYTHONIOENCODING": "utf-8",
                    # Windows 需要的环境变量
                    "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                    "TEMP": os.environ.get("TEMP", ""),
                    "TMP": os.environ.get("TMP", ""),
                },
            )
            
            try:
                # 30 秒超时限制
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=30
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    success=False, output="", error="代码执行超时（30秒限制）"
                )
            
            # 解码输出
            stdout_str = stdout.decode("utf-8", errors="replace").strip()
            stderr_str = stderr.decode("utf-8", errors="replace").strip()
            
            if process.returncode == 0:
                # 执行成功
                output = stdout_str
                if stderr_str:
                    output += f"\n[stderr]: {stderr_str}"
                return ToolResult(success=True, output=output or "(无输出)")
            else:
                # 执行失败
                return ToolResult(
                    success=False,
                    output=stdout_str,
                    error=stderr_str or f"进程退出码: {process.returncode}",
                )
                
        except Exception as e:
            return ToolResult(success=False, output="", error=f"执行异常: {str(e)}")
        finally:
            # 清理临时文件
            if tmp_file and os.path.exists(tmp_file):
                try:
                    os.unlink(tmp_file)
                except OSError:
                    pass  # 忽略清理失败
