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
        if (!section || !card1 || !card2 || !card3) return;
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
    window.addEventListener('load', updateCards);
    updateCards();
})();

// 🌙 水波纹夜晚模式切换（正确逻辑：先切主题，遮罩收缩露出新主题）
(function() {
    const toggleBtn = document.getElementById('night-mode-toggle');
    const ripple = document.getElementById('theme-ripple');
    if (!toggleBtn || !ripple) return;

    // 初始化：默认黑色（夜晚），如果本地存储标记为白天，则移除反色
    let isNight = localStorage.getItem('gsbot-night-mode') !== '0'; // 默认夜晚
    if (!isNight) {
        document.documentElement.classList.remove('night-mode');
    } else {
        document.documentElement.classList.add('night-mode');
    }

    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const currentIsNight = document.documentElement.classList.contains('night-mode');
        const nextIsNight = !currentIsNight;

        // 1. 立即切换底层主题
        document.documentElement.classList.toggle('night-mode', nextIsNight);
        localStorage.setItem('gsbot-night-mode', nextIsNight ? '1' : '0');

        // 2. 设置遮罩颜色 = 旧主题颜色（黑色或白色）
        //    当前是夜晚（黑色背景）→ 遮罩为黑色；当前是白天（白色背景）→ 遮罩为白色
        ripple.style.background = currentIsNight ? '#000' : '#fff';

        // 3. 初始遮罩完全覆盖屏幕（半径 150%），强制重绘
        ripple.style.clipPath = 'circle(150% at 50% 50%)';
        ripple.style.display = 'block';
        void ripple.offsetWidth;

        // 4. 收缩遮罩到 0，露出新主题
        ripple.style.clipPath = 'circle(0% at 50% 50%)';

        // 5. 动画结束后隐藏遮罩
        setTimeout(() => {
            ripple.style.display = 'none';
        }, 2100); // 2秒动画 + 0.1秒缓冲
    });
})();
