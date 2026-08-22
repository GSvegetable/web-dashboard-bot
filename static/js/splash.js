// ==========================================
// 菜单逻辑（放在最外层，防止报错阻断后续）
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    const menu = document.getElementById('menu');
    const menuOpenBtn = document.getElementById('menu-open');
    const menuCloseBtn = document.getElementById('menu-close');
    const menuBackdrop = document.getElementById('menu-backdrop');
    const menuLinks = document.querySelectorAll('.menu__link');

    if (menu && menuOpenBtn && menuCloseBtn && menuBackdrop) {
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
    }
});

// ==========================================
// 三卡片滚动动画
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
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
});

// ==========================================
// 主题切换按钮（完美复刻原版扩散效果）
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
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

        const rect = toggleBtn.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        const currentIsNight = document.documentElement.classList.contains('night-mode');
        const nextIsNight = !currentIsNight;

        // 设置遮罩颜色 = 旧主题颜色
        ripple.style.background = currentIsNight ? '#000' : '#fff';

        // 从按钮位置扩散
        ripple.style.clipPath = `circle(0% at ${x}px ${y}px)`;
        ripple.style.display = 'block';

        // 强制重绘
        void ripple.offsetWidth;
        ripple.style.clipPath = `circle(150% at ${x}px ${y}px)`;

        // 在扩散中段切换主题
        setTimeout(() => {
            document.documentElement.classList.toggle('night-mode', nextIsNight);
            localStorage.setItem('gsbot-night-mode', nextIsNight ? '1' : '0');
        }, 400);

        // 动画结束后隐藏遮罩
        setTimeout(() => {
            ripple.style.display = 'none';
        }, 850);
    });
});
