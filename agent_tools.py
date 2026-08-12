# agent_tools.py
# 定义可供 AI 智能体调用的工具列表

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bind_bot",
            "description": "绑定一个 Telegram 机器人到当前工作台。请务必询问用户的 Token 和 Telegram ID。",
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "机器人的 Bot Token"
                    },
                    "telegram_id": {
                        "type": "string",
                        "description": "用户的 Telegram ID (纯数字格式)"
                    },
                    "name": {
                        "type": "string",
                        "description": "机器人的显示名称，默认为宫水编辑器"
                    }
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
                    "name": {
                        "type": "string",
                        "description": "节点的显示名称"
                    },
                    "avatar": {
                        "type": "string",
                        "description": "机器人的头像 URL (可选)"
                    }
                },
                "required": ["name"]
            }
        }
    }
]
