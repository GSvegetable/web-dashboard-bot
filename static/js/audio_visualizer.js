/* 纯硬件加速，真实读取音频频谱驱动柱子 */
document.addEventListener("DOMContentLoaded", function() {
    const audio = document.getElementById('bg-audio');
    const playBtn = document.getElementById('play-pause-btn');
    const bars = document.querySelectorAll('.volume-bars .bar');
    
    if (!audio || !bars.length) return;

    let audioCtx, analyser, dataArray;

    // 当用户点击播放时，初始化 Web Audio API（由于浏览器策略，必须在用户手势触发后初始化）
    function initAudioContext() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            // 降低 fftSize，让我们提取的 8 个柱子能够更灵敏地捕捉到频段
            analyser.fftSize = 64; 
            const source = audioCtx.createMediaElementSource(audio);
            source.connect(analyser);
            analyser.connect(audioCtx.destination);
            dataArray = new Uint8Array(analyser.frequencyBinCount);
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    // 实时渲染循环
    function renderFrame() {
        requestAnimationFrame(renderFrame);
        if (audio.paused || !audioCtx || audioCtx.state !== 'running') return;

        // 提取音频频率数据
        analyser.getByteFrequencyData(dataArray);
        
        // 数据长度是 32，我们按频率高低把它均分成 8 段分配给 8 根柱子
        const step = Math.floor(dataArray.length / bars.length);
        for (let i = 0; i < bars.length; i++) {
            // 提取频段数据并归一化高度 (柱子最大高度 26px，最小 4px)
            const value = dataArray[i * step];
            const height = Math.max(4, (value / 255) * 26); 
            bars[i].style.height = height + 'px';
        }
    }

    // 绑定点击播放
    playBtn.addEventListener('click', function() {
        initAudioContext(); // 确保开启音频上下文
        renderFrame();      // 启动频谱渲染循环
    });
});
