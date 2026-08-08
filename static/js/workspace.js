// ==========================================
// 工作台核心 JS：画布交互、节点管理、预览
// ==========================================
document.addEventListener("DOMContentLoaded", function() {

    // --- 基础元素获取 ---
    const canvasArea = document.getElementById('canvasArea');
    const nodeContainer = document.getElementById('nodeContainer');
    const previewBox = document.getElementById('previewBox');
    const previewMessages = document.getElementById('previewMessages');
    const previewInput = document.getElementById('previewInput');

    // --- 状态存储与历史记录 ---
    let nodes = [];
    let history = [];
    let historyIndex = -1;
    let isDraggingCanvas = false;
    let isDraggingNode = false;
    let startX, startY, startLeft, startTop;
    let currentDragNode = null;
    let canvasOffsetX = 0, canvasOffsetY = 0;
    let lastMouseX = 0, lastMouseY = 0;

    // 保存历史快照
    function saveHistory() {
        // 截断后面的历史
        history = history.slice(0, historyIndex + 1);
        // 深拷贝当前节点状态
        history.push(JSON.parse(JSON.stringify(nodes)));
        historyIndex++;
        // 限制历史长度避免内存爆炸
        if (history.length > 50) {
            history.shift();
            historyIndex--;
        }
    }

    // 撤销
    window.undoAction = function() {
        if (historyIndex > 0) {
            historyIndex--;
            nodes = JSON.parse(JSON.stringify(history[historyIndex]));
            renderNodes();
        }
    };

    // 重做
    window.redoAction = function() {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            nodes = JSON.parse(JSON.stringify(history[historyIndex]));
            renderNodes();
        }
    };

    // 清空画布
    window.clearCanvas = function() {
        if (nodes.length === 0) return;
        nodes = [];
        saveHistory();
        renderNodes();
    };

    // --- 渲染节点 ---
    function renderNodes() {
        nodeContainer.innerHTML = '';
        nodes.forEach((node, index) => {
            const el = document.createElement('div');
            el.className = 'canvas-node';
            el.style.left = node.x + 'px';
            el.style.top = node.y + 'px';
            el.dataset.index = index;

            // 节点内容
            let bodyHtml = `<div class="node-handle"><span>节点 #${index+1}</span><span onclick="deleteNode(${index})" class="cursor-pointer hover:text-red-400">✕</span></div>`;
            if (node.type === 'text') {
                bodyHtml += `<div class="node-title">自动回复</div>`;
                bodyHtml += `<div class="node-body">${node.content || '点击输入文本...'}</div>`;
            } else if (node.type === 'button') {
                bodyHtml += `<div class="node-title">按钮菜单</div>`;
                bodyHtml += `<div class="node-body">${node.content || '点击编辑按钮...'}</div>`;
                if (node.buttons && node.buttons.length > 0) {
                    node.buttons.forEach(b => {
                        bodyHtml += `<span class="node-button">${b}</span>`;
                    });
                }
            }
            el.innerHTML = bodyHtml;

            // 节点拖拽逻辑
            el.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                if (e.button !== 0) return;
                isDraggingNode = true;
                currentDragNode = el;
                const rect = el.getBoundingClientRect();
                // 计算鼠标在节点内部的偏移量
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;
                el.style.zIndex = 100;
            });

            nodeContainer.appendChild(el);
        });
    }

    // 删除节点
    window.deleteNode = function(index) {
        nodes.splice(index, 1);
        saveHistory();
        renderNodes();
    };

    // 添加节点（从左侧面板触发）
    window.addNode = function(type) {
        // 取一个随机位置，不要在左上角堆叠
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

    // --- 画布拖拽平移 ---
    canvasArea.addEventListener('mousedown', (e) => {
        if (e.button !== 0 || e.target !== canvasArea && e.target.id === 'canvasArea') return;
        isDraggingCanvas = true;
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
        canvasArea.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', (e) => {
        if (isDraggingNode && currentDragNode) {
            // 计算节点新位置
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
            // 限制平移范围，不要跑出无限画布太远
            canvasOffsetX = Math.max(-window.innerWidth * 0.5, Math.min(window.innerWidth * 0.5, canvasOffsetX));
            canvasOffsetY = Math.max(-window.innerHeight * 0.5, Math.min(window.innerHeight * 0.5, canvasOffsetY));
            canvasArea.style.transform = `translate(${canvasOffsetX}px, ${canvasOffsetY}px)`;
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
        }
    });

    document.addEventListener('mouseup', (e) => {
        if (isDraggingNode && currentDragNode) {
            // 保存节点绝对位置到数据
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

    // 初始化一个默认节点
    window.addNode('text');

    // --- 预览交互逻辑 ---
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

        // 1. 显示用户消息
        const userMsg = document.createElement('div');
        userMsg.className = 'preview-msg-user';
        userMsg.innerText = text;
        previewMessages.appendChild(userMsg);
        previewMessages.scrollTop = previewMessages.scrollHeight;
        previewInput.value = '';

        // 2. 模拟机器人回复 (根据画布第一个匹配的规则)
        setTimeout(() => {
            const botMsg = document.createElement('div');
            botMsg.className = 'preview-msg-bot';
            // 简单模拟：如果有文本节点，就回那个
            const textNode = nodes.find(n => n.type === 'text');
            if (textNode) {
                botMsg.innerText = textNode.content || '预设回复内容';
                
                // 如果是按钮节点，把按钮加在回复下面
                const btnNode = nodes.find(n => n.type === 'button');
                if (btnNode && btnNode.buttons) {
                    const btnContainer = document.createElement('div');
                    btnContainer.style.marginTop = '8px';
                    btnNode.buttons.forEach(b => {
                        const btn = document.createElement('span');
                        btn.className = 'node-button';
                        btn.style.marginRight = '6px';
                        btn.style.cursor = 'pointer';
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

    // 机器人连接模拟
    window.connectBot = function() {
        const token = document.getElementById('botTokenInput').value;
        const status = document.getElementById('botStatus');
        if (token.length > 10) {
            status.innerHTML = '✅ 已连接，正在等待操作...';
            status.className = 'mt-1 text-[10px] text-green-400';
        } else {
            status.innerHTML = '❌ Token 格式错误';
            status.className = 'mt-1 text-[10px] text-red-400';
        }
    };
});
