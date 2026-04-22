"""文件操作工具 - 安全的文件读写操作"""
import os
import logging
from typing import Optional

from app.tools.base import BaseTool, ToolParameter, ToolResult
from app.config import settings

logger = logging.getLogger(__name__)

# 上传目录的绝对路径（从 tools/ 目录相对计算到 data/uploads/）
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "uploads")


def _safe_path(file_path: str) -> str:
    """
    验证并返回安全的绝对路径，防止目录穿越攻击。
    
    Args:
        file_path: 相对于 uploads 目录的文件路径
        
    Returns:
        安全的绝对路径
        
    Raises:
        ValueError: 路径不安全，试图访问 uploads 目录外的文件
    """
    # 规范化 UPLOAD_DIR
    base = os.path.realpath(UPLOAD_DIR)
    # 构建完整路径并规范化
    full_path = os.path.realpath(os.path.join(base, file_path))
    # 确保路径在 UPLOAD_DIR 内
    if not full_path.startswith(base):
        raise ValueError(f"Unsafe path: {file_path}. Access to files outside the uploads directory is not allowed")
    return full_path


class ReadFileTool(BaseTool):
    """读取文件内容工具"""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read the content of a specified file. File paths are restricted to the project's data/uploads/ directory."
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="File path (relative to data/uploads/ directory)",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding",
                required=False,
                default="utf-8"
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """
        读取文件内容。

        Args:
            file_path: 相对于 data/uploads/ 目录的文件路径
            encoding: 文件编码（默认 utf-8）

        Returns:
            ToolResult: 包含文件内容或错误信息
        """
        # 1. 检查功能开关
        if not settings.ENABLE_FILE_OPS:
            return ToolResult(
                success=False,
                output="",
                error="File operations are disabled (ENABLE_FILE_OPS=False)"
            )
        
        file_path = kwargs.get("file_path")
        encoding = kwargs.get("encoding", "utf-8")
        
        if not file_path:
            return ToolResult(
                success=False,
                output="",
                error="Missing required parameter: file_path"
            )

        try:
            # 2. 路径安全验证
            safe_full_path = _safe_path(file_path)

            # 3. 检查文件是否存在
            if not os.path.exists(safe_full_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}"
                )

            if not os.path.isfile(safe_full_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Path is not a file: {file_path}"
                )
            
            # 4. 读取文件内容
            with open(safe_full_path, "r", encoding=encoding) as f:
                content = f.read()
            
            # 5. 大文件截断（10000 字符）
            max_chars = 10000
            truncated = False
            if len(content) > max_chars:
                content = content[:max_chars]
                truncated = True
            
            # 获取文件大小
            file_size = os.path.getsize(safe_full_path)
            
            logger.info(f"读取文件成功: {file_path}, 大小: {file_size} bytes")
            
            return ToolResult(
                success=True,
                output=content,
                metadata={
                    "file_path": file_path,
                    "full_path": safe_full_path,
                    "file_size": file_size,
                    "truncated": truncated,
                    "encoding": encoding
                }
            )
            
        except ValueError as e:
            # 路径安全验证失败
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )
        except UnicodeDecodeError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"File encoding error, try a different encoding: {e}"
            )
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to read file: {e}"
            )


class WriteFileTool(BaseTool):
    """写入文件内容工具"""
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "Write content to a specified file. File paths are restricted to the project's data/uploads/ directory."
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="File path (relative to data/uploads/ directory)",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Content to write",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="File encoding",
                required=False,
                default="utf-8"
            ),
            ToolParameter(
                name="mode",
                type="string",
                description="Write mode (w=overwrite, a=append)",
                required=False,
                default="w",
                enum=["w", "a"]
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """
        写入文件内容。

        Args:
            file_path: 相对于 data/uploads/ 目录的文件路径
            content: 要写入的内容
            encoding: 文件编码（默认 utf-8）
            mode: 写入模式（w=覆盖, a=追加）

        Returns:
            ToolResult: 包含成功信息或错误信息
        """
        # 1. 检查功能开关
        if not settings.ENABLE_FILE_OPS:
            return ToolResult(
                success=False,
                output="",
                error="File operations are disabled (ENABLE_FILE_OPS=False)"
            )
        
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        encoding = kwargs.get("encoding", "utf-8")
        mode = kwargs.get("mode", "w")
        
        if not file_path:
            return ToolResult(
                success=False,
                output="",
                error="Missing required parameter: file_path"
            )

        if content is None:
            return ToolResult(
                success=False,
                output="",
                error="Missing required parameter: content"
            )

        # 验证写入模式
        if mode not in ("w", "a"):
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid write mode: {mode}. Only 'w' (overwrite) or 'a' (append) are supported"
            )
        
        try:
            # 2. 路径安全验证
            safe_full_path = _safe_path(file_path)
            
            # 3. 自动创建父目录
            parent_dir = os.path.dirname(safe_full_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                logger.info(f"创建目录: {parent_dir}")
            
            # 4. 写入文件
            with open(safe_full_path, mode, encoding=encoding) as f:
                f.write(content)
            
            # 5. 获取写入后的文件大小
            file_size = os.path.getsize(safe_full_path)
            
            mode_desc = "Overwrite" if mode == "w" else "Append"
            logger.info(f"写入文件成功: {file_path}, 模式: {mode_desc}, 大小: {file_size} bytes")
            
            return ToolResult(
                success=True,
                output=f"File {mode_desc} succeeded: {file_path}, size: {file_size} bytes",
                metadata={
                    "file_path": file_path,
                    "full_path": safe_full_path,
                    "file_size": file_size,
                    "mode": mode,
                    "encoding": encoding,
                    "content_length": len(content)
                }
            )
            
        except ValueError as e:
            # 路径安全验证失败
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )
        except Exception as e:
            logger.error(f"写入文件失败: {file_path}, 错误: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to write file: {e}"
            )
