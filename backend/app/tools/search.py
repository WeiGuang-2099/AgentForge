"""搜索工具实现 - 网络搜索和网页抓取"""
import httpx
import logging
from typing import Optional
from bs4 import BeautifulSoup

from app.tools.base import BaseTool, ToolParameter, ToolResult
from app.config import settings

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """网络搜索工具 - 支持 Serper API 和 DuckDuckGo"""
    
    @property
    def name(self) -> str:
        return "web_search"
    
    @property
    def description(self) -> str:
        return "搜索互联网获取最新信息。输入搜索关键词，返回相关网页结果。"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="搜索关键词",
                required=True,
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="返回结果数量",
                required=False,
                default=5,
            ),
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行网络搜索"""
        query = kwargs.get("query")
        num_results = kwargs.get("num_results", 5)
        
        if not query:
            return ToolResult(
                success=False,
                output="",
                error="搜索关键词不能为空",
            )
        
        # 优先使用 Serper API
        if settings.SERPER_API_KEY:
            return await self._search_serper(query, num_results)
        else:
            # 降级到 DuckDuckGo
            logger.info("SERPER_API_KEY 未配置，使用 DuckDuckGo 搜索")
            return await self._search_duckduckgo(query, num_results)
    
    async def _search_serper(self, query: str, num_results: int) -> ToolResult:
        """使用 Serper API 搜索"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    json={"q": query, "num": num_results},
                    headers={"X-API-KEY": settings.SERPER_API_KEY},
                )
                response.raise_for_status()
                data = response.json()
            
            # 格式化搜索结果
            results = []
            organic = data.get("organic", [])
            
            for i, item in enumerate(organic[:num_results], 1):
                title = item.get("title", "无标题")
                snippet = item.get("snippet", "无摘要")
                link = item.get("link", "")
                results.append(f"{i}. {title}\n   摘要: {snippet}\n   链接: {link}")
            
            if not results:
                return ToolResult(
                    success=True,
                    output=f"搜索 '{query}' 未找到相关结果。",
                    metadata={"source": "serper", "query": query},
                )
            
            output = f"搜索 '{query}' 的结果:\n\n" + "\n\n".join(results)
            return ToolResult(
                success=True,
                output=output,
                metadata={"source": "serper", "query": query, "count": len(results)},
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Serper API 请求失败: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Serper API 请求失败: HTTP {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"Serper 搜索出错: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"搜索出错: {str(e)}",
            )
    
    async def _search_duckduckgo(self, query: str, num_results: int) -> ToolResult:
        """使用 DuckDuckGo 搜索（免费备选方案）"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1},
                    headers={"User-Agent": "AgentForge/1.0"},
                )
                response.raise_for_status()
                data = response.json()
            
            results = []
            
            # DuckDuckGo Instant Answer API 返回格式
            # 抽象摘要
            abstract = data.get("Abstract")
            abstract_url = data.get("AbstractURL")
            if abstract:
                results.append(f"1. {data.get('Heading', '摘要')}\n   摘要: {abstract}\n   链接: {abstract_url}")
            
            # 相关主题
            related_topics = data.get("RelatedTopics", [])
            for i, topic in enumerate(related_topics[:num_results - len(results)], len(results) + 1):
                if isinstance(topic, dict) and "Text" in topic:
                    text = topic.get("Text", "")
                    url = topic.get("FirstURL", "")
                    if text:
                        results.append(f"{i}. {text[:100]}...\n   链接: {url}")
            
            # 定义结果
            definition = data.get("Definition")
            if definition and len(results) < num_results:
                results.append(f"{len(results) + 1}. 定义: {definition}")
            
            if not results:
                # DuckDuckGo Instant Answer API 可能没有直接结果
                return ToolResult(
                    success=True,
                    output=f"搜索 '{query}' 未找到即时答案。DuckDuckGo Instant Answer API 主要返回摘要信息，可能需要更具体的查询。",
                    metadata={"source": "duckduckgo", "query": query},
                )
            
            output = f"搜索 '{query}' 的结果 (DuckDuckGo):\n\n" + "\n\n".join(results)
            return ToolResult(
                success=True,
                output=output,
                metadata={"source": "duckduckgo", "query": query, "count": len(results)},
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"DuckDuckGo API 请求失败: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"DuckDuckGo API 请求失败: HTTP {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"DuckDuckGo 搜索出错: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"搜索出错: {str(e)}",
            )


class WebScrapeTool(BaseTool):
    """网页内容抓取工具 - 提取网页主要文本内容"""
    
    @property
    def name(self) -> str:
        return "scrape_web"
    
    @property
    def description(self) -> str:
        return "抓取指定网页的主要文本内容。输入URL，返回页面主要内容。"
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="string",
                description="要抓取的网页URL",
                required=True,
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="最大返回字符数",
                required=False,
                default=5000,
            ),
        ]
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行网页抓取"""
        url = kwargs.get("url")
        max_length = kwargs.get("max_length", 5000)
        
        if not url:
            return ToolResult(
                success=False,
                output="",
                error="URL 不能为空",
            )
        
        # 验证 URL 格式
        if not url.startswith(("http://", "https://")):
            return ToolResult(
                success=False,
                output="",
                error="URL 必须以 http:// 或 https:// 开头",
            )
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    },
                )
                response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"不支持的内容类型: {content_type}，仅支持 HTML 页面",
                )
            
            # 解析 HTML
            html = response.text
            text = self._extract_text(html)
            
            # 截断到 max_length
            if len(text) > max_length:
                text = text[:max_length] + "...\n\n[内容已截断]"
            
            return ToolResult(
                success=True,
                output=f"网页内容 ({url}):\n\n{text}",
                metadata={"url": url, "length": len(text)},
            )
            
        except httpx.TimeoutException:
            logger.error(f"抓取超时: {url}")
            return ToolResult(
                success=False,
                output="",
                error="请求超时，网页响应时间过长",
            )
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            error_msg = {
                403: "访问被拒绝 (403 Forbidden)，网站可能禁止爬虫访问",
                404: "页面不存在 (404 Not Found)",
                500: "服务器内部错误 (500)",
                502: "网关错误 (502)",
                503: "服务不可用 (503)",
            }.get(status, f"HTTP 错误: {status}")
            
            logger.error(f"抓取失败: {url}, HTTP {status}")
            return ToolResult(
                success=False,
                output="",
                error=error_msg,
            )
        except Exception as e:
            logger.error(f"抓取出错: {url}, {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"抓取失败: {str(e)}",
            )
    
    def _extract_text(self, html: str) -> str:
        """从 HTML 中提取主要文本内容"""
        soup = BeautifulSoup(html, "html.parser")
        
        # 移除脚本、样式、导航等非内容元素
        for element in soup(["script", "style", "nav", "header", "footer", 
                             "aside", "noscript", "iframe", "form", "button",
                             "input", "select", "textarea", "meta", "link"]):
            element.decompose()
        
        # 移除隐藏元素
        for element in soup.find_all(style=lambda x: x and "display:none" in x.replace(" ", "")):
            element.decompose()
        for element in soup.find_all(style=lambda x: x and "visibility:hidden" in x.replace(" ", "")):
            element.decompose()
        
        # 尝试找到主要内容区域
        main_content = None
        for selector in ["main", "article", '[role="main"]', "#content", ".content", "#main", ".main"]:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # 如果找到主要内容区域，使用它；否则使用 body
        if main_content:
            text = main_content.get_text(separator="\n", strip=True)
        else:
            body = soup.find("body")
            text = body.get_text(separator="\n", strip=True) if body else soup.get_text(separator="\n", strip=True)
        
        # 清理文本
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # 跳过太短的行（通常是菜单项等）
            if line and len(line) > 2:
                cleaned_lines.append(line)
        
        # 合并连续空行
        result = []
        prev_empty = False
        for line in cleaned_lines:
            if not line:
                if not prev_empty:
                    result.append("")
                prev_empty = True
            else:
                result.append(line)
                prev_empty = False
        
        return "\n".join(result)
