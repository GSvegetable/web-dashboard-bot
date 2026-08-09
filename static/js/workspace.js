// ==========================================
// 工作台核心 JS：只保留预览窗口功能
// ==========================================
document.addEventListener("DOMContentLoaded", function() {
    // --- 基础元素获取 ---
    const previewBox = document.getElementById('previewBox');
    const previewMessages = document.getElementById('previewMessages');
    const previewInput = document.getElementById('previewInput');

    // --- 预览窗口控制 ---
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
            botMsg.innerText = '模拟机器人回复...'; 
            previewMessages.appendChild(botMsg);
            previewMessages.scrollTop = previewMessages.scrollHeight;
        }, 600);
    };
});
