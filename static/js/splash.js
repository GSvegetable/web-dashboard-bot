// 确保DOM完全加载后再执行
document.addEventListener('DOMContentLoaded', function() {
    // ✅ 1. 汉堡菜单逻辑（彻底无干扰）
    const checkbox = document.getElementById('checkbox');
    const menu = document.getElementById('menu');
    const menuClose = document.getElementById('menu-close');
    const menuBackdrop = document.getElementById('menu-backdrop');
    const menuLinks = document.querySelectorAll('.menu__link');

    // 点击汉堡：切换菜单状态
    checkbox.addEventListener('change', function() {
        if (this.checked) {
            menu.classList.add('is-open');
        } else {
            menu.classList.remove('is-open');
        }
    });

    // 关闭按钮
    menuClose.addEventListener('click', function() {
        checkbox.checked = false;
        menu.classList.remove('is-open');
    });

    // 点击背景
    menuBackdrop.addEventListener('click', function() {
        checkbox.checked = false;
        menu.classList.remove('is-open');
    });

    // 点击菜单链接
    menuLinks.forEach(link => {
        link.addEventListener('click', function() {
            checkbox.checked = false;
            menu.classList.remove('is-open');
        });
    });

    // Esc关闭
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && menu.classList.contains('is-open')) {
            checkbox.checked = false;
            menu.classList.remove('is-open');
        }
    });

    // ✅ 2. 三张卡片滚动动画（逻辑不变）
    const section = document.getElementById('cardsSection');
    const card1 = document.getElementById('card1');
    const card2 = document.getElementById('card2');
    const card3 = document.getElementById('card3');
    if (section && card1 && card2 && card3) {
        const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
        const lerp = (a, b, t) => a + (b - a) * t;
        const easeOutCubic = (x) => 1 - Math.pow(1 - x, 3);

        function makeInitials() {
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            return {
                cX: 0, cY: vh * 0.55, cR: 0, cS: 0.82, cO: 0.5,
                lX: -vw * 0.45, lY: vh * 0.22, lR: -18, lS: 0.72, lO: 0.25,
                rX: vw * 0.45, rY: vh * 0.22, rR: 18, rS: 0.72, rO: 0.25
            };
        }

        let current = makeInitials();
        let target = makeInitials();
        let running = false;

        function updateTargets() {
            const rect = section.getBoundingClientRect();
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            const sectionCenter = rect.top + rect.height * 0.5;
            const offset = sectionCenter - vh * 0.5;
            const startDistance = vh * 0.85;
            const progress = clamp(1 - offset / startDistance, 0, 1);
            const t = easeOutCubic(progress);
            const distance = vw * 0.28;
            const ini = makeInitials();

            target.cX = 0;
            target.cY = lerp(ini.cY, 0, t);
            target.cR = 0;
            target.cS = lerp(ini.cS, 1, t);
            target.cO = lerp(ini.cO, 1, t);

            target.lX = lerp(ini.lX, -distance, t);
            target.lY = lerp(ini.lY, 0, t);
            target.lR = lerp(ini.lR, -6, t);
            target.lS = lerp(ini.lS, 1, t);
            target.lO = lerp(ini.lO, 1, t);

            target.rX = lerp(ini.rX, distance, t);
            target.rY = lerp(ini.rY, 0, t);
            target.rR = lerp(ini.rR, 6, t);
            target.rS = lerp(ini.rS, 1, t);
            target.rO = lerp(ini.rO, 1, t);
        }

        function apply() {
            card1.style.transform = `translate3d(${current.lX}px, ${current.lY}px, 0) translate(-50%, -50%) rotate(${current.lR}deg) scale(${current.lS})`;
            card2.style.transform = `translate3d(${current.cX}px, ${current.cY}px, 0) translate(-50%, -50%) rotate(${current.cR}deg) scale(${current.cS})`;
            card3.style.transform = `translate3d(${current.rX}px, ${current.rY}px, 0) translate(-50%, -50%) rotate(${current.rR}deg) scale(${current.rS})`;

            card1.style.opacity = current.lO;
            card2.style.opacity = current.cO;
            card3.style.opacity = current.rO;
        }

        function frame() {
            updateTargets();
            const keys = ['cX','cY','cR','cS','cO','lX','lY','lR','lS','lO','rX','rY','rR','rS','rO'];
            let delta = 0;
            for (const k of keys) {
                const old = current[k];
                current[k] = lerp(old, target[k], 0.09);
                delta += Math.abs(current[k] - old);
            }
            apply();
            if (delta > 0.001) {
                requestAnimationFrame(frame);
            } else {
                running = false;
            }
        }

        function start() {
            if (!running) {
                running = true;
                requestAnimationFrame(frame);
            }
        }

        window.addEventListener('scroll', start, { passive: true });
        window.addEventListener('resize', start);
        start();
    }

    // ✅ 3. 主题切换
    const toggleBtn = document.getElementById('night-mode-toggle');
    const blackLayer = document.getElementById('theme-bg-black');
    if (toggleBtn && blackLayer) {
        let isBlack = false;
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (isBlack) {
                blackLayer.style.clipPath = 'circle(0% at 48px 48px)';
                document.body.classList.remove('theme-black');
                isBlack = false;
            } else {
                blackLayer.style.clipPath = 'circle(0% at 48px 48px)';
                void blackLayer.offsetWidth;
                blackLayer.style.clipPath = 'circle(150% at 48px 48px)';
                document.body.classList.add('theme-black');
                isBlack = true;
            }
        });
    }
});
