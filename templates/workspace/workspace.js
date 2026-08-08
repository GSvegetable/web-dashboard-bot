document.addEventListener("DOMContentLoaded", function() {
    const canvasArea = document.getElementById('canvasArea');
    const nodeContainer = document.getElementById('nodeContainer');
    let nodes = [];
    let isDraggingCanvas = false;
    let canvasOffsetX = 0, canvasOffsetY = 0;
    let lastMouseX = 0, lastMouseY = 0;

    // ✅ 终极防御：禁止整个网页在任何情况下上下滚动
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';

    // ------------------- 画布拖拽逻辑 -------------------
    // 1. 鼠标拖拽（PC端）
    canvasArea.addEventListener('mousedown', (e) => {
        isDraggingCanvas = true;
        lastMouseX = e.clientX; lastMouseY = e.clientY;
        canvasArea.style.cursor = 'grabbing';
        e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
        if (!isDraggingCanvas) return;
        const dx = e.clientX - lastMouseX, dy = e.clientY - lastMouseY;
        canvasOffsetX += dx; canvasOffsetY += dy;
        canvasOffsetX = Math.max(-window.innerWidth * 0.8, Math.min(window.innerWidth * 0.8, canvasOffsetX));
        canvasOffsetY = Math.max(-window.innerHeight * 0.8, Math.min(window.innerHeight * 0.8, canvasOffsetY));
        canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
        lastMouseX = e.clientX; lastMouseY = e.clientY;
    });
    document.addEventListener('mouseup', () => { isDraggingCanvas = false; canvasArea.style.cursor = 'grab'; });

    // 2. 触摸/手指拖拽（iPad/手机端）
    canvasArea.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            e.preventDefault(); // 强制拦截浏览器上下滚动作死
            // ⚠️ 关键诊断：如果这里弹出了框，说明你的手指确实触摸成功了！
            alert('✅ 触摸成功！如果看到这个弹窗，说明代码生效了。点击确定后，请尝试滑动画布。');
            
            isDraggingCanvas = true;
            lastMouseX = e.touches[0].clientX;
            lastMouseY = e.touches[0].clientY;
        }
    }, { passive: false });

    document.addEventListener('touchmove', (e) => {
        if (isDraggingCanvas && e.touches.length === 1) {
            e.preventDefault();
            const dx = e.touches[0].clientX - lastMouseX;
            const dy = e.touches[0].clientY - lastMouseY;
            canvasOffsetX += dx; canvasOffsetY += dy;
            canvasOffsetX = Math.max(-window.innerWidth * 0.8, Math.min(window.innerWidth * 0.8, canvasOffsetX));
            canvasOffsetY = Math.max(-window.innerHeight * 0.8, Math.min(window.innerHeight * 0.8, canvasOffsetY));
            canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
            lastMouseX = e.touches[0].clientX;
            lastMouseY = e.touches[0].clientY;
        }
    }, { passive: false });

    document.addEventListener('touchend', () => { isDraggingCanvas = false; });

    // ------------------- 节点拖拽 -------------------
    function renderNode(node) {
        const el = document.createElement('div');
        el.className = 'canvas-node';
        el.style.left = node.x + 'px';
        el.style.top = node.y + 'px';
        el.innerHTML = `<div class="node-title">🤖 ${node.name}</div><div class="text-[10px] text-gray-400 mt-1">已接入宫水编辑器</div>`;
        nodeContainer.appendChild(el);

        let isDraggingNode = false, startX, startY;
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

    // ------------------- 绑定 Token -------------------
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
                const newNode = { x: 560, y: 150, name: data.name };
                nodes.push(newNode);
                renderNode(newNode);
                tokenInput.value = ''; 
            } else {
                alert('绑定失败：' + (data.error || 'Token 无效或网络错误'));
            }
        })
        .catch(() => alert('网络请求失败，请检查后端服务'));
    };
});
