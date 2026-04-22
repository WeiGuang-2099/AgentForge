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
        return "Search the internet for up-to-date information. Enter a search query and return relevant web results."
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query",
                required=True,
            ),
            ToolParameter(
                name="num_results",
                type="integer",
                description="Number of results to return",
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
                error="Search query cannot be empty",
            )
        
        # 优先使用 Serper API
        if settings.SERPER_API_KEY:
            return await self._search_serper(query, num_results)
        else:
            # 降级到 DuckDuckGo
            logger.info("SERPER_API_KEY not configured, using DuckDuckGo search")
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
                title = item.get("title", "No title")
                snippet = item.get("snippet", "No snippet")
                link = item.get("link", "")
                results.append(f"{i}. {title}\n   Snippet: {snippet}\n   Link: {link}")
            
            if not results:
                return ToolResult(
                    success=True,
                    output=f"No results found for '{query}'.",
                    metadata={"source": "serper", "query": query},
                )
            
            output = f"Results for '{query}':\n\n" + "\n\n".join(results)
            return ToolResult(
                success=True,
                output=output,
                metadata={"source": "serper", "query": query, "count": len(results)},
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Serper API request failed: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Serper API request failed: HTTP {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"Serper search error: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Search error: {str(e)}",
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
                results.append(f"1. {data.get('Heading', 'Abstract')}\n   Snippet: {abstract}\n   Link: {abstract_url}")
            
            # 相关主题
            related_topics = data.get("RelatedTopics", [])
            for i, topic in enumerate(related_topics[:num_results - len(results)], len(results) + 1):
                if isinstance(topic, dict) and "Text" in topic:
                    text = topic.get("Text", "")
                    url = topic.get("FirstURL", "")
                    if text:
                        results.append(f"{i}. {text[:100]}...\n   Link: {url}")
            
            # 定义结果
            definition = data.get("Definition")
            if definition and len(results) < num_results:
                results.append(f"{len(results) + 1}. Definition: {definition}")
            
            if not results:
                # DuckDuckGo Instant Answer API 可能没有直接结果
                return ToolResult(
                    success=True,
                    output=f"No instant answers found for '{query}'. DuckDuckGo Instant Answer API mainly returns abstract info. Try a more specific query.",
                    metadata={"source": "duckduckgo", "query": query},
                )
            
            output = f"Results for '{query}' (DuckDuckGo):\n\n" + "\n\n".join(results)
            return ToolResult(
                success=True,
                output=output,
                metadata={"source": "duckduckgo", "query": query, "count": len(results)},
            )
            
        except httpx.HTTPStatusError as e:
            logger.error(f"DuckDuckGo API request failed: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"DuckDuckGo API request failed: HTTP {e.response.status_code}",
            )
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Search error: {str(e)}",
            )


class WebScrapeTool(BaseTool):
    """网页内容抓取工具 - 提取网页主要文本内容"""
    
    @property
    def name(self) -> str:
        return "scrape_web"
    
    @property
    def description(self) -> str:
        return "Scrape the main text content from a specified web page. Enter a URL and return the page's primary content."
    
    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="string",
                description="URL of the web page to scrape",
                required=True,
            ),
            ToolParameter(
                name="max_length",
                type="integer",
                description="Maximum characters to return",
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
                error="URL cannot be empty",
            )
        
        # 验证 URL 格式
        if not url.startswith(("http://", "https://")):
            return ToolResult(
                success=False,
                output="",
                error="URL must start with http:// or https://",
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
                    error=f"Unsupported content type: {content_type}. Only HTML pages are supported",
                )
            
            # 解析 HTML
            html = response.text
            text = self._extract_text(html)
            
            # 截断到 max_length
            if len(text) > max_length:
                text = text[:max_length] + "...\n\n[Content truncated]"
            
            return ToolResult(
                success=True,
                output=f"Web page content ({url}):\n\n{text}",
                metadata={"url": url, "length": len(text)},
            )
            
        except httpx.TimeoutException:
            logger.error(f"Scrape timed out: {url}")
            return ToolResult(
                success=False,
                output="",
                error="Request timed out, page took too long to respond",
            )
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            error_msg = {
                403: "Access denied (403 Forbidden), website may block crawlers",
                404: "Page not found (404 Not Found)",
                500: "Internal server error (500)",
                502: "Bad gateway (502)",
                503: "Service unavailable (503)",
            }.get(status, f"HTTP error: {status}")
            
            logger.error(f"Scrape failed: {url}, HTTP {status}")
            return ToolResult(
                success=False,
                output="",
                error=error_msg,
            )
        except Exception as e:
            logger.error(f"Scrape error: {url}, {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Scrape failed: {str(e)}",
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
