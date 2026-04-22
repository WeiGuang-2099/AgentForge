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
            raise ValueError(f"Not allowed: '{d}'")
    
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
        return "Safe math calculator. Supports basic arithmetic, trigonometry, logarithms, etc. Examples: '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)'"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="expression",
                type="string",
                description="Math expression (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)', 'log(100)')",
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
                error="Missing required parameter: expression"
            )
        
        try:
            result = safe_eval(expression)
            
            logger.info(f"Calculation successful: {expression} = {result}")
            
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
                error=f"Expression syntax error: {e}"
            )
        except (ZeroDivisionError, OverflowError, ArithmeticError) as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Calculation error: {e}"
            )
        except Exception as e:
            logger.error(f"Calculation failed: {expression}, error: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Calculation failed: {e}"
            )


class DataAnalyzerTool(BaseTool):
    """CSV 数据分析工具"""
    
    @property
    def name(self) -> str:
        return "data_analyzer"
    
    @property
    def description(self) -> str:
        return "Analyze CSV data files. Supports statistical summaries, groupby aggregation, data filtering, and more."
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                type="string",
                description="CSV file path (relative to data/uploads/)",
                required=True
            ),
            ToolParameter(
                name="operation",
                type="string",
                description="Operation type",
                required=True,
                enum=["describe", "head", "groupby", "filter", "columns"]
            ),
            ToolParameter(
                name="params",
                type="string",
                description="Operation parameters (JSON string). Different operations require different params. head: {\"n\": 10}; groupby: {\"by\": \"column_name\", \"agg\": \"mean\"}; filter: {\"column\": \"name\", \"op\": \"==\", \"value\": \"xxx\"}",
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
                error="Missing required parameter: file_path"
            )
        
        if not operation:
            return ToolResult(
                success=False,
                output="",
                error="Missing required parameter: operation"
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
                    error=f"params is not valid JSON: {e}"
                )
        
        try:
            # 路径安全验证
            safe_full_path = _safe_path(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(safe_full_path):
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {file_path}"
                )
            
            # 读取 CSV
            df = pd.read_csv(safe_full_path)
            
            # 执行操作
            if operation == "columns":
                result = f"Columns: {list(df.columns)}\nRows: {len(df)}\nData types:\n{df.dtypes.to_string()}"
            
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
                        error="groupby operation requires 'by' parameter for column"
                    )
                
                if by not in df.columns:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Column '{by}' does not exist. Available columns: {list(df.columns)}"
                    )
                
                # 仅对数值列进行聚合
                numeric_df = df.select_dtypes(include=['number'])
                if numeric_df.empty:
                    return ToolResult(
                        success=False,
                        output="",
                        error="No numeric columns available for aggregation"
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
                        error="filter operation requires 'column' parameter"
                    )
                
                if value is None:
                    return ToolResult(
                        success=False,
                        output="",
                        error="filter operation requires 'value' parameter"
                    )
                
                if column not in df.columns:
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Column '{column}' does not exist. Available columns: {list(df.columns)}"
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
                        error=f"Unsupported operator: {op}。Supported: ==, !=, >, >=, <, <=, contains"
                    )
                
                result = f"Filtered results ({len(filtered)} rows):\n{filtered.to_string()}"
            
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unsupported operation: {operation}"
                )
            
            logger.info(f"Data analysis successful: {file_path}, operation: {operation}")
            
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
                error="CSV file is empty"
            )
        except pd.errors.ParserError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"CSV parse error: {e}"
            )
        except Exception as e:
            logger.error(f"Data analysis failed: {file_path}, error: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Data analysis failed: {e}"
            )


class TranslatorTool(BaseTool):
    """文本翻译工具（基于 LLM）"""
    
    @property
    def name(self) -> str:
        return "translator"
    
    @property
    def description(self) -> str:
        return "Text translation tool. Performs multilingual translation via LLM."
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="text",
                type="string",
                description="Text to translate",
                required=True
            ),
            ToolParameter(
                name="target_language",
                type="string",
                description="Target language (e.g., 'English', 'Chinese', 'Japanese', 'Spanish')",
                required=True
            ),
            ToolParameter(
                name="source_language",
                type="string",
                description="Source language (auto-detected if not specified)",
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
                error="Missing required parameter: text"
            )
        
        if not target_language:
            return ToolResult(
                success=False,
                output="",
                error="Missing required parameter: target_language"
            )
        
        try:
            # 构建翻译 prompt
            if source_language:
                prompt = f"Translate the following {source_language} text into {target_language}. Output only the translation, without any explanation:\n\n{text}"
            else:
                prompt = f"Translate the following text into {target_language}. Output only the translation, without any explanation:\n\n{text}"
            
            # 调用 LLM
            llm_client = LLMClient()
            response = await llm_client.acomplete([
                {"role": "system", "content": "You are a professional translation assistant. Please accurately translate the text provided by the user, maintaining the original tone and style. Output only the translation."},
                {"role": "user", "content": prompt}
            ])
            
            translated_text = response.content.strip()
            
            logger.info(f"Translation successful: {len(text)} chars -> {target_language}")
            
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
            logger.error(f"Translation failed: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Translation failed: {e}"
            )
