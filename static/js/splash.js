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

// 🌙 水波纹夜晚模式切换（核心修正：先切主题，再遮罩扩散）
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
        e.preventDefault();
        e.stopPropagation();

        // 当前是白天，要切黑夜 => 遮罩颜色设为白色（白天背景色）
        // 当前是黑夜，要切白天 => 遮罩颜色设为黑色（夜晚背景色）
        const currentIsNight = document.documentElement.classList.contains('night-mode');
        ripple.style.background = currentIsNight ? '#000' : '#fff';
        
        // 遮罩初始半径0，位于点击位置（这里用中心点，因为按钮在中心）
        const x = e.clientX || window.innerWidth / 2;
        const y = e.clientY || window.innerHeight / 2;
        ripple.style.clipPath = `circle(0% at ${x}px ${y}px)`;
        ripple.style.display = 'block';

        // 强制重绘
        void ripple.offsetWidth;

        // 立即切换主题（此时底层已经变成新主题）
        document.documentElement.classList.toggle('night-mode', !currentIsNight);
        localStorage.setItem('gsbot-night-mode', (!currentIsNight) ? '1' : '0');

        // 让遮罩层扩散到最大，然后隐藏
        requestAnimationFrame(() => {
            ripple.style.clipPath = `circle(150% at ${x}px ${y}px)`;
        });

        setTimeout(() => {
            ripple.style.display = 'none';
        }, 650);
    });
})();
