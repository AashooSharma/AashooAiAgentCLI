// 1. Terminal Simulation Database for Auto-typing Loop
const terminalData = {
  termux: {
    title: "termux — AashooAiAgentCLI",
    prompt: "$ ",
    steps: [
      { type: "input", text: "pkg update -y && pkg install python git ripgrep termux-api -y" },
      { type: "input", text: "git clone https://github.com/AashooSharma/AashooAiAgentCLI.git" },
      { type: "input", text: "cd AashooAiAgentCLI && python -m venv venv && source venv/bin/activate" },
      { type: "input", text: "pip install -r requirements.txt && python -m aashoo.main --setup" },
      { type: "input", text: "python -m aashoo.main" },
      { type: "output", text: "✓ Setup complete! Starting session..." },
      { type: "info", text: "You (Enter=newline, Ctrl+S=submit):" },
      { type: "prompt", text: "Build me a REST API for a todo app with Flask" }
    ]
  },
  linux: {
    title: "bash — AashooAiAgentCLI",
    prompt: "$ ",
    steps: [
      { type: "input", text: "git clone https://github.com/AashooSharma/AashooAiAgentCLI.git" },
      { type: "input", text: "cd AashooAiAgentCLI && python3 -m venv venv && source venv/bin/activate" },
      { type: "input", text: "pip install -r requirements.txt && python3 -m aashoo.main --setup" },
      { type: "input", text: "python3 -m aashoo.main" },
      { type: "output", text: "✓ Setup complete! Starting session..." },
      { type: "info", text: "You (Enter=newline, Ctrl+S=submit):" },
      { type: "prompt", text: "Build me a REST API for a todo app with Flask" }
    ]
  },
  macos: {
    title: "zsh — AashooAiAgentCLI",
    prompt: "$ ",
    steps: [
      { type: "input", text: "git clone https://github.com/AashooSharma/AashooAiAgentCLI.git" },
      { type: "input", text: "cd AashooAiAgentCLI && python3 -m venv venv && source venv/bin/activate" },
      { type: "input", text: "pip install -r requirements.txt && python3 -m aashoo.main --setup" },
      { type: "input", text: "python3 -m aashoo.main" },
      { type: "output", text: "✓ Setup complete! Starting session..." },
      { type: "info", text: "You (Enter=newline, Ctrl+S=submit):" },
      { type: "prompt", text: "Build me a REST API for a todo app with Flask" }
    ]
  },
  windows: {
    title: "PowerShell — AashooAiAgentCLI",
    prompt: "PS C:\\> ",
    steps: [
      { type: "input", text: "git clone https://github.com/AashooSharma/AashooAiAgentCLI.git" },
      { type: "input", text: "cd AashooAiAgentCLI; python -m venv venv; venv\\Scripts\\Activate.ps1" },
      { type: "input", text: "pip install -r requirements.txt; python -m aashoo.main --setup" },
      { type: "input", text: "python -m aashoo.main" },
      { type: "output", text: "✓ Setup complete! Starting session..." },
      { type: "info", text: "You (Enter=newline, Ctrl+S=submit):" },
      { type: "prompt", text: "Build me a REST API for a todo app with Flask" }
    ]
  }
};

document.addEventListener('DOMContentLoaded', () => {

  // Header Background Transition on Scroll
  const header = document.getElementById('siteHeader');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  });

  // Mobile Nav Hamburger Controls
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobileNav');

  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', (e) => {
      e.stopPropagation();
      mobileNav.classList.toggle('open');
      hamburger.classList.toggle('active');

      const spans = hamburger.querySelectorAll('span');
      if (mobileNav.classList.contains('open')) {
        spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
        spans[1].style.opacity = '0';
        spans[2].style.transform = 'rotate(-45deg) translate(6px, -6px)';
      } else {
        spans[0].style.transform = 'none';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'none';
      }
    });

    const mLinks = mobileNav.querySelectorAll('.mobile-nav-link');
    mLinks.forEach(link => {
      link.addEventListener('click', () => {
        mobileNav.classList.remove('open');
        hamburger.classList.remove('active');
        const spans = hamburger.querySelectorAll('span');
        spans[0].style.transform = 'none';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'none';
      });
    });

    document.addEventListener('click', (e) => {
      if (!mobileNav.contains(e.target) && !hamburger.contains(e.target)) {
        mobileNav.classList.remove('open');
        hamburger.classList.remove('active');
        const spans = hamburger.querySelectorAll('span');
        spans[0].style.transform = 'none';
        spans[1].style.opacity = '1';
        spans[2].style.transform = 'none';
      }
    });
  }

  // Installation Tabs Pane Switcher
  const tabButtons = document.querySelectorAll('.itab');
  const panels = document.querySelectorAll('.install-panel');

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const platform = btn.getAttribute('data-tab');
      const activePanel = document.querySelector(`.install-panel[data-panel="${platform}"]`);
      
      if (activePanel) {
        activePanel.classList.add('active');
      }
    });
  });

  // Reveal Animations on Scroll (Intersection Observer)
  const revealElements = document.querySelectorAll('.reveal');
  const revealOptions = {
    root: null,
    threshold: 0.05,
    rootMargin: '0px'
  };

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        obs.unobserve(entry.target);
      }
    });
  }, revealOptions);

  revealElements.forEach(el => observer.observe(el));

  // ═══════════════════════════════════════════════
  // TYPEWRITER SIMULATION CORE ENGINE
  // ═══════════════════════════════════════════════
  let currentOS = "termux";
  const osKeys = ["termux", "linux", "macos", "windows"];
  let currentOSIndex = 0;
  let animationTimeout = null;
  let isTyping = false;

  function typeWriter(osKey) {
    const terminalBody = document.getElementById("terminalBody");
    const terminalTitle = document.getElementById("terminalTitle");
    if (!terminalBody || !terminalTitle) return;

    // Reset timeouts
    if (animationTimeout) {
      clearTimeout(animationTimeout);
    }

    // Highlight active pill
    const pills = document.querySelectorAll("#heroPills .pill");
    pills.forEach(p => {
      if (p.getAttribute("data-os") === osKey) {
        p.classList.add("pill-highlight");
      } else {
        p.classList.remove("pill-highlight");
      }
    });

    const osData = terminalData[osKey];
    terminalTitle.textContent = osData.title;
    terminalBody.innerHTML = "";

    let stepIdx = 0;

    function runStep() {
      if (stepIdx >= osData.steps.length) {
        // Switch to the next OS pill automatically in 6 seconds
        animationTimeout = setTimeout(() => {
          currentOSIndex = (currentOSIndex + 1) % osKeys.length;
          currentOS = osKeys[currentOSIndex];
          typeWriter(currentOS);
        }, 6000);
        return;
      }

      const step = osData.steps[stepIdx];
      stepIdx++;

      // Automatically scroll to bottom of simulated terminal
      terminalBody.scrollTop = terminalBody.scrollHeight;

      if (step.type === "input" || step.type === "prompt") {
        const lineEl = document.createElement("p");
        if (step.type === "input") {
          lineEl.innerHTML = `<span class="t-dim">${osData.prompt}</span><span class="cmd-text"></span>`;
        } else {
          lineEl.innerHTML = `<span class="t-cyan">You</span> (Enter=newline, Ctrl+S=submit):<br/><span class="t-prompt"><span class="cmd-text"></span><span class="cursor">▌</span></span>`;
        }
        terminalBody.appendChild(lineEl);

        const cmdTextEl = lineEl.querySelector(".cmd-text");
        let charIdx = 0;

        function typeChar() {
          if (charIdx < step.text.length) {
            cmdTextEl.textContent += step.text.charAt(charIdx);
            charIdx++;
            terminalBody.scrollTop = terminalBody.scrollHeight;
            animationTimeout = setTimeout(typeChar, 18); // Typing Speed
          } else {
            if (step.type === "prompt") {
              const cursor = lineEl.querySelector(".cursor");
              if (cursor) cursor.style.display = 'none';
            }
            animationTimeout = setTimeout(runStep, 700); // Wait before next step
          }
        }
        typeChar();
      } else if (step.type === "output") {
        const lineEl = document.createElement("p");
        lineEl.className = "t-output";
        lineEl.textContent = step.text;
        terminalBody.appendChild(lineEl);
        terminalBody.scrollTop = terminalBody.scrollHeight;
        animationTimeout = setTimeout(runStep, 700);
      } else if (step.type === "info") {
        const lineEl = document.createElement("p");
        lineEl.className = "t-blink";
        lineEl.innerHTML = `<span class="t-cyan">You</span> (Enter=newline, Ctrl+S=submit):`;
        terminalBody.appendChild(lineEl);
        terminalBody.scrollTop = terminalBody.scrollHeight;
        animationTimeout = setTimeout(runStep, 700);
      }
    }

    runStep();
  }

  // Bind OS Pills Click triggers
  const pills = document.querySelectorAll("#heroPills .pill");
  pills.forEach((p, idx) => {
    p.addEventListener("click", () => {
      currentOSIndex = idx;
      currentOS = p.getAttribute("data-os");
      typeWriter(currentOS);
    });
  });

  // Start simulated terminal loop
  typeWriter("termux");
});

// Global Clipboard Copy Helper
function copyEl(elementId, buttonEl) {
  const codeNode = document.getElementById(elementId);
  if (!codeNode) return;

  const codeText = codeNode.textContent.trim();
  
  navigator.clipboard.writeText(codeText).then(() => {
    const originalText = buttonEl.textContent;
    buttonEl.textContent = 'Copied!';
    buttonEl.style.borderColor = 'var(--success)';
    buttonEl.style.color = 'var(--success)';

    setTimeout(() => {
      buttonEl.textContent = originalText;
      buttonEl.style.borderColor = '';
      buttonEl.style.color = '';
    }, 2000);
  }).catch(err => {
    console.error('Failed to copy: ', err);
  });
}
