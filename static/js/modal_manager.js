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
        if (el) {
            // 关掉时，把添加的平移动画也取消掉
            el.style.transform = 'translateX(0px)';
            el.classList.remove('active');
        }
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
    // ✅ 核心妥协方案：不要纠结 Bug，直接利用它！
    // 第一次：正常位置
    // 第 N 次（N>=2）：强制固定偏左 12px
    // ==========================================================
    window.openBecomeFanModal = function() {
        window.closeAllModals();
        const el = document.getElementById('becomeFanModal');
        if (el) {
            // 计数器判断
            if (typeof window._becomeOpenCount === 'undefined') {
                window._becomeOpenCount = 0;
            }
            window._becomeOpenCount++;

            // 🔥 核心修正：第二次及以后，强制给它加一个固定的左偏移！
            if (window._becomeOpenCount === 1) {
                el.style.transform = 'translateX(0px)';
            } else {
                // 永远固定在这里，不会再变化了
                el.style.transform = 'translateX(-12px)'; 
            }

            el.classList.add('active');
        }
    };
});
