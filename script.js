// Platform-specific installation commands database
const platformCommands = {
    termux: {
        step1: `pkg update -y && pkg install python git ripgrep termux-api -y\npython -m venv venv && source venv/bin/activate`,
        step2: `pip install aashoo-agent\npython -m aashoo.main --setup`,
        step3: `python -m aashoo.main`
    },
    unix: {
        step1: `# Install requirements (Debian/Ubuntu example)\nsudo apt update && sudo apt install -y python3 python3-venv git ripgrep\npython3 -m venv venv && source venv/bin/activate`,
        step2: `pip install aashoo-agent\npython3 -m aashoo.main --setup`,
        step3: `python3 -m aashoo.main`
    },
    windows: {
        step1: `# Ensure Python 3.9+ is installed\npython -m venv venv\nvenv\\Scripts\\Activate.ps1`,
        step2: `pip install aashoo-agent\npython -m aashoo.main --setup`,
        step3: `python -m aashoo.main`
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Menu Drawer Functionality
    const menuToggle = document.getElementById('menuToggle');
    const mobileDrawer = document.getElementById('mobileDrawer');
    
    if (menuToggle && mobileDrawer) {
        menuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            mobileDrawer.classList.toggle('open');
            menuToggle.classList.toggle('active');
            
            // Toggle hamburger icon animation
            const spans = menuToggle.querySelectorAll('span');
            if (mobileDrawer.classList.contains('open')) {
                spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(6px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });

        // Close drawer when clicking a link
        const drawerLinks = mobileDrawer.querySelectorAll('.drawer-link');
        drawerLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileDrawer.classList.remove('open');
                menuToggle.classList.remove('active');
                const spans = menuToggle.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            });
        });

        // Close drawer on clicking outside
        document.addEventListener('click', (e) => {
            if (!mobileDrawer.contains(e.target) && !menuToggle.contains(e.target)) {
                mobileDrawer.classList.remove('open');
                menuToggle.classList.remove('active');
                const spans = menuToggle.querySelectorAll('span');
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }

    // 2. Clipboard copy for Hero Pip command
    const copyBtn = document.getElementById('copyBtn');
    const pipCommand = document.getElementById('pipCommand');

    if (copyBtn && pipCommand) {
        copyBtn.addEventListener('click', () => {
            const commandText = pipCommand.textContent;
            navigator.clipboard.writeText(commandText).then(() => {
                const textNormal = copyBtn.querySelector('.copy-icon-txt');
                const textSuccess = copyBtn.querySelector('.success-icon-txt');
                
                textNormal.style.display = 'none';
                textSuccess.style.display = 'inline';
                copyBtn.style.borderColor = 'var(--success-color)';
                copyBtn.style.color = 'var(--success-color)';

                setTimeout(() => {
                    textNormal.style.display = 'inline';
                    textSuccess.style.display = 'none';
                    copyBtn.style.borderColor = '';
                    copyBtn.style.color = '';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        });
    }

    // 3. Dynamic Platform Tab Switcher
    const tabBtns = document.querySelectorAll('.tab-btn');
    const step1Code = document.getElementById('codeStep1');
    const step2Code = document.getElementById('codeStep2');
    const step3Code = document.getElementById('codeStep3');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active status from all tabs and assign to clicked one
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const platform = btn.getAttribute('data-platform');
            const commands = platformCommands[platform];

            if (commands) {
                // Fade out command content, switch text, then fade back in
                const codeBlocks = [step1Code, step2Code, step3Code];
                codeBlocks.forEach((block, index) => {
                    block.parentElement.style.opacity = 0.3;
                    setTimeout(() => {
                        if (index === 0) block.textContent = commands.step1;
                        if (index === 1) block.textContent = commands.step2;
                        if (index === 2) block.textContent = commands.step3;
                        block.parentElement.style.opacity = 1;
                    }, 150);
                });
            }
        });
    });

    // 4. Reveal Scroll Animations using IntersectionObserver
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target); // Trigger only once
            }
        });
    }, observerOptions);

    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach(el => revealObserver.observe(el));
});

// Helper function to copy command step blocks
function copyCode(elementId, btnElement) {
    const codeElement = document.getElementById(elementId);
    if (!codeElement) return;

    navigator.clipboard.writeText(codeElement.textContent).then(() => {
        const originalText = btnElement.textContent;
        btnElement.textContent = 'Copied!';
        btnElement.style.color = 'var(--success-color)';
        btnElement.style.borderColor = 'var(--success-color)';

        setTimeout(() => {
            btnElement.textContent = originalText;
            btnElement.style.color = '';
            btnElement.style.borderColor = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
}
