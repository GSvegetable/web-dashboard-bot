# agent_tools.py
# 定义可供 AI 智能体调用的工具列表
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

# ==========================================
# 1. 网页内容抓取工具 (用于阅读具体网址)
# ==========================================
def read_webpage(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else "无标题"
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        if not text:
            return {"status": "error", "content": "当前页面似乎没有可提取的正文内容。"}
        if len(text) > 3000:
            text = text[:3000] + "..."
        return {"status": "success", "title": title, "content": text}
    except Exception as e:
        return {"status": "error", "content": f"读取网页失败: {str(e)}"}

# ==========================================
# 2. 真正的联网搜索工具 (配合面板开关启用)
# ==========================================
def web_search(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return {"status": "error", "content": "没找到相关搜索结果。"}
            
            summary = f"关于【{query}】的搜索结果：\n"
            for i, res in enumerate(results, 1):
                summary += f"\n{i}. 标题：{res['title']}\n   链接：{res['href']}\n   简介：{res['body']}\n"
            return {"status": "success", "content": summary}
    except Exception as e:
        return {"status": "error", "content": f"联网搜索失败: {str(e)}"}

# ==========================================
# 3. 工具列表清单
# ==========================================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bind_bot",
            "description": "绑定一个 Telegram 机器人到当前工作台。请务必询问用户的 Token 和 Telegram ID。",
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "机器人的 Bot Token"},
                    "telegram_id": {"type": "string", "description": "用户的 Telegram ID (纯数字格式)"},
                    "name": {"type": "string", "description": "机器人的显示名称，默认为宫水编辑器"}
                },
                "required": ["token", "telegram_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_bot_node",
            "description": "在工作台的画布上凭空添加一个机器人节点卡片。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "节点的显示名称"},
                    "avatar": {"type": "string", "description": "机器人的头像 URL (可选)"}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "通过 URL 读取并提取一个网页的标题和正文内容。",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "需要读取的目标网页完整 URL"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "当用户要求搜索最新资讯、时事、或不确定的百科内容时，使用此工具进行智能联网搜索。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "用户的搜索关键词或问题"}
                },
                "required": ["query"]
            }
        }
    }
]
