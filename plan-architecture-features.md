# 🤖 AashooAiAgentCLI — Full Plan, Architecture & Features Document

> **Author:** Abhishek (Aashoo), BTech CSE Student, Jaipur  
> **GitHub:** [github.com/AashooSharma/AashooAiAgentCLI](https://github.com/AashooSharma/AashooAiAgentCLI)  
> **License:** MIT | **Status:** Active Development  
> **Version:** v0.1.0 (Pre-production)

---

## 📋 Table of Contents

1. [Project Vision](#-project-vision)
2. [Current Architecture](#-current-architecture)
3. [Module Breakdown](#-module-breakdown)
4. [What's Implemented (Fully Done)](#-whats-implemented-fully-done)
5. [Partially Implemented / Needs Improvement](#-partially-implemented--needs-improvement)
6. [What's Missing for Production](#-whats-missing-for-production)
7. [Feature Comparison with Competitors](#-feature-comparison-with-competitors)
8. [Roadmap to Production](#-roadmap-to-production)
9. [Tech Stack Reference](#-tech-stack-reference)

---

## 🎯 Project Vision

AashooAiAgentCLI is a **developer-first, terminal-native AI coding agent** that:

- Runs **anywhere** — Android Termux, Linux, macOS, Windows (no Docker, no cloud backend needed)
- Works with **any LLM provider** — Groq, Google, OpenAI, Anthropic, or local Ollama
- Follows a **Plan → Approve → Execute → Remember** lifecycle
- Uses a **fine-grained permission system** — not a black box that silently modifies your codebase
- Is **completely free and open source** (MIT License)

**The core differentiator:** Unlike all competitors, it runs natively on Android via Termux with no modifications required.

---

## 🏗️ Current Architecture

```
AashooAiAgentCLI/
│
├── aashoo/                         ← Main Python package
│   ├── main.py                     ← CLI entrypoint, menu system, chat loop
│   ├── setup_wizard.py             ← First-run interactive setup
│   │
│   ├── agent/                      ← Core intelligence layer
│   │   ├── loop.py                 ← Plan-first agent execution loop
│   │   ├── tools.py                ← All 19 tool definitions + schemas
│   │   └── memory.py               ← SQLite-based persistent memory
│   │
│   ├── llm/                        ← LLM provider abstraction layer
│   │   ├── base.py                 ← BaseLLM abstract class
│   │   ├── groq.py                 ← Groq (Llama) client
│   │   ├── google.py               ← Google Gemini client
│   │   ├── openai.py               ← OpenAI GPT client
│   │   ├── anthropic.py            ← Anthropic Claude client
│   │   └── ollama.py               ← Ollama local LLM client
│   │
│   ├── projects/
│   │   └── manager.py              ← Project create/open/clone logic
│   │
│   └── ui/
│       ├── tui.py                  ← Rich-based TUI: panels, permission prompts
│       ├── file_tree.py            ← Git-aware colored file tree
│       └── editor_server.py        ← Monaco Web Editor (zero-dependency HTTP server)
│
├── index.html                      ← Landing page
├── styles.css                      ← Landing page styles
├── script.js                       ← Landing page scripts
├── requirements.txt                ← Python dependencies
├── logo.txt                        ← ASCII art logos (random on startup)
├── example.env                     ← Environment variable example
└── README.md                       ← Documentation
```

### Data Flow

```
User Input (prompt_toolkit)
        │
        ▼
  main.py (chat loop)
        │
        ▼
  loop.py: _needs_plan()? ──Yes──► LLM: Generate Plan ──► tui.show_plan_approval()
        │                                                         │
        │                                              Approve/Edit/Reject
        │                                                         │
        └──────────────────────────────────────────────────────────┘
        │
        ▼
  loop.py: Agent Execution Loop (max 10 iterations)
        │
        ├── llm.chat(messages, tools=TOOLS_SCHEMA)
        │         │
        │         ▼
        │   response: content + tool_calls
        │         │
        │         ▼
        │   _check_permission() ──► tui.permission_prompt()
        │         │                      │
        │         │               Allow/Always/Deny/Stop
        │         │
        │         ▼
        │   AVAILABLE_FUNCTIONS[tool_name](**args)
        │         │
        │         ▼
        │   Result → messages → next LLM call
        │
        ▼
  memory.save_message() → SQLite
```

---

## 📦 Module Breakdown

### `aashoo/main.py` (467 lines)
- CLI entrypoint with `main()` function
- Random ASCII logo + rainbow colorizer on startup
- Main menu (New Project, Open Project, GitHub Clone, Settings, Exit)
- `start_agent_session()` — Full agent chat loop with:
  - `prompt_toolkit` multiline input (Enter = newline, **Ctrl+S = submit**)
  - Fallback to `rich.prompt.Prompt` if prompt_toolkit not installed
  - Background process status display in each loop iteration
  - All slash commands: `/help`, `/clear`, `/tree`, `/history`, `/undo`, `/bg`, `/bg-stop`, `/editor`, `/code`, `/switch`, `/exit`
  - Dynamic config switcher: `/switch` for provider/model/API key rotation at runtime
  - Settings menu

### `aashoo/setup_wizard.py` (248 lines)
- First-run 5-step interactive wizard
- Step 1: LLM provider selection (Groq, Google, OpenAI, Anthropic, Ollama)
- Step 2: Multiple API keys input (comma-separated, for rate-limit bypass)
- Step 3: Model selection from provider-specific list
- Step 4: Projects folder path configuration
- Step 5: Preferences (auto-allow low-risk tools)
- Config saved to `~/.aashoo/config.json`
- Config migration: old singular key → array key format

### `aashoo/agent/loop.py` (412 lines)
- System prompt in Hinglish (casual + technical English)
- Plan-first trigger detection via keywords + word count heuristic
- `_get_plan_from_llm()` — separate LLM call without tool access, returns only plan text
- Plan approval UI with 3 options: Approve, Edit (with feedback), Reject
- Agent execution loop (max 10 iterations) with:
  - Tool call parsing from LLM response
  - Permission checking + always-allow memory
  - Denied-tools tracking to prevent repeated requests
  - `__STOP_AGENT__` signal from user (X key)
  - Automatic `cwd` injection for git/command tools
  - File tree refresh after file-modifying tools

### `aashoo/agent/memory.py` (139 lines)
**SQLite DB at `~/.aashoo/memory.db` with 4 tables:**
- `projects` — registered projects (name, path, timestamps)
- `messages` — per-project conversation history (role, content, timestamp)
- `always_allow` — per-project tool always-allow whitelist
- `agent_notes` — key-value store for agent's own notes per project

### `aashoo/agent/tools.py` (987 lines)
**19 fully implemented tools:**

| Tool | Risk | Description |
|------|------|-------------|
| `read_file` | Low | Read file with line numbers, 6000 char limit |
| `write_file` | High | Create/overwrite file, auto-creates dirs, backup |
| `edit_file` | High | Diff-based partial edit (old_code → new_code) |
| `list_directory` | Low | Git-aware tree, respects `.agentignore` |
| `run_command` | High | Shell command, 60s timeout, 3000 char output |
| `git_status` | Low | `git status --short` |
| `git_diff` | Low | `git diff`, 4000 char limit |
| `git_commit` | High | Auto-stage all + commit |
| `web_search` | Low | DuckDuckGo API (no key needed) |
| `undo_last` | High | In-memory backup stack restore |
| `search_codebase` | Low | ripgrep first, Python fallback |
| `find_files` | Low | Glob pattern filename search |
| `read_file_lines` | Low | Specific line range read |
| `edit_file_lines` | High | Line-range replacement with backup |
| `get_file_outline` | Low | Extract class/function outline (Python, JS, TS) |
| `run_tests` | High | pytest/npm test wrapper |
| `start_background_process` | High | Non-blocking subprocess + log file |
| `list_background_processes` | Low | Status of all running bg processes |
| `stop_background_process` | High | Terminate/kill bg process by ID |
| `read_background_process_log` | Low | Tail log file of bg process |

### `aashoo/llm/` — LLM Abstraction Layer
- `base.py` — `BaseLLM` abstract class with `chat(messages, tools)` interface
- `groq.py` — Groq API (llama-3.3-70b-versatile, mixtral, gemma2, etc.)
- `google.py` — Google Gemini (1.5-pro, 1.5-flash, 2.0-flash-exp, etc.)
- `openai.py` — OpenAI GPT (gpt-4o, gpt-4o-mini, o1-preview, etc.)
- `anthropic.py` — Anthropic Claude (claude-3-5-sonnet, haiku, opus, etc.)
- `ollama.py` — Ollama local LLM (llama3, mistral, qwen2.5-coder, etc.)

### `aashoo/projects/manager.py` (253 lines)
- `create_project()` — create folder, optional git init, `.agentignore` template
- `open_project()` — list all projects in rich table, select by number
- `clone_github()` — git clone URL, auto-detect project name from URL
- Project metadata: name, path, git status, file count, last modified

### `aashoo/ui/tui.py` (223 lines)
- `print_user_message()` — cyan panel
- `print_agent_message()` — green panel with Markdown rendering
- `print_tool_call()` — yellow panel with JSON syntax highlighting
- `print_tool_result()` — dim panel, green for success, red for error
- `permission_prompt()` — A/!/D/R/X permission system
- `show_plan_approval()` — Y/E/N plan approval with feedback
- `print_command_help()` — full command list with multiline tip

### `aashoo/ui/file_tree.py`
- Git-aware file tree with color-coded status:
  - 🟢 Green — new/untracked files
  - 🟡 Yellow — modified files
  - 🔴 Red — deleted files
  - Gray — unchanged files
- Respects `.agentignore` and standard ignore patterns

### `aashoo/ui/editor_server.py` (19KB)
- Monaco Editor served via Python's built-in `http.server`
- Zero extra dependencies
- File browser + full Monaco editor in browser
- File read/write via HTTP endpoints
- Launches with `/editor` or `/code` command

---

## ✅ What's Implemented (Fully Done)

| Feature | Status | Notes |
|---------|--------|-------|
| **Multi-LLM support** | ✅ Done | Groq, Google, OpenAI, Anthropic, Ollama |
| **Multiple API key rotation** | ✅ Done | Comma-separated keys, bypass rate limits |
| **Dynamic /switch command** | ✅ Done | Switch provider/model/key mid-session |
| **Plan-first workflow** | ✅ Done | Keyword + word count heuristic triggers |
| **Plan approval UI** | ✅ Done | Approve / Edit (with feedback) / Reject |
| **Permission system** | ✅ Done | A/!/D/R/X per-tool permission + always-allow |
| **SQLite persistent memory** | ✅ Done | Per-project history, notes, always-allow |
| **19 agent tools** | ✅ Done | Full set including bg processes |
| **Background process manager** | ✅ Done | Start/list/stop/log bg servers |
| **Git integration** | ✅ Done | status, diff, commit (auto-stage) |
| **Git-aware file tree** | ✅ Done | Color-coded live tree |
| **Diff-based file editing** | ✅ Done | edit_file (old→new), edit_file_lines |
| **Undo last change** | ✅ Done | In-memory backup stack |
| **Web search** | ✅ Done | DuckDuckGo, no API key needed |
| **Monaco Web Editor** | ✅ Done | Zero-dependency browser-based editor |
| **GitHub clone from UI** | ✅ Done | Via projects manager |
| **Multi-line input** | ✅ Done | prompt_toolkit, Ctrl+S to submit |
| **Ripgrep fallback search** | ✅ Done | Falls back to Python rglob |
| **.agentignore support** | ✅ Done | Agent respects project-level ignore file |
| **Auto-allow low-risk tools** | ✅ Done | Configurable per session |
| **Denied-tool memory** | ✅ Done | Won't ask again for same denied action |
| **Config migration** | ✅ Done | Old single key → array key auto-migration |
| **Interactive setup wizard** | ✅ Done | 5-step first-run wizard |
| **Random ASCII logo** | ✅ Done | Random from logo.txt on each startup |
| **Landing page** | ✅ Done | index.html + styles.css + script.js |

---

## ⚠️ Partially Implemented / Needs Improvement

| Feature | Current State | What's Missing |
|---------|--------------|----------------|
| **Web search quality** | DuckDuckGo Instant Answer API only | Proper full-text web scraping results. DDG Instant Answer is often empty for coding queries |
| **get_file_outline** | Python + JS/TS basic detection | No support for Go, Rust, Java, C++ outlines. Uses string match, not AST |
| **run_command timeout** | Hard 60s limit | No streaming output — user sees nothing while it runs |
| **Ollama support** | File exists, basic structure | Needs testing and tool-call format verification |
| **Agent iteration limit** | MAX_ITERATIONS = 10 | No progress indicator, no "continue?" prompt when hitting limit |
| **Error handling in LLM** | Basic try/except | No retry logic, no exponential backoff on rate limits |
| **Permission system UX** | Single-character prompt | No visual diff preview before approving file edits |
| **Memory/history** | Last 30 messages loaded | No context summarization — will hit token limits on long sessions |
| **`/history` command** | Shows last 20 messages raw | No search, no export, no session labeling |
| **Plan heuristic** | Keyword match + word count | False positives and false negatives (simple questions can trigger plan) |
| **multiline input in Windows** | prompt_toolkit Ctrl+S | Ctrl+S may be intercepted by some Windows terminal emulators |

---

## 🚧 What's Missing for Production

### 🔴 Critical (must have before v1.0)

| Missing Feature | Why It Matters | Effort |
|-----------------|----------------|--------|
| **`pip install aashoo-agent` works** | Currently no `setup.py` or `pyproject.toml` — can't be published to PyPI | Medium |
| **`aashoo` CLI command (entry point)** | Users must run `python -m aashoo.main` — not ergonomic | Low |
| **Proper error messages and recovery** | If LLM API fails, app crashes silently. Need user-facing error with suggestion | Medium |
| **Token limit management** | On long sessions, message history will exceed context. Need sliding window + summarization | High |
| **Rate limit auto-rotate** | Currently user must `/switch` manually. Should auto-rotate to next key on 429 error | Medium |
| **Unit tests** | Zero test coverage. No CI pipeline | High |
| **Structured logging** | No debug/info logs for diagnosing production issues | Low |

### 🟡 Important (v1.0 quality)

| Missing Feature | Why It Matters | Effort |
|-----------------|----------------|--------|
| **Streaming LLM output** | All responses are blocking — user stares at spinner. Streaming text shows progress | High |
| **`/clear-history` command** | No way to reset conversation context to free up tokens | Low |
| **Agent notes tool** | `save_note`/`get_note` in memory.py exists but is never exposed as an agent tool | Low |
| **Better web search** | DuckDuckGo Instant Answer rarely returns useful coding results. Need SerpAPI/Brave Search | Medium |
| **Diff preview before edit** | Show user a visual diff before approving `edit_file` or `write_file` | Medium |
| **`/switch` model list refresh** | Model list is hardcoded in setup_wizard.py. Need dynamic fetching from provider | Low |
| **`.env` file support for API keys** | `example.env` exists but the wizard doesn't offer to read from `.env` automatically | Low |
| **Windows terminal compatibility** | Full testing needed on PowerShell and Windows Terminal for prompt_toolkit keybindings | Medium |

### 🟢 Nice to Have (v2.0 features)

| Missing Feature | Description | Effort |
|-----------------|-------------|--------|
| **Textual TUI** | `aashoo/ui/tui.py` has a comment: "Phase 2 mein Textual replace karega" — split-panel view | Very High |
| **MCP (Model Context Protocol) tools** | Plug-in external tools (browsers, databases, etc.) via MCP standard | Very High |
| **Agent memory search** | Semantic search over past conversations and notes | High |
| **Project templates** | `aashoo new --template flask-api` — scaffolded project starters | Medium |
| **Multi-file atomic edits** | Edit multiple files in a single "transaction" with all-or-nothing undo | High |
| **Voice input** | whisper.cpp or Termux microphone for mobile voice prompts | Very High |
| **Web UI** | Full React/Next.js dashboard for non-terminal users | Very High |
| **Plugin system** | Allow community-built tools beyond the built-in 19 | Very High |

---

## 📊 Feature Comparison with Competitors

| Feature | **AashooAgent** | **Claude Code** | **Antigravity (Google)** | **OpenCode** | **Aider** |
|---------|:-:|:-:|:-:|:-:|:-:|
| **Android / Termux support** | ✅ **Yes (USP)** | ❌ No | ❌ No | ❌ No | ⚠️ Limited |
| **100% Free & Open Source** | ✅ MIT | ❌ Billing required | ✅ Yes | ✅ Yes | ✅ MIT |
| **Zero network backend** | ✅ Yes | ❌ Requires Anthropic | ⚠️ Requires Google | ✅ Yes | ✅ Yes |
| **Local Ollama support** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Multi-LLM support** | ✅ 5 providers | ❌ Claude only | ⚠️ Google only | ✅ Multiple | ✅ Multiple |
| **Multi-API key rotation** | ✅ Built-in | ❌ No | ❌ No | ❌ No | ❌ No |
| **Plan-first workflow** | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Limited | ❌ No |
| **Interactive plan edit** | ✅ Yes | ❌ No | ⚠️ Partial | ❌ No | ❌ No |
| **Smart permission system** | ✅ A/!/D/R/X | ✅ Yes | ✅ Yes | ⚠️ Basic | ❌ No |
| **Always-allow memory** | ✅ Per-project SQLite | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Background process manager** | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| **Built-in Monaco Web Editor** | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| **Git-colored file tree** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Basic |
| **Git commit from agent** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Undo last change** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Web search (no key)** | ✅ DuckDuckGo | ✅ Yes | ✅ Yes | ⚠️ Optional | ⚠️ Optional |
| **Persistent memory per project** | ✅ SQLite | ✅ Yes | ✅ Yes | ⚠️ Session only | ❌ No |
| **Streaming output** | ❌ Not yet | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Test runner** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Multiline terminal input** | ✅ Ctrl+S | ⚠️ Varies | ⚠️ Varies | ⚠️ Varies | ❌ No |
| **PyPI installable** | ❌ Not yet | N/A | N/A | ✅ Yes | ✅ Yes |

### Key Differentiators Summary

**AashooAgent wins at:**
1. 📱 **Termux/Android** — absolute uniqueness, no competitor supports this
2. ⛓️ **Multi-key rate limit bypass** — comma-separate multiple API keys, auto-rotate
3. 🖥️ **Built-in Monaco Web Editor** — browser-based editor, zero extra install
4. 🔄 **Background process manager** — run Flask/Node servers without blocking
5. 🔒 **Deny + Reason** — give agent context WHY you denied, it adapts

**AashooAgent currently loses at:**
1. ⚡ **Streaming output** — all competitors stream; AashooAgent shows spinner
2. 📦 **PyPI package** — can't `pip install aashoo-agent` yet (no pyproject.toml)
3. 🧪 **Test coverage** — zero automated tests
4. 🌐 **Web search quality** — DuckDuckGo Instant Answer is very limited

---

## 🗺️ Roadmap to Production

### Phase 1 — PyPI Ready (Target: 2 weeks)
- [ ] Add `pyproject.toml` (or `setup.py`) with entry point `aashoo = aashoo.main:main`
- [ ] Publish to PyPI (`pip install aashoo-agent`)
- [ ] Add `aashoo` console script entry point
- [ ] Auto-rotate API key on 429 rate limit errors
- [ ] `/clear-history` command to reset context
- [ ] Expose `save_note`/`get_note` as agent tools

### Phase 2 — Production Quality (Target: 1 month)
- [ ] Streaming LLM output (all 5 providers)
- [ ] Context window management (sliding window + summarization)
- [ ] Unit tests for all tools (pytest)
- [ ] GitHub Actions CI pipeline
- [ ] Proper error messages with recovery suggestions
- [ ] Diff preview before approving file edits
- [ ] Better web search (Brave Search API or SerpAPI integration)
- [ ] Ollama full testing + tool-call format fix

### Phase 3 — Growth Features (Target: 2 months)
- [ ] Textual TUI split-panel view (code on left, agent on right)
- [ ] Project templates system (`--template` flag)
- [ ] Agent memory semantic search
- [ ] MCP (Model Context Protocol) plugin support
- [ ] Multi-file atomic transactions with full undo
- [ ] Windows Terminal full compatibility testing
- [ ] Community contribution guide + issue templates

---

## 🛠️ Tech Stack Reference

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| **TUI** | `rich` | ≥13.7.0 | Panels, tables, syntax highlighting, markdown |
| **Input** | `prompt_toolkit` | ≥3.0.0 | Multiline input, Ctrl+S to submit |
| **Groq** | `groq` | ≥0.9.0 | Llama models via Groq API |
| **Google** | `google-generativeai` | ≥0.8.0 | Gemini models |
| **OpenAI** | `openai` | ≥1.50.0 | GPT models |
| **Anthropic** | `anthropic` | ≥0.34.0 | Claude models |
| **Git** | `gitpython` | ≥3.1.40 | Git operations |
| **HTTP** | `requests` | ≥2.31.0 | Web search, API calls |
| **Config** | `python-dotenv` | ≥1.0.0 | `.env` file support |
| **DB** | `sqlite3` | Built-in | Persistent memory |
| **Web editor** | `http.server` | Built-in | Monaco editor backend |
| **Search** | `ripgrep` | System pkg | Fast codebase search |
| **Config file** | JSON | Built-in | `~/.aashoo/config.json` |
| **Memory DB** | SQLite | Built-in | `~/.aashoo/memory.db` |

---

## 📁 Config & Data Locations

| Location | Contents |
|----------|----------|
| `~/.aashoo/config.json` | Provider, API keys, model, preferences |
| `~/.aashoo/memory.db` | SQLite: projects, messages, always-allow, notes |
| `~/.aashoo/logs/bg_N.log` | Background process log files |
| `~/aashoo-projects/` | Default projects directory (configurable) |
| `<project>/.agentignore` | Agent-specific ignore patterns |

---

*Last updated: July 2026 | Generated by comprehensive codebase analysis*
