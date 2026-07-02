# 🚀 Aashoo AI Agent CLI

> **An open-source, lightweight AI Coding Agent that runs directly inside your terminal.**
> *Plan → Ask Permission → Execute → Remember → Repeat.*

Aashoo AI Agent CLI is a developer-first AI coding assistant that helps you build, edit, test, and manage software using natural language. It keeps you in complete control through a clear, permission-based execution model.

Designed to be **blazing fast**, **transparent**, **Git-aware**, and fully **Termux-compatible**, it brings the power of state-of-the-art AI agents to resource-constrained terminal environments.

---

## ✨ Features

- **🧠 Plan-First Workflow**: For complex requests, the agent generates a step-by-step markdown plan. You can approve, edit, or reject the plan before any tool starts.
- **🔒 Safety Permission System**: High-risk operations (e.g. modifying files, executing commands) require explicit approval (`Allow`, `Always Allow`, `Deny`, `Deny + Reason`, or `Stop Agent`). Low-risk tools (e.g. reading files, diffs) can run automatically.
- **🚀 Background Process Manager**: Easily start, list, stop, and inspect the logs of background servers (e.g. Flask, Django, Node.js) directly through the agent.
- **🌳 Git-Aware File Tree**: A real-time, git-status colored file tree refreshes automatically after changes.
- **📖 Precise Tools**: Includes file editors, line-by-line range reader/replacer, codebase keyword search, function outlines, test execution, and search.
- **🧠 Persistent SQLite Memory**: Remembers your project details, chat history, and always-allow permissions.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/AashooSharma/AashooAiAgentCLI.git
cd AashooAiAgentCLI
```

---

### 2. Platform-Specific Setup

#### 📱 Termux (Android Mobile)
Make sure your environment packages are updated and setup python/git:
```bash
# Update packages and install dependencies
pkg update -y
pkg install python git ripgrep termux-api -y

# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### 🐧 Linux & macOS
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

#### 🪟 Windows (Powershell)
```powershell
# Setup virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

---

### 3. API Key & Environment Setup

Copy the example environment file to create your own configuration:
```bash
# On Linux/macOS/Termux
cp example.env .env

# On Windows (PowerShell)
copy example.env .env
```

Open `.env` and fill in your keys (e.g. `GROQ_API_KEY`, `GOOGLE_API_KEY`, etc.). Alternatively, you can set them in your system environment variables.

---

## 🚀 Running the Agent

Start the agent CLI session:
```bash
python -m aashoo.main
```

To rerun the configuration/setup wizard at any time:
```bash
python -m aashoo.main --setup
```

---

## 💬 Supported Commands

Inside the agent session, you can use the following commands:
- `/help` — Show help listing of commands.
- `/clear` — Clear the console screen.
- `/tree` — Refresh and reprint the git-status file tree.
- `/history` — Show conversation history.
- `/undo` — Revert the last file modification made by the agent.
- `/bg` — List all active background processes.
- `/bg-stop <id>` — Stop the background process by its ID (e.g. `/bg-stop 1`).
- `/exit` or `exit` — Exit the active project session.

---

## 📁 Project Structure

```text
AashooAiAgentCLI/
│
├── aashoo/
│   ├── agent/
│   │   ├── loop.py         # Main agent loop logic & permission checks
│   │   ├── memory.py       # SQLite database queries & memory management
│   │   └── tools.py        # All built-in tools (file/cmd/search/bg tools)
│   │
│   ├── llm/
│   │   ├── base.py         # Abstract LLM client base
│   │   └── groq.py         # Groq LLM integration
│   │
│   ├── projects/
│   │   └── manager.py      # Project creator and manager
│   │
│   ├── ui/
│   │   ├── file_tree.py    # Git-aware file tree renderer
│   │   └── tui.py          # Terminal Panels and permission prompts
│   │
│   ├── setup_wizard.py     # Configuration setup wizard
│   └── main.py             # Entrypoint script
│
├── .gitignore
├── example.env             # Reference file for API keys configuration
├── LICENSE                 # MIT License
└── README.md               # Documentation
```

---

## 🔒 Safety First

Unlike fully autonomous agents that execute commands silently, Aashoo AI Agent puts **safety first**. High-risk actions (modifying files, running shell commands, stopping processes) will trigger a visual popup requesting permission. You can:
- **`[A] Allow`** to run the tool once.
- **`[!] Always Allow`** to white-list the tool for this project session.
- **`[D] Deny`** to skip the action. The agent will find an alternative.
- **`[R] Deny + Reason`** to reject and tell the agent why, so it changes course.
- **`[X] Stop Agent`** to abort the run entirely.

---

## 🤝 Contributing

We welcome contributions! Please open an issue or submit a pull request if you want to help improve the agent CLI.

## 📜 License

This project is licensed under the **MIT License**.
