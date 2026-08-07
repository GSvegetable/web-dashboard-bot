// ==========================================
// Agent 独立执行引擎（硬编码，绝不报错）
// ==========================================
(function() {
    // 注册宏命令容器
    window.AgentMacros = {};

    // ==========================================
    // 核心脚本 1：打开音乐并播放
    // ==========================================
    window.AgentMacros.MACRO_MUSIC_ON = async function() {
        // 第 1 步：打开音乐卡片
        if (typeof window.openMusicModal === 'function') {
            window.openMusicModal();
        } else {
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.add('active');
        }

        // 第 2 步：等待 300ms 让卡片动画弹出
        await new Promise(r => setTimeout(r, 300));

        // 第 3 步：直接播放音频
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.play().catch(e => console.log('播放被浏览器拦截', e));
        }
    };

    // ==========================================
    // 核心脚本 2：关闭音乐并关闭卡片
    // ==========================================
    window.AgentMacros.MACRO_MUSIC_OFF = async function() {
        const audio = document.getElementById('bg-audio');
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }

        if (typeof window.closeMusicModal === 'function') {
            window.closeMusicModal();
        } else {
            const modal = document.getElementById('musicModal');
            if (modal) modal.classList.remove('active');
        }
    };

    // 其他宏（全屏、日志等略...）
    // ...（这里暂不赘述，完整代码请参考上一轮回复）
})();
