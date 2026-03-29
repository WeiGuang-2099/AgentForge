"""允许通过 python -m app.cli 或 python -m app 运行 CLI"""
import sys

# 为 Windows 终端设置 UTF-8 编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.cli import main
import asyncio

asyncio.run(main())
