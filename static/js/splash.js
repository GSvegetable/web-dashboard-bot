// 菜单逻辑
const menu = document.getElementById('menu');
const menuOpenBtn = document.getElementById('menu-open');
const menuCloseBtn = document.getElementById('menu-close');
const menuBackdrop = document.getElementById('menu-backdrop');
const menuLinks = document.querySelectorAll('.menu__link');

function setMenu(open) {
    menu.classList.toggle('is-open', open);
    menuOpenBtn.setAttribute('aria-expanded', String(open));
    if (open) {
        menuCloseBtn.focus({ preventScroll: true });
    } else {
        menuOpenBtn.focus({ preventScroll: true });
    }
}

menuOpenBtn.addEventListener('click', () => setMenu(true));
menuCloseBtn.addEventListener('click', () => setMenu(false));
menuBackdrop.addEventListener('click', () => setMenu(false));
menuLinks.forEach(link => {
    link.addEventListener('click', () => setMenu(false));
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('is-open')) {
        setMenu(false);
    }
});

// 三卡片滚动动画
(function() {
    const section = document.getElementById('cardsSection');
    const card1 = document.getElementById('card1');
    const card2 = document.getElementById('card2');
    const card3 = document.getElementById('card3');

    function easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    function updateCards() {
        const rect = section.getBoundingClientRect();
        const vh = window.innerHeight;
        let progress = (vh - rect.top) / (vh * 0.8);
        progress = Math.max(0, Math.min(1, progress));
        const eased = easeOutCubic(progress);

        const offset1 = Math.max(0, Math.min(1, (eased - 0.05) / 0.9));
        const offset2 = Math.max(0, Math.min(1, (eased - 0.15) / 0.9));
        const offset3 = Math.max(0, Math.min(1, (eased - 0.25) / 0.9));

        card1.style.transform = `translateX(${-150 * (1 - offset1)}px)`;
        card1.style.opacity = offset1;

        card2.style.transform = `translateY(${100 * (1 - offset2)}px)`;
        card2.style.opacity = offset2;

        card3.style.transform = `translateX(${150 * (1 - offset3)}px)`;
        card3.style.opacity = offset3;
    }

    window.addEventListener('scroll', updateCards, { passive: true });
    window.addEventListener('resize', updateCards);
    updateCards();
})();

// 🌙 水波纹夜晚模式切换
(function() {
    const toggleBtn = document.getElementById('night-mode-toggle');
    const ripple = document.getElementById('theme-ripple');
    if (!toggleBtn || !ripple) return;

    // 初始化夜晚模式状态
    let isNight = localStorage.getItem('gsbot-night-mode') === '1';
    if (isNight) {
        document.documentElement.classList.add('night-mode');
    }

    toggleBtn.addEventListener('click', function(e) {
        const x = e.clientX;
        const y = e.clientY;

        // 设置遮罩颜色：切黑夜用黑，切白天用白（因为反色后白变黑）
        ripple.style.background = isNight ? '#fff' : '#000';
        
        // 设置初始位置和大小（从点击点扩散）
        ripple.style.clipPath = `circle(0% at ${x}px ${y}px)`;
        ripple.style.display = 'block';
        
        // 强制重绘后开始动画
        void ripple.offsetWidth;
        
        // 扩散到全屏
        ripple.style.clipPath = `circle(150% at ${x}px ${y}px)`;

        // 动画结束后切换主题并隐藏遮罩
        ripple.addEventListener('transitionend', function handler() {
            ripple.removeEventListener('transitionend', handler);
            
            // 先隐藏遮罩，再切换类（避免遮罩被全局反色影响）
            ripple.style.display = 'none';
            
            // 切换状态
            isNight = !isNight;
            document.documentElement.classList.toggle('night-mode', isNight);
            localStorage.setItem('gsbot-night-mode', isNight ? '1' : '0');
        });
    });
})();
