// ==========================================
// Agent 独立执行引擎（直连核心，废弃物理点击）
// ==========================================
(function() {
    window.AgentMacros = {};

    // 核心脚本 1：打开音乐并播放
    window.AgentMacros.MACRO_MUSIC_ON = async function() {
        // 1. 直接调用你网页自带的弹出函数（彻底告别 querySelector）
        if (typeof window.openMusicModal === 'function') {
            window.openMusicModal();
        } else if (typeof window.toggleMusicModal === 'function') {
            // 如果你的打开逻辑是切换的，兜底调这个
            window.toggleMusicModal();
        } else {
            // 终极兜底：直接操控底层 DOM，100%绝对暴力开启
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.add('active');
        }

        // 2. 等待 500ms 让卡片动画完成
        await new Promise(r => setTimeout(r, 500));

        // 3. 直接播放音频
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.play().catch(e => console.log('播放被浏览器拦截', e));
        }
    };

    // 核心脚本 2：关闭音乐并关闭卡片
    window.AgentMacros.MACRO_MUSIC_OFF = async function() {
        // 1. 直接调用关闭函数
        if (typeof window.closeMusicModal === 'function') {
            window.closeMusicModal();
        } else if (typeof window.toggleMusicModal === 'function') {
            window.toggleMusicModal();
        } else {
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.remove('active');
        }

        // 2. 暂停并重置音频
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }
    };

    // 其他宏命令（全屏、日志等）
    window.AgentMacros.MACRO_TOGGLE_FULLSCREEN = async function() {
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else if (document.exitFullscreen) document.exitFullscreen();
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
