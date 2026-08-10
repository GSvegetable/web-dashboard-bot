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
            // 关闭时，顺便把计数器重置，或者保持让下一次打开重新计算。
            // 但我们希望用户看到"第二次"效果，重置的话用户总是看到"第一次"。
            // 所以这里不做重置，保持累积。
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
    // 🔥 核心修正：专门修改开发者卡片的打开逻辑
    // 第1次打开：正常靠右（flex-end）
    // 第2次及以后所有打开：强制贴靠最左边（flex-start）
    // ==========================================================
    window.openBecomeFanModal = function() {
        window.closeAllModals();
        const el = document.getElementById('becomeFanModal');
        if (el) {
            // 1. 初始化或累加专属计数器
            if (typeof window._becomeOpenCount === 'undefined') {
                window._becomeOpenCount = 0;
            }
            window._becomeOpenCount++;

            // 2. 根据打开次数，强制修改外层对齐方向
            if (window._becomeOpenCount === 1) {
                // 第一次：保持你原始完美的靠右位置！
                el.style.justifyContent = 'flex-end';
                el.style.paddingLeft = '0px';
                el.style.paddingRight = '24px';
            } else {
                // 第二次及之后所有点击：直接劈到画面最左边！
                el.style.justifyContent = 'flex-start';
                el.style.paddingLeft = '24px'; // 留一点点内边距，不至于完全贴着边缘
                el.style.paddingRight = '0px';
            }

            // 3. 弹出卡片
            el.classList.add('active');
        }
    };
});
