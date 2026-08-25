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

// 缓存viewport尺寸，避免频繁读取
let cachedVw = document.documentElement.clientWidth;
let cachedVh = document.documentElement.clientHeight;

function resizeDuplicate() {
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;

    const currentWidth = canvas.width;
    const currentHeight = canvas.height;

    if (currentWidth !== vw || currentHeight !== vh) {
        canvas.width = vw;
        canvas.height = vh;
        cachedVw = vw;
        cachedVh = vh;
    }
}

let animationFrameId = null;
let lastFrameTime = 0;
const frameInterval = 16.67; // ~60fps

function frame() {
    const now = performance.now();
    
    // 严格的帧率控制
    if (now - lastFrameTime < frameInterval) {
        animationFrameId = requestAnimationFrame(frame);
        return;
    }
    lastFrameTime = now;

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

    // 关键优化：使用缓存的viewport尺寸，减少DOM查询
    let vw = cachedVw;
    let vh = cachedVh;

    const rect = card.getBoundingClientRect();
    
    // 只在卡片在视口内时才更新
    if (rect.bottom < 0 || rect.top > vh) {
        // 卡片不在视口内，跳过绘制
        animationFrameId = requestAnimationFrame(frame);
        return;
    }

    container.style.left = `${-rect.left}px`;
    container.style.top = `${-rect.top}px`;
    container.style.width = `${vw}px`;
    container.style.height = `${vh}px`;

    try {
        // Reproduce CSS object-fit: cover for the video frame
        const cover = Math.max(vw / video.videoWidth, vh / video.videoHeight);
        const sw = vw / cover;
        const sh = vh / cover;
        const sx = (video.videoWidth - sw) / 2;
        const sy = (video.videoHeight - sh) / 2;

        // 使用 clearRect 前检查是否真的需要重绘
        ctx.clearRect(0, 0, vw, vh);
        ctx.drawImage(video, sx, sy, sw, sh, 0, 0, vw, vh);
    } catch (e) {
        // A frame may not be decodable yet; skip this cycle silently
    }
    
    animationFrameId = requestAnimationFrame(frame);
}

// 使用被动监听器和防抖处理窗口大小改变
let resizeTimeout = null;
function handleResize() {
    cachedVw = document.documentElement.clientWidth;
    cachedVh = document.documentElement.clientHeight;
    
    if (resizeTimeout) clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        resizeDuplicate();
    }, 100);
}

window.addEventListener('resize', handleResize, { passive: true });

// 初始化
resizeDuplicate();
frame();
