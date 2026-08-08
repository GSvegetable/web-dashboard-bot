document.addEventListener("DOMContentLoaded", function() {
    const canvasArea = document.getElementById('canvasArea');
    const nodeContainer = document.getElementById('nodeContainer');
    let nodes = [];
    let isDraggingCanvas = false;
    let canvasOffsetX = 0, canvasOffsetY = 0;
    let lastMouseX = 0, lastMouseY = 0;

    // 画布平移控制（鼠标/触摸）修复
    canvasArea.addEventListener('mousedown', (e) => {
        if (e.target !== canvasArea && e.target.id !== 'canvasArea') return;
        isDraggingCanvas = true;
        lastMouseX = e.clientX; lastMouseY = e.clientY;
        canvasArea.style.cursor = 'grabbing';
    });
    document.addEventListener('mousemove', (e) => {
        if (isDraggingCanvas) {
            const dx = e.clientX - lastMouseX, dy = e.clientY - lastMouseY;
            canvasOffsetX += dx; canvasOffsetY += dy;
            canvasOffsetX = Math.max(-window.innerWidth, Math.min(window.innerWidth, canvasOffsetX));
            canvasOffsetY = Math.max(-window.innerHeight, Math.min(window.innerHeight, canvasOffsetY));
            canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
            lastMouseX = e.clientX; lastMouseY = e.clientY;
        }
    });
    document.addEventListener('mouseup', () => { isDraggingCanvas = false; canvasArea.style.cursor = 'grab'; });
    // 触摸事件（支持平板）
    canvasArea.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) { isDraggingCanvas = true; lastMouseX = e.touches[0].clientX; lastMouseY = e.touches[0].clientY; }
    });
    document.addEventListener('touchmove', (e) => {
        if (isDraggingCanvas && e.touches.length === 1) {
            const dx = e.touches[0].clientX - lastMouseX, dy = e.touches[0].clientY - lastMouseY;
            canvasOffsetX += dx; canvasOffsetY += dy;
            canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
            lastMouseX = e.touches[0].clientX; lastMouseY = e.touches[0].clientY;
        }
    }, { passive: false });
    document.addEventListener('touchend', () => { isDraggingCanvas = false; });

    // 渲染节点
    function renderNode(node) {
        const el = document.createElement('div');
        el.className = 'canvas-node';
        el.style.left = node.x + 'px';
        el.style.top = node.y + 'px';
        el.innerHTML = `<div class="node-title">🤖 ${node.name}</div><div class="text-[10px] text-gray-400 mt-1">已接入宫水编辑器</div>`;
        nodeContainer.appendChild(el);

        // 节点拖拽逻辑
        let isDraggingNode = false, startX, startY, startLeft, startTop;
        el.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            isDraggingNode = true;
            const rect = el.getBoundingClientRect();
            startX = e.clientX - rect.left; startY = e.clientY - rect.top;
            el.style.zIndex = 100;
            const onMove = (ev) => {
                if (!isDraggingNode) return;
                const left = ev.clientX - startX - canvasArea.getBoundingClientRect().left;
                const top = ev.clientY - startY - canvasArea.getBoundingClientRect().top;
                el.style.left = left + 'px'; el.style.top = top + 'px';
            };
            const onUp = () => { isDraggingNode = false; el.style.zIndex = 10; document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); };
            document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp);
        });
    }

    // 暴露绑定函数
    window.bindBotToken = function() {
        const tokenInput = document.getElementById('botTokenInput');
        const token = tokenInput.value.trim();
        if (!token) return alert('请输入有效的 Telegram Bot Token');

        fetch('/api/bind_bot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // 生成节点位置：在卡片右侧 x=560, y=150 处
                const newNode = { x: 560, y: 150, name: data.name };
                nodes.push(newNode);
                renderNode(newNode);
                tokenInput.value = ''; 
                console.log('✅ 绑定成功，节点已生成:', data.name);
            } else {
                alert('绑定失败：' + (data.error || 'Token 无效或网络错误'));
                console.error('❌ 绑定失败:', data.error);
            }
        })
        .catch(err => {
            alert('网络请求失败，请检查后端服务');
            console.error('❌ 请求异常:', err);
        });
    };
});
