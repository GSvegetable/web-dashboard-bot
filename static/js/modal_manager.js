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
            // 关闭时重置卡片位置
            const modalBox = el.querySelector('.modal-box');
            if (modalBox) modalBox.style.transform = 'translateX(0px)';
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
    // ✅ 核心最终版：二次点击固定左移 28px！
    // ==========================================================
    window.openBecomeFanModal = function() {
        window.closeAllModals();
        const el = document.getElementById('becomeFanModal');
        if (el) {
            if (typeof window._becomeOpenCount === 'undefined') {
                window._becomeOpenCount = 0;
            }
            window._becomeOpenCount++;

            const modalBox = el.querySelector('.modal-box');
            if (modalBox) {
                if (window._becomeOpenCount === 1) {
                    modalBox.style.transform = 'translateX(0px)'; // 第一次：完美原位置
                } else {
                    modalBox.style.transform = 'translateX(-28px)'; // ✨ 后续所有：固定左移 28px
                }
            }

            el.classList.add('active');
        }
    };
});
