/* 极度灵敏测试版：专门用来测试柱子到底能不能动 */
document.addEventListener("DOMContentLoaded", function() {
    const audio = document.getElementById('bg-audio');
    const playBtn = document.getElementById('play-pause-btn');
    const bars = document.querySelectorAll('.volume-bars .bar');
    
    if (!audio || !bars.length) return;

    let audioCtx, analyser, dataArray, source;

    function initAudioContext() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 128; 
            if (!source) {
                source = audioCtx.createMediaElementSource(audio);
                source.connect(analyser);
                analyser.connect(audioCtx.destination);
            }
            dataArray = new Uint8Array(analyser.frequencyBinCount);
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    function renderFrame() {
        requestAnimationFrame(renderFrame);
        if (audio.paused || !audioCtx || audioCtx.state !== 'running') return;

        analyser.getByteFrequencyData(dataArray);
        
        const step = Math.floor(dataArray.length / bars.length);
        for (let i = 0; i < bars.length; i++) {
            const value = dataArray[i * step];
            
            // ★★★ 极度放大测试版 ★★★
            // 原来的除数除以90，现在改为除以 10。灵敏度直接拉满！
            let height = (value / 10) * 3; 
            
            // 打印原始数值到控制台（你在电脑上按F12就能看到）
            console.log(`第${i}根柱子的原始数值: ${value}`); 
            
            // 设置最低底线，并设置一个 50px 的最高极限（防止把卡片撑爆）
            height = Math.max(4, Math.min(50, height)); 
            
            bars[i].style.height = height + 'px';
        }
    }

    playBtn.addEventListener('click', function() {
        initAudioContext();
        renderFrame();      
    });
});
