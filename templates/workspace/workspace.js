<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>开发工作台 - gsbot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
    <style>
        body { 
            font-family: -apple-system, "PingFang SC", "Helvetica Neue", sans-serif; 
            background-color: #0f0f10;
            overflow: hidden; 
        }
        .glass-panel {
            background: rgba(15, 15, 18, 0.15);
            backdrop-filter: blur(28px);
            -webkit-backdrop-filter: blur(28px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6);
            border-radius: 28px;
        }
        .canvas-node {
            position: absolute;
            padding: 12px 16px;
            background: rgba(30, 30, 30, 0.85);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #e5e7eb;
            cursor: grab;
            min-width: 120px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            user-select: none;
            transition: box-shadow 0.2s;
            z-index: 10;
        }
        .canvas-node:active { cursor: grabbing; box-shadow: 0 8px 24px rgba(0,0,0,0.8); }
        .canvas-node .node-title { font-weight: 600; font-size: 14px; margin-top: 4px; }
        
        .preview-box {
            position: fixed; bottom: 24px; right: 24px; width: 320px; height: 480px;
            background: rgba(10, 10, 12, 0.7); backdrop-filter: blur(24px); border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px; box-shadow: 0 16px 48px rgba(0,0,0,0.8);
            display: flex; flex-direction: column; overflow: hidden; transform: translateY(120%); opacity: 0;
            transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .preview-box.open { transform: translateY(0); opacity: 1; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
    </style>
</head>
<body>
    
    <!-- 右上角三枚完美等宽按钮 -->
    <div class="fixed top-4 right-4 z-50 flex items-center gap-2 w-[340px]">
        <button onclick="toggleAgentPanel()" class="flex-1 text-center px-3 py-2 bg-[rgba(255,255,255,0.08)] border border-[rgba(255,255,255,0.3)] backdrop-blur-[6px] text-[13px] font-medium text-white rounded-[30px] transition hover:bg-[rgba(255,255,255,0.15)] active:scale-95">
            Agent
        </button>
        <button onclick="toggleFullScreen()" class="flex-1 text-center px-3 py-2 bg-[rgba(255,255,255,0.08)] border border-[rgba(255,255,255,0.3)] backdrop-blur-[6px] text-[13px] font-medium text-white rounded-[30px] transition hover:bg-[rgba(255,255,255,0.15)] active:scale-95">
            全屏显示
        </button>
        <button onclick="window.location.href='/'" class="flex-1 text-center px-3 py-2 bg-[rgba(255,255,255,0.08)] border border-[rgba(255,255,255,0.3)] backdrop-blur-[6px] text-[13px] font-medium text-white rounded-[30px] transition hover:bg-[rgba(255,255,255,0.15)] active:scale-95">
            返回主页
        </button>
    </div>

    <!-- 主工作区 -->
    <div class="flex w-screen h-screen">
        
        <!-- 左侧面板 -->
        <div class="fixed left-6 top-6 bottom-6 w-[480px] glass-panel flex flex-col p-8 z-20 rounded-3xl">
            <h1 class="text-4xl font-bold text-white tracking-wide mb-8">机器人配置</h1>
            
            <div class="flex flex-col sm:flex-row gap-4">
                <input id="botTokenInput" type="password" placeholder="请输入 Bot Token" class="flex-1 bg-black/20 border border-white/10 rounded-xl px-5 py-4 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-1 focus:ring-white/30 transition-all">
                <button onclick="bindBotToken()" class="bg-[#493F36] hover:bg-[#3a322c] text-white font-medium rounded-xl px-6 py-4 text-sm transition active:scale-95 whitespace-nowrap">
                    绑定
                </button>
            </div>
        </div>

        <!-- 右侧：无限画布 -->
        <div class="flex-1 h-full relative overflow-hidden">
            <div class="absolute inset-0 pointer-events-none opacity-5" style="background-image: radial-gradient(#ffffff 1px, transparent 1px); background-size: 40px 40px;"></div>
            
            <!-- ✅ 重点修复：图片路径直接指向 static/ 根目录 -->
            <div id="canvasArea" class="absolute inset-0 w-[200vw] h-[200vh] left-[-50vw] top-[-50vh] cursor-grab active:cursor-grabbing" style="background-image: url('{{ url_for('static', filename='IMG_20260808_170606.png') }}'); background-size: cover; background-position: center; background-repeat: no-repeat; touch-action: none;">
                <div id="nodeContainer" class="relative w-full h-full">
                </div>
            </div>
        </div>

        <!-- 预览窗口 -->
        <div id="previewBox" class="preview-box z-50">
            <div class="preview-header px-4 py-3 border-b border-white/5 text-white/60 text-sm flex justify-between">
                <span>🤖 机器人预览</span>
                <span onclick="document.getElementById('previewBox').classList.remove('open')" class="cursor-pointer hover:text-white">✕</span>
            </div>
            <div class="flex-1 bg-transparent p-4 text-white/50 text-sm flex items-center justify-center">绑定机器人后，此处将显示节点</div>
        </div>
    </div>

    <!-- 引入 JS -->
    <script src="{{ url_for('static', filename='workspace/workspace.js') }}"></script>
    {% include 'components/agent_action_panel.html' %}

    <script>
        window.toggleFullScreen = function() {
            if (!document.fullscreenElement) document.documentElement.requestFullscreen();
            else if (document.exitFullscreen) document.exitFullscreen();
        };

        const originalToggle = window.toggleAgentPanel;
        window.toggleAgentPanel = function() {
            const wrapper = document.getElementById('agentPanelWrapper');
            const panel = document.getElementById('agentPanel');
            if (!wrapper || !panel) return;
            const isWorkspace = !document.getElementById('cardStackContainer');
            if (isWorkspace) {
                if (wrapper.style.display === 'block') {
                    panel.classList.add('translate-y-full');
                    setTimeout(() => { wrapper.style.display = 'none'; }, 300);
                } else {
                    wrapper.style.display = 'block';
                    wrapper.style.width = '360px';
                    wrapper.style.left = 'auto';
                    wrapper.style.right = '24px';
                    wrapper.style.transform = 'none';
                    setTimeout(() => {
                        panel.classList.remove('translate-y-full');
                        const input = document.getElementById('agentInput');
                        if (input) setTimeout(() => input.focus(), 400);
                    }, 10);
                }
            } else {
                if (typeof originalToggle === 'function') originalToggle();
            }
        };
    </script>
</body>
</html>
