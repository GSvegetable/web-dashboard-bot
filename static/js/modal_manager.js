// 卡片互锁逻辑（修复联系开发者卡片无法被其他按钮关闭的Bug）
document.addEventListener("DOMContentLoaded", function() {
    // 备份原本的打开函数
    const originalOpenLogin = window.openLoginModal;
    const originalOpenMusic = window.openMusicModal;
    const originalOpenContact = window.openContactModal;

    // 覆盖 closeContactModal，解决“不带e参数无法关闭”的问题
    window.closeContactModal = function() {
        const modal = document.getElementById('contactModal');
        if (modal) {
            modal.classList.remove('active');
        }
    };

    // 定义新的打开逻辑：带着“互锁”功能
    window.openLoginModal = function() {
        // 先关掉其他的
        if (document.getElementById('musicModal') && document.getElementById('musicModal').classList.contains('active')) {
            window.closeMusicModal();
        }
        if (document.getElementById('contactModal') && document.getElementById('contactModal').classList.contains('active')) {
            window.closeContactModal(); // 现在这里一定能执行成功
        }
        // 再执行原本的打开逻辑
        if (originalOpenLogin) originalOpenLogin();
    };

    window.openMusicModal = function() {
        // 先关掉其他的
        if (document.getElementById('loginModal') && document.getElementById('loginModal').classList.contains('active')) {
            window.closeLoginModal();
        }
        if (document.getElementById('contactModal') && document.getElementById('contactModal').classList.contains('active')) {
            window.closeContactModal(); // 现在这里一定能执行成功
        }
        // 再执行原本的打开逻辑
        if (originalOpenMusic) originalOpenMusic();
    };

    window.openContactModal = function() {
        // 先关掉其他的
        if (document.getElementById('loginModal') && document.getElementById('loginModal').classList.contains('active')) {
            window.closeLoginModal();
        }
        if (document.getElementById('musicModal') && document.getElementById('musicModal').classList.contains('active')) {
            window.closeMusicModal();
        }
        // 再执行原本的打开逻辑
        if (originalOpenContact) originalOpenContact();
    };
});
