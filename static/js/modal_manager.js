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

    // 定义所有卡片打开函数
    window.openLoginModal = function() {
        window.closeAllModals();
        const el = document.getElementById('loginModal');
        if (el) el.classList.add('active');
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
    // ✅ 彻底抹除偏移 Bug：强制每一次都在最右侧！
    // ==========================================================
    window.openBecomeFanModal = function() {
        window.closeAllModals();
        const el = document.getElementById('becomeFanModal');
        if (el) {
            // 🛡️ 每一回打开，都强制把容器对齐到右侧
            // 防止任何缓存的前端代码把它往左拽
            el.style.justifyContent = 'flex-end';
            el.style.paddingLeft = '0px';
            el.style.paddingRight = '24px';
            
            // 打开卡片
            el.classList.add('active');
        }
    };
});
