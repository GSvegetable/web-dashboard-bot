// 卡片互锁逻辑（修复联系开发者卡片无法被其他按钮关闭的Bug + 新增两个占位按钮）
document.addEventListener("DOMContentLoaded", function() {
    // 备份原本的打开函数
    const originalOpenLogin = window.openLoginModal;
    const originalOpenMusic = window.openMusicModal;
    const originalOpenContact = window.openContactModal;
    const originalOpenUpdateLog = window.openUpdateLogModal;
    const originalOpenBecomeFan = window.openBecomeFanModal;

    // 覆盖关闭函数，解决“不带e参数无法关闭”的问题
    window.closeLoginModal = function() {
        const modal = document.getElementById('loginModal');
        if (modal) modal.classList.remove('active');
    };
    window.closeMusicModal = function() {
        const modal = document.getElementById('musicModal');
        if (modal) modal.classList.remove('active');
    };
    window.closeContactModal = function() {
        const modal = document.getElementById('contactModal');
        if (modal) modal.classList.remove('active');
    };
    window.closeUpdateLogModal = function() {
        const modal = document.getElementById('updateLogModal');
        if (modal) modal.classList.remove('active');
    };
    window.closeBecomeFanModal = function() {
        const modal = document.getElementById('becomeFanModal');
        if (modal) modal.classList.remove('active');
    };

    // 定义打开逻辑：带着“互锁”功能
    window.openLoginModal = function() {
        closeMusicModal(); closeContactModal(); closeUpdateLogModal(); closeBecomeFanModal();
        if (originalOpenLogin) originalOpenLogin();
    };
    window.openMusicModal = function() {
        closeLoginModal(); closeContactModal(); closeUpdateLogModal(); closeBecomeFanModal();
        if (originalOpenMusic) originalOpenMusic();
    };
    window.openContactModal = function() {
        closeLoginModal(); closeMusicModal(); closeUpdateLogModal(); closeBecomeFanModal();
        if (originalOpenContact) originalOpenContact();
    };
    window.openUpdateLogModal = function() {
        closeLoginModal(); closeMusicModal(); closeContactModal(); closeBecomeFanModal();
        if (originalOpenUpdateLog) originalOpenUpdateLog();
    };
    window.openBecomeFanModal = function() {
        closeLoginModal(); closeMusicModal(); closeContactModal(); closeUpdateLogModal();
        if (originalOpenBecomeFan) originalOpenBecomeFan();
    };
});
