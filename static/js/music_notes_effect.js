document.addEventListener("DOMContentLoaded", function() {
    const audio = document.getElementById('bg-audio');
    if (!audio) return;

    // 创建画布
    const canvas = document.createElement('canvas');
    canvas.id = 'music-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none'; // 防止挡住点击
    canvas.style.zIndex = '5';
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    let width = window.innerWidth;
    let height = window.innerHeight;
    function resizeCanvas() {
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width;
        canvas.height = height;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // 音符池
    const NOTES_COUNT = 25; // 密度很低
    const symbols = ['♩', '♪', '♫', '♬']; // 音符形状

    class Note {
        constructor() {
            this.reset(true);
        }
        reset(init = false) {
            this.x = Math.random() * width;
            this.y = init ? Math.random() * height : -10 - Math.random() * 100;
            this.size = 10 + Math.random() * 8; // 音符很小
            this.speedY = 0.3 + Math.random() * 0.6; // 速度特别慢
            this.driftX = (Math.random() - 0.5) * 0.3; // 左右随机轻微飘动
            this.rotation = Math.random() * Math.PI * 2;
            this.rotationSpeed = (Math.random() - 0.5) * 0.03; // 慢慢左右旋转
            this.symbol = symbols[Math.floor(Math.random() * symbols.length)];
            this.opacity = 0.2 + Math.random() * 0.3;
        }
        update() {
            this.y += this.speedY;
            this.x += this.driftX;
            this.rotation += this.rotationSpeed;
            if (this.y > height + 20) {
                this.reset();
            }
            if (this.x < -20) this.x = width + 20;
            if (this.x > width + 20) this.x = -20;
        }
        draw() {
            ctx.save();
            ctx.translate(this.x, this.y);
            ctx.rotate(this.rotation);
            ctx.font = `${this.size}px Arial`;
            ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(this.symbol, 0, 0);
            ctx.restore();
        }
    }

    const notes = [];
    for (let i = 0; i < NOTES_COUNT; i++) {
        notes.push(new Note());
    }

    let isPlaying = false;
    let animFrameId = null;

    function animate() {
        if (!isPlaying) {
            // 如果暂停，依然维持画布干净，或者清空
            ctx.clearRect(0, 0, width, height);
            animFrameId = requestAnimationFrame(animate);
            return;
        }
        ctx.clearRect(0, 0, width, height);
        notes.forEach(note => {
            note.update();
            note.draw();
        });
        animFrameId = requestAnimationFrame(animate);
    }
    // 预启动动画循环（按需渲染）
    animate();

    // 监听音频的播放和暂停
    audio.addEventListener('play', () => {
        isPlaying = true;
    });
    audio.addEventListener('pause', () => {
        isPlaying = false;
    });
    audio.addEventListener('ended', () => {
        isPlaying = false;
    });
});
