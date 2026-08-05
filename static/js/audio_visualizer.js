/* 纯硬件加速，真实读取音频频谱驱动柱子（提升灵敏度版） */
document.addEventListener("DOMContentLoaded", function() {
    const audio = document.getElementById('bg-audio');
    const playBtn = document.getElementById('play-pause-btn');
    const bars = document.querySelectorAll('.volume-bars .bar');
    
    if (!audio || !bars.length) return;

    let audioCtx, analyser, dataArray;

    // 当用户点击播放时，初始化 Web Audio API
    function initAudioContext() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            
            // 核心修改 1：把 fftSize 从 64 提高到 128，让采样频段更细腻，低频响应更好
            analyser.fftSize = 128; 
            
            const source = audioCtx.createMediaElementSource(audio);
            source.connect(analyser);
            analyser.connect(audioCtx.destination);
            
            // frequencyBinCount 变成 64
            dataArray = new Uint8Array(analyser.frequencyBinCount);
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    // 实时渲染循环
    function renderFrame() {
        requestAnimationFrame(renderFrame);
        // 如果音频暂停或未初始化，跳过渲染
        if (audio.paused || !audioCtx || audioCtx.state !== 'running') return;

        // 提取音频频率数据
        analyser.getByteFrequencyData(dataArray);
        
        // 数据长度现在是 64，分配给 8 根柱子
        const step = Math.floor(dataArray.length / bars.length);
        for (let i = 0; i < bars.length; i++) {
            const value = dataArray[i * step];
            
            // 核心修改 2：原本除以 255 太迟钝了，改为除以 128，配合 3px 宽度，灵敏度和视觉重量刚刚好
            const height = Math.max(3, (value / 128) * 26); 
            bars[i].style.height = height + 'px';
        }
    }

    // 绑定点击播放
    playBtn.addEventListener('click', function() {
        initAudioContext(); // 确保开启音频上下文
        renderFrame();      // 启动频谱渲染循环
    });
});
