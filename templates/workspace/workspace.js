document.addEventListener("DOMContentLoaded", function() {
    const canvasArea = document.getElementById('canvasArea');
    const nodeContainer = document.getElementById('nodeContainer');
    let nodes = [];
    let isDraggingCanvas = false;
    let canvasOffsetX = 0, canvasOffsetY = 0;
    let lastTouchX = 0, lastTouchY = 0;

    // ---------- 画布平移（PC 鼠标） ----------
    canvasArea.addEventListener('mousedown', (e) => {
        isDraggingCanvas = true;
        lastTouchX = e.clientX; lastTouchY = e.clientY;
        e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
        if (!isDraggingCanvas) return;
        const dx = e.clientX - lastTouchX, dy = e.clientY - lastTouchY;
        canvasOffsetX += dx; canvasOffsetY += dy;
        canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
        lastTouchX = e.clientX; lastTouchY = e.clientY;
    });
    document.addEventListener('mouseup', () => { isDraggingCanvas = false; });

    // ---------- 画布平移（iPad 触摸） ----------
    canvasArea.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            e.preventDefault(); // 阻止网页滚动
            isDraggingCanvas = true;
            lastTouchX = e.touches[0].clientX;
            lastTouchY = e.touches[0].clientY;
        }
    }, { passive: false });

    document.addEventListener('touchmove', (e) => {
        if (isDraggingCanvas && e.touches.length === 1) {
            e.preventDefault();
            const dx = e.touches[0].clientX - lastTouchX;
            const dy = e.touches[0].clientY - lastTouchY;
            canvasOffsetX += dx; canvasOffsetY += dy;
            canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
            lastTouchX = e.touches[0].clientX;
            lastTouchY = e.touches[0].clientY;
        }
    }, { passive: false });

    document.addEventListener('touchend', () => { isDraggingCanvas = false; });

    // ---------- 节点渲染 ----------
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

    // ---------- 绑定 Token ----------
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
