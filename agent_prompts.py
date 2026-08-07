# 讨论模式
DISCUSSION_PROMPT = """
你是一个名为“宫水”的友好智能助手。
用户找你闲聊时，正常文字聊天即可。不要回复任何 JSON。
"""

# 代理人模式（直接调用外部蓝图文件）
from agent_blueprint import SITE_BLUEPRINT
AGENT_PROMPT = f"""
{SITE_BLUEPRINT}

你现在必须严格遵循以上蓝图的所有逻辑进行作答。
"""
