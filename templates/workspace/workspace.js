// ==========================================
// 工作台核心 JS：画布交互、节点管理、预览
// ==========================================
document.addEventListener("DOMContentLoaded", function() {

    const canvasArea = document.getElementById('canvasArea');
    const nodeContainer = document.getElementById('nodeContainer');
    const previewBox = document.getElementById('previewBox');
    const previewMessages = document.getElementById('previewMessages');
    const previewInput = document.getElementById('previewInput');

    let nodes = [];
    let history = [];
    let historyIndex = -1;
    let isDraggingCanvas = false;
    let isDraggingNode = false;
    let startX, startY, startLeft, startTop;
    let currentDragNode = null;
    let canvasOffsetX = 0, canvasOffsetY = 0;
    let lastMouseX = 0, lastMouseY = 0;

    function saveHistory() {
        history = history.slice(0, historyIndex + 1);
        history.push(JSON.parse(JSON.stringify(nodes)));
        historyIndex++;
        if (history.length > 50) {
            history.shift();
            historyIndex--;
        }
    }

    window.undoAction = function() {
        if (historyIndex > 0) {
            historyIndex--;
            nodes = JSON.parse(JSON.stringify(history[historyIndex]));
            renderNodes();
        }
    };

    window.redoAction = function() {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            nodes = JSON.parse(JSON.stringify(history[historyIndex]));
            renderNodes();
        }
    };

    window.clearCanvas = function() {
        if (nodes.length === 0) return;
        nodes = [];
        saveHistory();
        renderNodes();
    };

    function renderNodes() {
        nodeContainer.innerHTML = '';
        nodes.forEach((node, index) => {
            const el = document.createElement('div');
            el.className = 'canvas-node';
            el.style.left = node.x + 'px';
            el.style.top = node.y + 'px';
            el.dataset.index = index;

            let bodyHtml = `<div class="node-handle"><span>节点 #${index+1}</span><span onclick="deleteNode(${index})" class="cursor-pointer hover:text-red-400">✕</span></div>`;
            if (node.type === 'text') {
                bodyHtml += `<div class="node-title">自动回复</div>`;
                bodyHtml += `<div class="node-body">${node.content || '点击输入文本...'}</div>`;
            } else if (node.type === 'button') {
                bodyHtml += `<div class="node-title">按钮菜单</div>`;
                bodyHtml += `<div class="node-body">${node.content || '点击编辑按钮...'}</div>`;
                if (node.buttons && node.buttons.length > 0) {
                    node.buttons.forEach(b => {
                        bodyHtml += `<span class="inline-block bg-[#493F36] text-white px-2 py-1 rounded text-[10px] mt-1 mr-1">${b}</span>`;
                    });
                }
            } else if (node.type === 'bot') {
                bodyHtml += `<div class="node-title text-[#F5E6CF] flex items-center gap-2"><span>🤖</span> ${node.name}</div>`;
                bodyHtml += `<div class="node-body text-[10px] text-gray-400 mt-1">已绑定，等待配置回复...</div>`;
            }
            el.innerHTML = bodyHtml;

            el.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                if (e.button !== 0) return;
                isDraggingNode = true;
                currentDragNode = el;
                const rect = el.getBoundingClientRect();
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;
                el.style.zIndex = 100;
            });

            nodeContainer.appendChild(el);
        });
    }

    window.deleteNode = function(index) {
        nodes.splice(index, 1);
        saveHistory();
        renderNodes();
    };

    window.addNode = function(type) {
        const baseX = 200 + Math.random() * 300;
        const baseY = 200 + Math.random() * 300;
        const newNode = {
            id: Date.now() + Math.random(),
            type: type,
            x: baseX,
            y: baseY,
            content: type === 'text' ? '输入你的回复...' : '按钮名称',
            buttons: type === 'button' ? ['按钮1', '按钮2'] : []
        };
        nodes.push(newNode);
        saveHistory();
        renderNodes();
    };

    // ✅ 终极修正：精确放在画布几何中心
    window.addBotNode = function(name) {
        const botCount = nodes.filter(n => n.type === 'bot').length;
        
        // 画布中心 0,0 正好是屏幕视角的中心
        const baseX = 0; 
        const baseY = 0 + (botCount * 140);

        const newNode = {
            id: Date.now() + Math.random(),
            type: 'bot',
            name: name || '我的机器人',
            x: baseX,
            y: baseY
        };
        nodes.push(newNode);
        saveHistory();
        renderNodes();
    };

    // --- 画布拖拽 ---
    canvasArea.addEventListener('mousedown', (e) => {
        if (e.button !== 0 || e.target !== canvasArea && e.target.id === 'canvasArea') return;
        isDraggingCanvas = true;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
        canvasArea.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', (e) => {
        if (isDraggingNode && currentDragNode) {
            const left = e.clientX - startX - canvasArea.getBoundingClientRect().left;
            const top = e.clientY - startY - canvasArea.getBoundingClientRect().top;
            currentDragNode.style.left = left + 'px';
            currentDragNode.style.top = top + 'px';
        }
        if (isDraggingCanvas) {
            const dx = e.clientX - lastMouseX;
            const dy = e.clientY - lastMouseY;
            canvasOffsetX += dx;
            canvasOffsetY += dy;
            canvasOffsetX = Math.max(-window.innerWidth * 0.5, Math.min(window.innerWidth * 0.5, canvasOffsetX));
            canvasOffsetY = Math.max(-window.innerHeight * 0.5, Math.min(window.innerHeight * 0.5, canvasOffsetY));
            canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
        }
    });

    document.addEventListener('mouseup', (e) => {
        if (isDraggingNode && currentDragNode) {
            const index = parseInt(currentDragNode.dataset.index);
            if (!isNaN(index)) {
                nodes[index].x = parseFloat(currentDragNode.style.left);
                nodes[index].y = parseFloat(currentDragNode.style.top);
                saveHistory();
            }
            currentDragNode.style.zIndex = 1;
            isDraggingNode = false;
            currentDragNode = null;
        }
        if (isDraggingCanvas) {
            isDraggingCanvas = false;
            canvasArea.style.cursor = 'grab';
        }
    });

    canvasArea.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            isDraggingCanvas = true;
            lastMouseX = touch.clientX;
            lastMouseY = touch.clientY;
        }
    });

    document.addEventListener('touchmove', (e) => {
        if (isDraggingCanvas && e.touches.length === 1) {
            const touch = e.touches[0];
            const dx = touch.clientX - lastMouseX;
            const dy = touch.clientY - lastMouseY;
            canvasOffsetX += dx;
            canvasOffsetY += dy;
            canvasOffsetX = Math.max(-window.innerWidth * 0.5, Math.min(window.innerWidth * 0.5, canvasOffsetX));
            canvasOffsetY = Math.max(-window.innerHeight * 0.5, Math.min(window.innerHeight * 0.5, canvasOffsetY));
            canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
            lastMouseX = touch.clientX;
            lastMouseY = touch.clientY;
        }
    }, { passive: false });

    document.addEventListener('touchend', (e) => {
        if (isDraggingCanvas) {
            isDraggingCanvas = false;
        }
    });

    window.togglePreview = function() {
        previewBox.classList.toggle('open');
        if (previewBox.classList.contains('open')) {
            document.getElementById('previewToggleBtn').innerText = '👁 关闭预览';
        } else {
            document.getElementById('previewToggleBtn').innerText = '👁 预览';
        }
    };

    window.sendPreviewMessage = function() {
        const text = previewInput.value.trim();
        if (!text) return;
        const userMsg = document.createElement('div');
        userMsg.className = 'preview-msg-user';
        userMsg.innerText = text;
        previewMessages.appendChild(userMsg);
        previewMessages.scrollTop = previewMessages.scrollHeight;
        previewInput.value = '';

        setTimeout(() => {
            const botMsg = document.createElement('div');
            botMsg.className = 'preview-msg-bot';
            const textNode = nodes.find(n => n.type === 'text');
            if (textNode) {
                botMsg.innerText = textNode.content || '预设回复内容';
                const btnNode = nodes.find(n => n.type === 'button');
                if (btnNode && btnNode.buttons) {
                    const btnContainer = document.createElement('div');
                    btnContainer.style.marginTop = '8px';
                    btnNode.buttons.forEach(b => {
                        const btn = document.createElement('span');
                        btn.className = 'inline-block bg-[#493F36] text-white px-2 py-1 rounded text-[10px] mt-1 mr-1 cursor-pointer';
                        btn.innerText = b;
                        btnContainer.appendChild(btn);
                    });
                    botMsg.appendChild(btnContainer);
                }
            } else {
                botMsg.innerText = '暂无配置回复节点，请先在左侧添加文本回复！';
            }
            previewMessages.appendChild(botMsg);
            previewMessages.scrollTop = previewMessages.scrollHeight;
        }, 600);
    };
});
