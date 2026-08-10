// 卡片互锁逻辑（彻底重写，直接操作DOM，绝对稳定）
document.addEventListener("DOMContentLoaded", function() {
    // 定义所有卡片关闭函数
    window.closeLoginModal = function() {
        const el = document.getElementById('loginModal');
        if (el) el.classList.remove('active');
    };
    window.closeMusicModal = function() {
        const el = document.getElementById('musicModal');
        if (el) el.classList.remove('active');
    };
    window.closeContactModal = function() {
        const el = document.getElementById('contactModal');
        if (el) el.classList.remove('active');
    };
    window.closeUpdateLogModal = function() {
        const el = document.getElementById('updateLogModal');
        if (el) el.classList.remove('active');
    };
    window.closeBecomeFanModal = function() {
        const el = document.getElementById('becomeFanModal');
        if (el) el.classList.remove('active');
    };

    // 一键关闭所有卡片的辅助函数
    window.closeAllModals = function() {
        const ids = ['loginModal', 'musicModal', 'contactModal', 'updateLogModal', 'becomeFanModal'];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.remove('active');
        });
    };

    // 定义所有卡片打开函数（自带“先关闭其他”的逻辑）
    window.openLoginModal = function() {
        window.closeAllModals(); // 先关掉其它所有卡片
        const el = document.getElementById('loginModal');
        if (el) el.classList.add('active'); // 然后打开当前卡片
    };
    window.openMusicModal = function() {
        window.closeAllModals();
        const el = document.getElementById('musicModal');
        if (el) el.classList.add('active');
    };
    window.openContactModal = function() {
        window.closeAllModals();
        const el = document.getElementById('contactModal');
        if (el) el.classList.add('active');
    };
    window.openUpdateLogModal = function() {
        window.closeAllModals();
        const el = document.getElementById('updateLogModal');
        if (el) el.classList.add('active');
    };

    // ==========================================================
    // ✅ 最终定型：每一次点击开发者，位置都完全一致
    // （不再区分第一次或第N次，完全由 splash.html 里的 CSS 控制位置）
    // ==========================================================
    window.openBecomeFanModal = function() {
        window.closeAllModals();
        const el = document.getElementById('becomeFanModal');
        if (el) {
            // 不强行修改 flex 对齐和 padding 了，让原生 CSS 控制它
            el.classList.add('active');
        }
    };
});
