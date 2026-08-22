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

// 🌙 完美复刻原版的夜晚模式切换（从按钮位置扩散）
(function() {
    const toggleBtn = document.getElementById('theme-toggle-btn');
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

        // 1. 获取按钮在屏幕上的精确坐标
        const rect = toggleBtn.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        const currentIsNight = document.documentElement.classList.contains('night-mode');
        const nextIsNight = !currentIsNight;

        // 2. 设置遮罩层颜色 = 旧主题颜色
        ripple.style.background = currentIsNight ? '#000' : '#fff';

        // 3. 把遮罩初始化为从按钮位置展开的 0% 圆
        ripple.style.clipPath = `circle(0% at ${x}px ${y}px)`;
        ripple.style.display = 'block';

        // 4. 强制重绘后，扩散到 150%（覆盖全屏）
        void ripple.offsetWidth;
        ripple.style.clipPath = `circle(150% at ${x}px ${y}px)`;

        // 5. 在扩散动画进行到一半时（0.4s）切换主题，产生原版“新背景从按钮蔓延”的效果
        setTimeout(() => {
            document.documentElement.classList.toggle('night-mode', nextIsNight);
            localStorage.setItem('gsbot-night-mode', nextIsNight ? '1' : '0');
        }, 400);

        // 6. 动画结束后隐藏遮罩
        setTimeout(() => {
            ripple.style.display = 'none';
        }, 850); // 与 0.8s 动画时长一致，稍加缓冲
    });
})();
