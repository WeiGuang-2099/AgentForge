"""Tests for tool modules (data, file, code)."""
import pytest
from unittest.mock import patch, MagicMock

from app.tools.data import CalculatorTool, DataAnalyzerTool, safe_eval
from app.tools.file import _safe_path, ReadFileTool


# --- CalculatorTool tests ---

async def test_calculator_basic_math():
    """CalculatorTool handles '2+3*4' correctly."""
    tool = CalculatorTool()
    result = await tool.execute(expression="2+3*4")
    assert result.success is True
    assert result.output == "14"


async def test_calculator_functions():
    """CalculatorTool handles 'sqrt(16)' correctly."""
    tool = CalculatorTool()
    result = await tool.execute(expression="sqrt(16)")
    assert result.success is True
    assert float(result.output) == 4.0


async def test_calculator_rejects_dangerous():
    """CalculatorTool rejects 'import os' expressions."""
    tool = CalculatorTool()
    result = await tool.execute(expression="import os")
    assert result.success is False
    assert "Not allowed" in result.error


async def test_calculator_rejects_exec():
    """CalculatorTool rejects expressions with 'exec', '__'."""
    tool = CalculatorTool()

    result = await tool.execute(expression="exec('print(1)')")
    assert result.success is False
    assert "Not allowed" in result.error

    result2 = await tool.execute(expression="__import__('os')")
    assert result2.success is False
    assert "Not allowed" in result2.error


# --- File path safety tests ---

def test_file_safe_path_valid():
    """_safe_path accepts valid relative paths."""
    # A simple relative filename should not raise
    result = _safe_path("test.txt")
    assert "test.txt" in result


def test_file_safe_path_traversal():
    """_safe_path rejects '../../../etc/passwd'."""
    with pytest.raises(ValueError, match="Unsafe path"):
        _safe_path("../../../etc/passwd")


# --- ReadFileTool tests ---

async def test_read_file_not_found():
    """ReadFileTool returns error for nonexistent file."""
    tool = ReadFileTool()
    with patch("app.tools.file.settings") as mock_settings:
        mock_settings.ENABLE_FILE_OPS = True
        result = await tool.execute(file_path="nonexistent_file_12345.txt")
    assert result.success is False
    assert "not found" in result.error.lower() or "File not found" in result.error


# --- DataAnalyzerTool tests ---

async def test_data_analyzer_missing_file():
    """DataAnalyzerTool returns error for missing CSV."""
    tool = DataAnalyzerTool()
    result = await tool.execute(file_path="nonexistent_data.csv", operation="describe")
    assert result.success is False
    assert "not found" in result.error.lower() or "File not found" in result.error
