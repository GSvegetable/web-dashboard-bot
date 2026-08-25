const video = document.getElementById('bg-video');
const card = document.querySelector('[data-glass-card]');
const container = document.getElementById('dup-video-container');
const canvas = document.getElementById('dup-image');
const ctx = canvas.getContext('2d', { willReadFrequently: false });

// Sizing the duplicate to the viewport rather than to the card is deliberate.
// The filter shifts each colour channel by a different amount, so the filtered
// element's own leading edges show hard channel-separation bands. At viewport
// size those bands fall outside the card and only clean refraction shows.
const DUP_PIXEL_RATIO = 1;

// 防抖和节流控制
let resizeTimeout = null;
let lastFrameTime = 0;
const frameInterval = 1000 / 60; // 60fps

function resizeDuplicate() {
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    const dpr = DUP_PIXEL_RATIO;

    const currentWidth = canvas.width;
    const currentHeight = canvas.height;

    if (currentWidth !== vw || currentHeight !== vh) {
        canvas.width = vw;
        canvas.height = vh;
    }
}

let animationFrameId = null;
let isFrameScheduled = false;

function frame() {
    const now = performance.now();
    
    // 节流帧渲染
    if (now - lastFrameTime < frameInterval) {
        if (!isFrameScheduled) {
            isFrameScheduled = true;
            animationFrameId = requestAnimationFrame(frame);
        }
        return;
    }
    lastFrameTime = now;
    isFrameScheduled = false;

    if (!card || !video) {
        animationFrameId = requestAnimationFrame(frame);
        return;
    }
    if (!card.offsetWidth || !card.offsetHeight) {
        animationFrameId = requestAnimationFrame(frame);
        return;
    }
    if (!video.videoWidth || !video.videoHeight) {
        animationFrameId = requestAnimationFrame(frame);
        return;
    }

    const rect = card.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;

    container.style.left = `${-rect.left}px`;
    container.style.top = `${-rect.top}px`;
    container.style.width = `${vw}px`;
    container.style.height = `${vh}px`;

    resizeDuplicate();

    try {
        // Reproduce CSS object-fit: cover for the video frame
        const cover = Math.max(vw / video.videoWidth, vh / video.videoHeight);
        const sw = vw / cover;
        const sh = vh / cover;
        const sx = (video.videoWidth - sw) / 2;
        const sy = (video.videoHeight - sh) / 2;

        ctx.drawImage(video, sx, sy, sw, sh, 0, 0, vw, vh);
    } catch (e) {
        // A frame may not be decodable yet; skip this cycle silently
    }
    
    animationFrameId = requestAnimationFrame(frame);
}

// 优化的窗口大小改变处理
function handleResize() {
    if (resizeTimeout) clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        resizeDuplicate();
        if (!isFrameScheduled) {
            isFrameScheduled = true;
            if (animationFrameId) cancelAnimationFrame(animationFrameId);
            animationFrameId = requestAnimationFrame(frame);
        }
    }, 100);
}

// 优化滑动性能：减少事件监听器
window.addEventListener('resize', handleResize, { passive: true });

// 启动动画循环
frame();
