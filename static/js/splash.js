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

// 🌙 背景图片扩散切换（完美逻辑，不再改）
(function() {
    const toggleBtn = document.getElementById('night-mode-toggle');
    const themeBg = document.getElementById('theme-bg');
    if (!toggleBtn || !themeBg) return;

    // 初始状态：图片隐藏（黑色背景）
    let isImageShown = false;

    toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        // 切换状态
        isImageShown = !isImageShown;

        // 核心：强制重绘后，改变 clip-path 触发 2 秒过渡动画
        if (isImageShown) {
            // 显示图片：从0扩散到150%
            themeBg.style.clipPath = 'circle(0% at 50% 50%)';
            void themeBg.offsetWidth; // 强制重绘
            themeBg.style.clipPath = 'circle(150% at 50% 50%)';
        } else {
            // 隐藏图片：从150%收缩到0%
            themeBg.style.clipPath = 'circle(150% at 50% 50%)';
            void themeBg.offsetWidth; // 强制重绘
            themeBg.style.clipPath = 'circle(0% at 50% 50%)';
        }
    });
})();
