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
        raise ValueError(f"路径不安全: {file_path}，不允许访问 uploads 目录外的文件")
    return full_path


class ReadFileTool(BaseTool):
    """读取文件内容工具"""
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "读取指定文件的内容。文件路径限制在项目 data/uploads/ 目录内。"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="文件路径（相对于 data/uploads/ 目录）",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="文件编码",
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
                error="文件操作功能已禁用（ENABLE_FILE_OPS=False）"
            )
        
        file_path = kwargs.get("file_path")
        encoding = kwargs.get("encoding", "utf-8")
        
        if not file_path:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: file_path"
            )
        
        try:
            # 2. 路径安全验证
            safe_full_path = _safe_path(file_path)
            
            # 3. 检查文件是否存在
            if not os.path.exists(safe_full_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"文件不存在: {file_path}"
                )
            
            if not os.path.isfile(safe_full_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"路径不是文件: {file_path}"
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
                error=f"文件编码错误，请尝试其他编码: {e}"
            )
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"读取文件失败: {e}"
            )


class WriteFileTool(BaseTool):
    """写入文件内容工具"""
    
    @property
    def name(self) -> str:
        return "write_file"
    
    @property
    def description(self) -> str:
        return "将内容写入指定文件。文件路径限制在项目 data/uploads/ 目录内。"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="文件路径（相对于 data/uploads/ 目录）",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="要写入的内容",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="文件编码",
                required=False,
                default="utf-8"
            ),
            ToolParameter(
                name="mode",
                type="string",
                description="写入模式（w=覆盖, a=追加）",
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
                error="文件操作功能已禁用（ENABLE_FILE_OPS=False）"
            )
        
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        encoding = kwargs.get("encoding", "utf-8")
        mode = kwargs.get("mode", "w")
        
        if not file_path:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: file_path"
            )
        
        if content is None:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: content"
            )
        
        # 验证写入模式
        if mode not in ("w", "a"):
            return ToolResult(
                success=False,
                output="",
                error=f"无效的写入模式: {mode}，仅支持 'w'（覆盖）或 'a'（追加）"
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
            
            mode_desc = "覆盖写入" if mode == "w" else "追加写入"
            logger.info(f"写入文件成功: {file_path}, 模式: {mode_desc}, 大小: {file_size} bytes")
            
            return ToolResult(
                success=True,
                output=f"文件{mode_desc}成功: {file_path}，大小: {file_size} bytes",
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
                error=f"写入文件失败: {e}"
            )
