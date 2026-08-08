// ==========================================
// Agent 独立执行引擎（硬编码，绝不报错）
// ==========================================
(function() {
    window.AgentMacros = {};

    // 核心脚本 1：打开音乐并播放
    window.AgentMacros.MACRO_MUSIC_ON = async function() {
        // 【第一步】模拟真实点击右上角的音乐按钮！
        // 它会完美触发你原本写的 toggleMusicModal() 和 GSAP 动画，彻底解决卡片弹不出的问题
        const musicBtn = document.querySelector('.top-actions .top-btn:last-child');
        if (musicBtn) {
            musicBtn.click(); 
        } else {
            // 如果找不到按钮，走兜底
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.add('active');
        }

        // 【第二步】等待 500ms 让卡片弹窗动画完成
        await new Promise(r => setTimeout(r, 500));

        // 【第三步】尝试播放音频（如果被浏览器拦截，直接什么都不做，不报错）
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.play().catch(e => {});
        }
    };

    // 核心脚本 2：关闭音乐并关闭卡片
    window.AgentMacros.MACRO_MUSIC_OFF = async function() {
        // 先点击右上角按钮关闭（完美回退）
        const musicBtn = document.querySelector('.top-actions .top-btn:last-child');
        if (musicBtn) {
            musicBtn.click();
        } else {
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.remove('active');
        }

        // 暂停并重置音频
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }
    };

    // 其他宏保持不变...
    window.AgentMacros.MACRO_TOGGLE_FULLSCREEN = async function() {
        if (!document.fullscreenElement) document.documentElement.requestFullscreen();
        else if (document.exitFullscreen) document.exitFullscreen();
    };
    window.AgentMacros.MACRO_OPEN_LOG = async function() {
        document.getElementById('updateLogModal')?.classList.add('active');
    };
    window.AgentMacros.MACRO_OPEN_CONTACT = async function() {
        document.getElementById('contactModal')?.classList.add('active');
    };
    window.AgentMacros.MACRO_OPEN_DEVELOPER = async function() {
        document.getElementById('becomeFanModal')?.classList.add('active');
    };
})();
