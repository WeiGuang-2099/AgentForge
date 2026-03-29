"""数据分析工具 - 计算器、数据分析、翻译"""
import os
import math
import json
import logging
from typing import Optional

import pandas as pd

from app.tools.base import BaseTool, ToolParameter, ToolResult
from app.tools.file import _safe_path
from app.core.llm import LLMClient

logger = logging.getLogger(__name__)


# 安全数学计算的白名单函数和常量
SAFE_NAMES = {
    # 内置函数
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    "int": int,
    "float": float,
    # 数学常量
    "pi": math.pi,
    "e": math.e,
    # 三角函数
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    # 对数函数
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    # 其他数学函数
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
    "exp": math.exp,
    "factorial": math.factorial,
    "degrees": math.degrees,
    "radians": math.radians,
}


def safe_eval(expression: str) -> float:
    """
    安全地计算数学表达式。
    
    Args:
        expression: 数学表达式字符串
        
    Returns:
        计算结果
        
    Raises:
        ValueError: 表达式包含危险关键词
    """
    # 检查是否包含危险关键词
    dangerous = ["import", "exec", "eval", "__", "open", "os", "sys", "subprocess", "compile"]
    expression_lower = expression.lower()
    for d in dangerous:
        if d in expression_lower:
            raise ValueError(f"不允许使用 '{d}'")
    
    # 使用 compile + eval 并限制命名空间
    code = compile(expression, "<calculator>", "eval")
    return eval(code, {"__builtins__": {}}, SAFE_NAMES)


class CalculatorTool(BaseTool):
    """安全的数学计算工具"""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "安全的数学计算工具。支持基础算术、三角函数、对数等。例如: '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)'"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type="string",
                description="数学表达式（如 '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)', 'log(100)'）",
                required=True
            ),
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行数学计算。
        
        Args:
            expression: 数学表达式
            
        Returns:
            ToolResult: 包含计算结果或错误信息
        """
        expression = kwargs.get("expression")
        
        if not expression:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: expression"
            )
        
        try:
            result = safe_eval(expression)
            
            logger.info(f"计算成功: {expression} = {result}")
            
            return ToolResult(
                success=True,
                output=str(result),
                metadata={
                    "expression": expression,
                    "result": result,
                    "result_type": type(result).__name__
                }
            )
            
        except ValueError as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )
        except SyntaxError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"表达式语法错误: {e}"
            )
        except (ZeroDivisionError, OverflowError, ArithmeticError) as e:
            return ToolResult(
                success=False,
                output="",
                error=f"计算错误: {e}"
            )
        except Exception as e:
            logger.error(f"计算失败: {expression}, 错误: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"计算失败: {e}"
            )


class DataAnalyzerTool(BaseTool):
    """CSV 数据分析工具"""
    
    @property
    def name(self) -> str:
        return "data_analyzer"
    
    @property
    def description(self) -> str:
        return "分析 CSV 数据文件。支持统计描述、分组聚合、数据筛选等。"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="CSV 文件路径（相对于 data/uploads/）",
                required=True
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="操作类型",
                required=True,
                enum=["describe", "head", "groupby", "filter", "columns"]
            ),
            ToolParameter(
                name="params",
                type="string",
                description="操作参数（JSON 字符串），不同操作需要不同参数。head: {\"n\": 10}; groupby: {\"by\": \"column_name\", \"agg\": \"mean\"}; filter: {\"column\": \"name\", \"op\": \"==\", \"value\": \"xxx\"}",
                required=False
            ),
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        分析 CSV 数据。
        
        Args:
            file_path: CSV 文件路径
            operation: 操作类型
            params: 操作参数（JSON 字符串）
            
        Returns:
            ToolResult: 包含分析结果或错误信息
        """
        file_path = kwargs.get("file_path")
        operation = kwargs.get("operation")
        params_str = kwargs.get("params")
        
        if not file_path:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: file_path"
            )
        
        if not operation:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: operation"
            )
        
        # 解析参数
        params = {}
        if params_str:
            try:
                params = json.loads(params_str)
            except json.JSONDecodeError as e:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"params 参数不是有效的 JSON: {e}"
                )
        
        try:
            # 路径安全验证
            safe_full_path = _safe_path(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(safe_full_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"文件不存在: {file_path}"
                )
            
            # 读取 CSV
            df = pd.read_csv(safe_full_path)
            
            # 执行操作
            if operation == "columns":
                result = f"列名: {list(df.columns)}\n行数: {len(df)}\n数据类型:\n{df.dtypes.to_string()}"
            
            elif operation == "describe":
                result = df.describe(include='all').to_string()
            
            elif operation == "head":
                n = params.get("n", 5)
                result = df.head(n).to_string()
            
            elif operation == "groupby":
                by = params.get("by")
                agg = params.get("agg", "mean")
                
                if not by:
                    return ToolResult(
                        success=False,
                        output="",
                        error="groupby 操作需要 'by' 参数指定分组列"
                    )
                
                if by not in df.columns:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"列 '{by}' 不存在。可用列: {list(df.columns)}"
                    )
                
                # 仅对数值列进行聚合
                numeric_df = df.select_dtypes(include=['number'])
                if numeric_df.empty:
                    return ToolResult(
                        success=False,
                        output="",
                        error="没有可用于聚合的数值列"
                    )
                
                grouped = df.groupby(by)[numeric_df.columns.tolist()].agg(agg)
                result = grouped.to_string()
            
            elif operation == "filter":
                column = params.get("column")
                op = params.get("op", "==")
                value = params.get("value")
                
                if not column:
                    return ToolResult(
                        success=False,
                        output="",
                        error="filter 操作需要 'column' 参数"
                    )
                
                if value is None:
                    return ToolResult(
                        success=False,
                        output="",
                        error="filter 操作需要 'value' 参数"
                    )
                
                if column not in df.columns:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"列 '{column}' 不存在。可用列: {list(df.columns)}"
                    )
                
                # 根据操作符筛选
                if op == "==":
                    filtered = df[df[column] == value]
                elif op == "!=":
                    filtered = df[df[column] != value]
                elif op == ">":
                    filtered = df[df[column] > value]
                elif op == ">=":
                    filtered = df[df[column] >= value]
                elif op == "<":
                    filtered = df[df[column] < value]
                elif op == "<=":
                    filtered = df[df[column] <= value]
                elif op == "contains":
                    filtered = df[df[column].astype(str).str.contains(str(value), na=False)]
                else:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"不支持的操作符: {op}。支持: ==, !=, >, >=, <, <=, contains"
                    )
                
                result = f"筛选结果 ({len(filtered)} 行):\n{filtered.to_string()}"
            
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"不支持的操作: {operation}"
                )
            
            logger.info(f"数据分析成功: {file_path}, 操作: {operation}")
            
            return ToolResult(
                success=True,
                output=result,
                metadata={
                    "file_path": file_path,
                    "operation": operation,
                    "params": params,
                    "rows": len(df),
                    "columns": list(df.columns)
                }
            )
            
        except ValueError as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e)
            )
        except pd.errors.EmptyDataError:
            return ToolResult(
                success=False,
                output="",
                error="CSV 文件为空"
            )
        except pd.errors.ParserError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"CSV 解析错误: {e}"
            )
        except Exception as e:
            logger.error(f"数据分析失败: {file_path}, 错误: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"数据分析失败: {e}"
            )


class TranslatorTool(BaseTool):
    """文本翻译工具（基于 LLM）"""
    
    @property
    def name(self) -> str:
        return "translator"
    
    @property
    def description(self) -> str:
        return "文本翻译工具。通过 LLM 进行多语言翻译。"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="text",
                type="string",
                description="要翻译的文本",
                required=True
            ),
            ToolParameter(
                name="target_language",
                type="string",
                description="目标语言（如 'English', '中文', '日本語', 'Español'）",
                required=True
            ),
            ToolParameter(
                name="source_language",
                type="string",
                description="源语言（不指定则自动检测）",
                required=False
            ),
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """
        翻译文本。
        
        Args:
            text: 要翻译的文本
            target_language: 目标语言
            source_language: 源语言（可选）
            
        Returns:
            ToolResult: 包含翻译结果或错误信息
        """
        text = kwargs.get("text")
        target_language = kwargs.get("target_language")
        source_language = kwargs.get("source_language")
        
        if not text:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: text"
            )
        
        if not target_language:
            return ToolResult(
                success=False,
                output="",
                error="缺少必需参数: target_language"
            )
        
        try:
            # 构建翻译 prompt
            if source_language:
                prompt = f"将以下{source_language}文本翻译成{target_language}，只输出翻译结果，不要添加任何解释：\n\n{text}"
            else:
                prompt = f"将以下文本翻译成{target_language}，只输出翻译结果，不要添加任何解释：\n\n{text}"
            
            # 调用 LLM
            llm_client = LLMClient()
            response = await llm_client.acomplete([
                {"role": "system", "content": "你是一个专业的翻译助手。请准确翻译用户提供的文本，保持原文的语气和风格。只输出翻译结果。"},
                {"role": "user", "content": prompt}
            ])
            
            translated_text = response.content.strip()
            
            logger.info(f"翻译成功: {len(text)} 字符 -> {target_language}")
            
            return ToolResult(
                success=True,
                output=translated_text,
                metadata={
                    "source_language": source_language or "auto-detect",
                    "target_language": target_language,
                    "source_length": len(text),
                    "translated_length": len(translated_text),
                    "model": response.model,
                    "usage": response.usage
                }
            )
            
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"翻译失败: {e}"
            )
