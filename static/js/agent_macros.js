// ==========================================
// Agent 独立执行引擎（硬编码，绝不报错）
// ==========================================
(function() {
    // 注册宏命令容器
    window.AgentMacros = {};

    // ==========================================
    // 核心脚本 1：打开音乐并播放（全流程固化）
    // ==========================================
    window.AgentMacros.MACRO_MUSIC_ON = async function() {
        // 第 1 步：打开音乐卡片
        if (typeof window.openMusicModal === 'function') {
            window.openMusicModal();
        } else {
            // 兜底：直接给 DOM 加类
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.add('active');
        }

        // 第 2 步：等待 300ms 让卡片动画弹出
        await new Promise(r => setTimeout(r, 300));

        // 第 3 步：直接播放音频
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.play().catch(e => {
                // 如果被浏览器拦截（通常发生在手机上），无需报错，等待用户手动点一下即可
                console.log('播放被浏览器拦截，等待用户手动触发', e);
            });
        }
    };

    // ==========================================
    // 核心脚本 2：关闭音乐并关闭卡片（全流程固化）
    // ==========================================
    window.AgentMacros.MACRO_MUSIC_OFF = async function() {
        // 第 1 步：停止音频并重置
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }

        // 第 2 步：关闭音乐卡片
        if (typeof window.closeMusicModal === 'function') {
            window.closeMusicModal();
        } else {
            // 兜底：直接移除 DOM 类
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.remove('active');
        }
    };

    // ==========================================
    // 扩展脚本：全屏、日志、联系我们、开发者（未来加功能只需在此扩充）
    // ==========================================
    window.AgentMacros.MACRO_TOGGLE_FULLSCREEN = async function() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    };

    window.AgentMacros.MACRO_OPEN_LOG = async function() {
        if (typeof window.openUpdateLogModal === 'function') {
            window.openUpdateLogModal();
        } else {
            document.getElementById('updateLogModal')?.classList.add('active');
        }
    };

    window.AgentMacros.MACRO_OPEN_CONTACT = async function() {
        if (typeof window.openContactModal === 'function') {
            window.openContactModal();
        } else {
            document.getElementById('contactModal')?.classList.add('active');
        }
    };

    window.AgentMacros.MACRO_OPEN_DEVELOPER = async function() {
        if (typeof window.openBecomeFanModal === 'function') {
            window.openBecomeFanModal();
        } else {
            document.getElementById('becomeFanModal')?.classList.add('active');
        }
    };
})();
