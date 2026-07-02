"""
Sab tools — agent loop inhe call karega.
10 tools + TOOLS_SCHEMA + risk levels.
"""

import os
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

import requests


# ============================================================
# PROJECT CONTEXT — agent loop yahan set karega
# ============================================================
_current_project_path: str = "."

def set_project_context(path: str):
    """Agent loop is function se project path set karega."""
    global _current_project_path
    _current_project_path = path

def _resolve_path(path: str) -> str:
    """
    Relative path ko project path ke saath resolve karo.
    Agar already absolute hai to waise hi rakho.
    """
    from pathlib import Path
    p = Path(path)
    if p.is_absolute():
        return str(p)
    # Project folder ke andar resolve karo
    return str(Path(_current_project_path) / p)

# ============================================================
# RISK LEVELS
# low  → auto-allow (agar config mein auto_allow_low_risk=True)
# high → hamesha permission maango
# ============================================================
TOOL_RISK = {
    "read_file":                  "low",
    "list_directory":             "low",
    "web_search":                 "low",
    "edit_file":                  "high",
    "write_file":                 "high",
    "run_command":                "high",
    "git_status":                 "low",
    "git_diff":                   "low",
    "git_commit":                 "high",
    "undo_last":                  "high",
    "search_codebase":            "low",
    "find_files":                 "low",
    "read_file_lines":            "low",
    "edit_file_lines":            "high",
    "get_file_outline":           "low",
    "run_tests":                  "high",
    "start_background_process":   "high",
    "list_background_processes":  "low",
    "stop_background_process":    "high",
    "read_background_process_log": "low",
}

TOOL_ICONS = {
    "read_file":                  "📄",
    "list_directory":             "📁",
    "web_search":                 "🌐",
    "edit_file":                  "✏️",
    "write_file":                 "💾",
    "run_command":                "⚡",
    "git_status":                 "📊",
    "git_diff":                   "🔍",
    "git_commit":                 "📦",
    "undo_last":                  "↩️",
    "search_codebase":            "🔍",
    "find_files":                 "📂",
    "read_file_lines":            "📖",
    "edit_file_lines":            "📝",
    "get_file_outline":           "🗂️",
    "run_tests":                  "🧪",
    "start_background_process":   "🚀",
    "list_background_processes":  "📋",
    "stop_background_process":    "🛑",
    "read_background_process_log": "📰",
}

# Backup store karne ke liye (undo ke liye)
_backup_stack: list[dict] = []


# ============================================================
# TOOL FUNCTIONS
# ============================================================

def read_file(path: str) -> str:
    try:
        resolved = _resolve_path(path)  # ← yeh add karo
        content = Path(resolved).read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        # Line numbers ke saath dikhao (agent ko context milta hai)
        numbered = "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
        return f"[{len(lines)} lines]\n{numbered}"[:6000]
    except Exception as e:
        return f"Error: {e}"


def write_file(path: str, content: str) -> str:
    try:
        resolved = _resolve_path(path)  # ← yeh add karo
        p = Path(resolved)
        # Backup pehle
        if p.exists():
            _backup_stack.append({
                "type": "write",
                "path": str(p),
                "original": p.read_text(encoding="utf-8", errors="replace"),
                "timestamp": datetime.now().isoformat(),
            })
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✓ '{path}' likh diya ({len(content)} chars, {len(content.splitlines())} lines)"
    except Exception as e:
        return f"Error: {e}"


def edit_file(path: str, old_code: str, new_code: str) -> str:
    """Diff-based partial edit — sirf changed part replace karo."""
    try:
        resolved = _resolve_path(path)  # ← yeh add karo
        p = Path(resolved)
        if not p.exists():
            return f"Error: '{path}' exist nahi karta"

        content = p.read_text(encoding="utf-8", errors="replace")

        if old_code not in content:
            return (
                f"Error: old_code text file mein exact match nahi hua.\n"
                f"Tip: read_file se content dekho phir sahi old_code do."
            )

        count = content.count(old_code)
        if count > 1:
            return f"Error: old_code {count} jagah match hua — unique text do."

        # Backup
        _backup_stack.append({
            "type": "edit",
            "path": str(p),
            "original": content,
            "timestamp": datetime.now().isoformat(),
        })

        new_content = content.replace(old_code, new_code, 1)
        p.write_text(new_content, encoding="utf-8")

        old_lines = len(old_code.splitlines())
        new_lines = len(new_code.splitlines())
        return f"✓ '{path}' edit hua ({old_lines} lines → {new_lines} lines)"

    except Exception as e:
        return f"Error: {e}"


def list_directory(path: str = ".") -> str:
    """Git-aware directory listing."""
    try:
        # path nahi diya ya "." hai to project folder use karo
        if not path or path in (".", "./", ""):
            resolved = _current_project_path
        else:
            resolved = _resolve_path(path)  # ← yeh add karo
        p = Path(resolved)
        if not p.exists():
            return f"Error: '{path}' exist nahi karta"

        # .agentignore load karo
        ignore_patterns = {
            "__pycache__", ".git", "venv", "node_modules",
            ".DS_Store", "*.pyc", "*.log"
        }
        agentignore = p / ".agentignore"
        if agentignore.exists():
            for line in agentignore.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    ignore_patterns.add(line.rstrip("/"))

        def should_ignore(name: str) -> bool:
            if name in ignore_patterns:
                return True
            for pat in ignore_patterns:
                if pat.startswith("*") and name.endswith(pat[1:]):
                    return True
            return False

        lines = []
        def walk(folder: Path, prefix: str = ""):
            try:
                items = sorted(folder.iterdir(),
                               key=lambda x: (x.is_file(), x.name))
            except PermissionError:
                return
            for i, item in enumerate(items):
                if should_ignore(item.name):
                    continue
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                if item.is_dir():
                    lines.append(f"{prefix}{connector}[{item.name}/]")
                    walk(item, prefix + ("    " if is_last else "│   "))
                else:
                    size = item.stat().st_size
                    size_str = f"{size}B" if size < 1024 else f"{size//1024}KB"
                    lines.append(f"{prefix}{connector}{item.name} ({size_str})")
                if len(lines) > 200:
                    lines.append("... (truncated)")
                    return

        lines.append(f"[{p.name}/]")
        walk(p)
        return "\n".join(lines)

    except Exception as e:
        return f"Error: {e}"


def run_command(command: str, cwd: str = None) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
        )
        output = result.stdout + result.stderr
        output = output.strip()
        if not output:
            output = f"(exit code: {result.returncode}, no output)"
        return output[:3000]
    except subprocess.TimeoutExpired:
        return "Error: Command timeout (60s)"
    except Exception as e:
        return f"Error: {e}"


def git_status(cwd: str = ".") -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=cwd
        )
        if result.returncode != 0:
            return "Git repo nahi hai ya git install nahi."
        output = result.stdout.strip()
        return output if output else "Working tree clean — koi changes nahi."
    except Exception as e:
        return f"Error: {e}"


def git_diff(cwd: str = ".") -> str:
    try:
        result = subprocess.run(
            ["git", "diff"],
            capture_output=True, text=True, cwd=cwd
        )
        output = result.stdout.strip()
        return output[:4000] if output else "Koi diff nahi."
    except Exception as e:
        return f"Error: {e}"


def git_commit(message: str, cwd: str = ".") -> str:
    try:
        # Stage all
        subprocess.run(["git", "add", "-A"], cwd=cwd, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True, text=True, cwd=cwd
        )
        output = (result.stdout + result.stderr).strip()
        return output[:1000]
    except Exception as e:
        return f"Error: {e}"


def web_search(query: str) -> str:
    """DuckDuckGo instant answer API — no key needed."""
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            },
            timeout=10,
            headers={"User-Agent": "aashoo-agent/0.1"},
        )
        data = resp.json()

        results = []
        if data.get("AbstractText"):
            results.append(f"Summary: {data['AbstractText']}")
        if data.get("Answer"):
            results.append(f"Answer: {data['Answer']}")
        for r in data.get("RelatedTopics", [])[:4]:
            if isinstance(r, dict) and r.get("Text"):
                results.append(f"• {r['Text'][:200]}")

        return "\n".join(results) if results else "Koi result nahi mila."

    except Exception as e:
        return f"Search error: {e}"


def undo_last() -> str:
    """Last file change revert karo."""
    if not _backup_stack:
        return "Koi backup nahi hai — undo nahi ho sakta."

    backup = _backup_stack.pop()
    try:
        Path(backup["path"]).write_text(
            backup["original"], encoding="utf-8"
        )
        return (
            f"✓ Undo hua: '{backup['path']}' "
            f"({backup['type']} at {backup['timestamp'][:19]})"
        )
    except Exception as e:
        return f"Undo error: {e}"


def search_codebase(query: str, path: str = None, file_pattern: str = "*") -> str:
    """Puri codebase mein text/keyword search."""
    import subprocess
    from pathlib import Path
    
    search_path = path or _current_project_path
    
    # ripgrep check karo pehle
    try:
        result = subprocess.run(
            ["rg", "--line-number", "--with-filename", "--max-count", "5", query, search_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode in (0, 1):
            return result.stdout[:3000] or "Koi match nahi mila."
    except FileNotFoundError:
        pass
    
    # Fallback: Python se manual search
    results = []
    base = Path(search_path)
    for f in base.rglob(file_pattern):
        if any(part in f.parts for part in (".git", "venv", "node_modules", "__pycache__")):
            continue
        if not f.is_file():
            continue
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            for i, line in enumerate(lines, 1):
                if query.lower() in line.lower():
                    results.append(f"{f.relative_to(base)}:{i}: {line.strip()}")
                    if len(results) >= 50:
                        break
            if len(results) >= 50:
                break
        except Exception:
            continue
    
    return "\n".join(results) if results else "Koi match nahi mila."


def find_files(pattern: str, path: str = None) -> str:
    """File name pattern search (e.g. *.py, index.html)"""
    from pathlib import Path
    search_path = path or _current_project_path
    base = Path(search_path)
    results = []
    
    for f in base.rglob(pattern):
        if any(part in f.parts for part in (".git", "venv", "node_modules", "__pycache__")):
            continue
        if f.is_file():
            try:
                rel = f.relative_to(base)
                results.append(str(rel))
            except ValueError:
                results.append(str(f))
        if len(results) >= 100:
            results.append("... (truncated)")
            break
            
    return "\n".join(results) if results else "Koi file nahi mili."


def read_file_lines(path: str, start_line: int = 1, end_line: int = None) -> str:
    """Specific line range padhna."""
    try:
        resolved = _resolve_path(path)
        lines = Path(resolved).read_text(encoding="utf-8", errors="replace").splitlines()
        
        total = len(lines)
        end = end_line or total
        start = max(1, start_line)
        end = min(total, end)
        
        selected = lines[start-1:end]
        numbered = "\n".join(f"{i+start:4d} | {line}" for i, line in enumerate(selected))
        return f"[Lines {start}-{end} of {total} — {resolved}]\n{numbered}"
    except Exception as e:
        return f"Error: {e}"


def edit_file_lines(path: str, start_line: int, end_line: int, new_content: str) -> str:
    """Specific line range replace karo."""
    try:
        resolved = _resolve_path(path)
        p = Path(resolved)
        if not p.exists():
            return f"Error: '{path}' exist nahi karta"
        
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        total_lines = len(lines)
        if start_line < 1 or start_line > total_lines or end_line < 1 or end_line > total_lines or start_line > end_line:
            return f"Error: Invalid line range {start_line}-{end_line} for file with {total_lines} lines."

        # Backup
        _backup_stack.append({
            "type": "edit_lines",
            "path": resolved,
            "original": "".join(lines),
            "timestamp": datetime.now().isoformat(),
        })
        
        new_lines = new_content.splitlines(keepends=True)
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] = new_lines[-1] + "\n"
        
        result_lines = lines[:start_line-1] + new_lines + lines[end_line:]
        p.write_text("".join(result_lines), encoding="utf-8")
        return f"✓ Lines {start_line}-{end_line} replace hue → {len(new_lines)} new lines"
    except Exception as e:
        return f"Error: {e}"


def get_file_outline(path: str) -> str:
    """File mein defined classes aur functions ka outline dikhata hai."""
    try:
        resolved = _resolve_path(path)
        p = Path(resolved)
        if not p.exists():
            return f"Error: '{path}' exist nahi karta"
        
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        outline = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if p.suffix == ".py":
                if stripped.startswith("def ") or stripped.startswith("class "):
                    indent = len(line) - len(line.lstrip())
                    outline.append(f"{i:4d} | {' ' * indent}{stripped}")
            elif p.suffix in (".js", ".ts"):
                if "function " in stripped or "class " in stripped or (stripped.startswith("const ") and "=>" in stripped):
                    indent = len(line) - len(line.lstrip())
                    outline.append(f"{i:4d} | {' ' * indent}{stripped}")
            else:
                if stripped.startswith("class ") or stripped.startswith("def ") or stripped.startswith("function "):
                    indent = len(line) - len(line.lstrip())
                    outline.append(f"{i:4d} | {' ' * indent}{stripped}")
                    
        return "\n".join(outline) if outline else "Outline nahi mila ya unsupported file type."
    except Exception as e:
        return f"Error: {e}"


def run_tests(command: str) -> str:
    """Tests command run karta hai project folder mein (pytest, npm test etc.)."""
    return run_command(command, cwd=_current_project_path)


_bg_processes: dict[int, dict] = {}
_bg_counter = 1

def start_background_process(command: str) -> str:
    """Shell/terminal command ko background mein run karta hai (jaise server start karna)."""
    global _bg_counter
    import time
    try:
        log_dir = Path.home() / ".aashoo" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"bg_{_bg_counter}.log"
        
        # open file for log redirection
        f = open(log_file, "w", encoding="utf-8", errors="replace")
        
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=_current_project_path,
            stdout=f,
            stderr=f,
            text=True
        )
        
        # wait a little bit to check if it crashed immediately
        time.sleep(0.5)
        poll_status = proc.poll()
        if poll_status is not None:
            f.close()
            # Read whatever log was created
            log_content = log_file.read_text(encoding="utf-8", errors="replace")
            return (
                f"Error: Process immediately exited with code {poll_status}.\n"
                f"Log content:\n{log_content}"
            )
            
        _bg_processes[_bg_counter] = {
            "proc": proc,
            "command": command,
            "start_time": start_time,
            "log_file": str(log_file),
            "file_obj": f,
        }
        
        res = (
            f"✓ Background process start ho gayi:\n"
            f"  ID: [{_bg_counter}]\n"
            f"  PID: {proc.pid}\n"
            f"  Command: {command}\n"
            f"  Log file: {log_file}\n"
            f"Tip: 'read_background_process_log' se iske outputs check karo."
        )
        _bg_counter += 1
        return res
    except Exception as e:
        return f"Error background process start karne mein: {e}"


def list_background_processes() -> str:
    """Sari background running processes ki list aur status dikhata hai."""
    if not _bg_processes:
        return "Koi background process running nahi hai."
        
    lines = []
    # Clean up exited processes first or mark them
    for bid, pinfo in list(_bg_processes.items()):
        proc = pinfo["proc"]
        poll_status = proc.poll()
        status = "Running" if poll_status is None else f"Exited ({poll_status})"
        lines.append(
            f"[{bid}] PID {proc.pid}: {pinfo['command']}\n"
            f"    Status: {status}\n"
            f"    Started: {pinfo['start_time']}\n"
            f"    Log: {pinfo['log_file']}"
        )
    return "\n".join(lines)


def stop_background_process(process_id: int) -> str:
    """Running background process ko terminate/kill karta hai."""
    if process_id not in _bg_processes:
        return f"Error: Background process ID [{process_id}] nahi mili."
        
    pinfo = _bg_processes[process_id]
    proc = pinfo["proc"]
    
    try:
        poll_status = proc.poll()
        if poll_status is not None:
            if "file_obj" in pinfo:
                try:
                    pinfo["file_obj"].close()
                except:
                    pass
            del _bg_processes[process_id]
            return f"✓ Process [{process_id}] already exited with code {poll_status}."
            
        # Terminate
        proc.terminate()
        for _ in range(20):
            import time
            time.sleep(0.1)
            if proc.poll() is not None:
                break
        else:
            proc.kill()
            
        if "file_obj" in pinfo:
            try:
                pinfo["file_obj"].close()
            except:
                pass
                
        del _bg_processes[process_id]
        return f"✓ Background process [{process_id}] (PID {proc.pid}) ko stop/kill kar diya."
    except Exception as e:
        return f"Error stopping process [{process_id}]: {e}"


def read_background_process_log(process_id: int, lines: int = 50) -> str:
    """Background process ke log file ka output read karta hai."""
    if process_id not in _bg_processes:
        log_file = Path.home() / ".aashoo" / "logs" / f"bg_{process_id}.log"
        if not log_file.exists():
            return f"Error: Background process ID [{process_id}] ya log file nahi mili."
    else:
        log_file = Path(_bg_processes[process_id]["log_file"])
        
    try:
        if process_id in _bg_processes and "file_obj" in _bg_processes[process_id]:
            try:
                _bg_processes[process_id]["file_obj"].flush()
            except:
                pass
                
        content = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        total = len(content)
        selected = content[-lines:]
        selected_content = "\n".join(selected)
        return (
            f"[Log for process ID [{process_id}] — Last {len(selected)} lines of {total}]\n"
            f"{selected_content}"
        )
    except Exception as e:
        return f"Error reading log for process [{process_id}]: {e}"


def get_active_processes_list() -> list[dict]:
    """Active running processes ki minimal list return karta hai UI display ke liye."""
    active = []
    for bid, pinfo in list(_bg_processes.items()):
        proc = pinfo["proc"]
        poll_status = proc.poll()
        if poll_status is None:
            active.append({
                "id": bid,
                "pid": proc.pid,
                "command": pinfo["command"],
                "start_time": pinfo["start_time"],
            })
        else:
            if "file_obj" in pinfo:
                try:
                    pinfo["file_obj"].close()
                except:
                    pass
    return active


def cleanup_background_processes():
    """CLI exit hone par sab background running processes ko clean up aur kill karo."""
    if not _bg_processes:
        return
        
    for bid, pinfo in list(_bg_processes.items()):
        proc = pinfo["proc"]
        if proc.poll() is None:
            try:
                proc.terminate()
                if "file_obj" in pinfo:
                    pinfo["file_obj"].close()
            except:
                pass
    _bg_processes.clear()


# ============================================================
# GROQ FUNCTION CALLING SCHEMA
# ============================================================
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "File ka content padhta hai line numbers ke saath.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Nayi file banata hai ya poori file overwrite karta hai.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string", "description": "Poora file content"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "File ke specific part ko replace karta hai (diff-based). "
                "Poori file nahi likhni padti — sirf old_code → new_code."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_code": {"type": "string", "description": "Exact text jo replace hona hai"},
                    "new_code": {"type": "string", "description": "Naya text jo aayega"},
                },
                "required": ["path", "old_code", "new_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Folder structure dikhata hai tree format mein.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Folder path, default '.'"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Shell/terminal command execute karta hai.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "cwd": {"type": "string", "description": "Working directory (optional)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Git status check karta hai — modified/new/deleted files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cwd": {"type": "string", "description": "Repo path"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Git diff dikhata hai — kya changes hue hain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cwd": {"type": "string", "description": "Repo path"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Saari changes stage karke commit karta hai.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                    "cwd": {"type": "string", "description": "Repo path"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Internet pe search karta hai (DuckDuckGo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "undo_last",
            "description": "Last file change (write/edit) revert karta hai.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_codebase",
            "description": "Codebase mein keyword ya pattern search karta hai.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term jo find karna hai"},
                    "file_pattern": {"type": "string", "description": "Glob file pattern filter, e.g. '*.py' (optional)", "default": "*"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "File name pattern search karta hai project folder mein.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern of filename (e.g. '*.html', 'models.py')"}
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_lines",
            "description": "File ka specific line range padhta hai line numbers ke saath.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "start_line": {"type": "integer", "description": "Start line number (1-indexed), default is 1", "default": 1},
                    "end_line": {"type": "integer", "description": "End line number (inclusive)"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file_lines",
            "description": "File ki specific line range ko replace karta hai (line range edit).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "start_line": {"type": "integer", "description": "Replace start line (1-indexed)"},
                    "end_line": {"type": "integer", "description": "Replace end line (inclusive, 1-indexed)"},
                    "new_content": {"type": "string", "description": "Naya text jo in lines ki jagah aayega"}
                },
                "required": ["path", "start_line", "end_line", "new_content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_outline",
            "description": "File mein classes aur functions defined ka outline map detail dikhata hai line numbers ke saath.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Tests command run karta hai project folder mein (jaise pytest, npm test).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Test command to execute, default is 'pytest'", "default": "pytest"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_background_process",
            "description": "Shell/terminal command ko background mein run karta hai (jaise server start karna).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command string to run in background (e.g. 'python app.py')"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_background_processes",
            "description": "Sari background running processes ki list aur status dikhata hai.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_background_process",
            "description": "Running background process ko terminate/kill karta hai.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_id": {"type": "integer", "description": "Index number of the process (e.g. 1)"}
                },
                "required": ["process_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_background_process_log",
            "description": "Background process ke log file ka output read karta hai ports/status dekhne ke liye.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_id": {"type": "integer", "description": "Index number of the process (e.g. 1)"},
                    "lines": {"type": "integer", "description": "Output lines to fetch (default is 50)", "default": 50}
                },
                "required": ["process_id"],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "read_file":                  read_file,
    "write_file":                 write_file,
    "edit_file":                  edit_file,
    "list_directory":             list_directory,
    "run_command":                run_command,
    "git_status":                 git_status,
    "git_diff":                   git_diff,
    "git_commit":                 git_commit,
    "web_search":                 web_search,
    "undo_last":                  undo_last,
    "search_codebase":            search_codebase,
    "find_files":                 find_files,
    "read_file_lines":            read_file_lines,
    "edit_file_lines":            edit_file_lines,
    "get_file_outline":           get_file_outline,
    "run_tests":                  run_tests,
    "start_background_process":   start_background_process,
    "list_background_processes":  list_background_processes,
    "stop_background_process":    stop_background_process,
    "read_background_process_log": read_background_process_log,
}