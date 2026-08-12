# agent_tools.py
# 定义可供 AI 智能体调用的工具列表
import requests
from bs4 import BeautifulSoup

# ---- 读网页的实际功能函数 ----
def read_webpage(url):
    try:
        # 伪装成浏览器访问，防止被网站拦截
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title = soup.title.string.strip() if soup.title else "无标题"
        
        # 提取所有段落文字
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        if not text:
            return {"status": "error", "content": "当前页面似乎没有可提取的正文内容。"}
        
        # 控制提取长度，避免 Token 飙高 (截取前 3000 字)
        if len(text) > 3000:
            text = text[:3000] + "..."
            
        return {"status": "success", "title": title, "content": text}
    except Exception as e:
        return {"status": "error", "content": f"读取网页失败: {str(e)}"}

# ---- 工具清单（供 AI 识别） ----
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
    # ✨ 新增：读网页工具
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
    }
]
