// 卡片互锁逻辑（打开一个，自动关闭其他）
document.addEventListener("DOMContentLoaded", function() {
    // 备份原本的打开函数
    const originalOpenLogin = window.openLoginModal;
    const originalOpenMusic = window.openMusicModal;
    const originalOpenContact = window.openContactModal;

    // 定义新的打开逻辑：带着“互锁”功能
    window.openLoginModal = function() {
        // 先关掉其他的
        if (document.getElementById('musicModal') && document.getElementById('musicModal').classList.contains('active')) {
            window.closeMusicModal();
        }
        if (document.getElementById('contactModal') && document.getElementById('contactModal').classList.contains('active')) {
            window.closeContactModal();
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
            window.closeContactModal();
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
