/* 修复版：解决重复创建音频源导致崩溃的问题 */
document.addEventListener("DOMContentLoaded", function() {
    const audio = document.getElementById('bg-audio');
    const playBtn = document.getElementById('play-pause-btn');
    const bars = document.querySelectorAll('.volume-bars .bar');
    
    if (!audio || !bars.length) return;

    let audioCtx, analyser, dataArray, source; // 把 source 提升到全局，防止重复创建

    // 当用户点击播放时，初始化 Web Audio API
    function initAudioContext() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioCtx.createAnalyser();
            analyser.fftSize = 128; 
            
            // ✅ 修复核心：如果 source 已经创建过了，绝不重复创建！
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

    // 实时渲染循环
    function renderFrame() {
        requestAnimationFrame(renderFrame);
        if (audio.paused || !audioCtx || audioCtx.state !== 'running') return;

        analyser.getByteFrequencyData(dataArray);
        
        const step = Math.floor(dataArray.length / bars.length);
        for (let i = 0; i < bars.length; i++) {
            const value = dataArray[i * step];
            
            // ✅ 再次放宽阈值：以前 /128，现在改为 /90，同时加上最小值 4px。
            // 这样哪怕是音量极小的纯音乐，也会瞬间拉高柱子，灵敏度拉到顶！
            const height = Math.max(4, (value / 90) * 28); 
            bars[i].style.height = height + 'px';
        }
    }

    // 绑定点击播放
    playBtn.addEventListener('click', function() {
        initAudioContext(); // 现在这个函数无论点多少次都不会崩溃了
        renderFrame();      
    });
});
