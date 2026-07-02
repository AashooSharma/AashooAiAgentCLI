"""
Git-colored file tree — agent ke har action ke baad refresh hota hai.
Colors: Green=new, Yellow=modified, Red=deleted, Cyan=renamed, White=unchanged
"""

import subprocess
from pathlib import Path
from rich.console import Console
from rich.text import Text

console = Console()


def get_git_status(project_path: str) -> dict[str, str]:
    """Git status parse karo — {filename: status_code}"""
    status_map = {}
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True,
            cwd=project_path
        )
        if result.returncode != 0:
            return {}
        for line in result.stdout.splitlines():
            if len(line) < 4:
                continue
            code = line[:2].strip()
            fname = line[3:].strip().strip('"')
            # Rename case: "old -> new"
            if " -> " in fname:
                fname = fname.split(" -> ")[-1]
            status_map[fname] = code
    except Exception:
        pass
    return status_map


def _status_color(rel_path: str, status_map: dict) -> str:
    """File ke liye color decide karo."""
    code = status_map.get(rel_path, "")
    if not code:
        # Parent folder check karo
        for k, v in status_map.items():
            if k.startswith(rel_path + "/") or k.startswith(rel_path + "\\"):
                code = v
                break

    if not code:
        return "white"
    c = code.upper()
    if "?" in c:
        return "bright_green"    # untracked/new
    if "A" in c:
        return "green"           # added
    if "M" in c:
        return "yellow"          # modified
    if "D" in c:
        return "red"             # deleted
    if "R" in c:
        return "cyan"            # renamed
    if "C" in c:
        return "blue"            # copied
    return "white"


def render_file_tree(project_path: str, max_lines: int = 40) -> Text:
    """Rich Text object return karo — colors ke saath."""
    p = Path(project_path)
    status_map = get_git_status(project_path)

    # .agentignore patterns
    ignore = {"__pycache__", ".git", "venv", "node_modules", ".DS_Store"}
    agentignore = p / ".agentignore"
    if agentignore.exists():
        for line in agentignore.read_text().splitlines():
            line = line.strip().rstrip("/")
            if line and not line.startswith("#"):
                ignore.add(line)

    def should_ignore(name: str) -> bool:
        if name in ignore:
            return True
        for pat in ignore:
            if pat.startswith("*") and name.endswith(pat[1:]):
                return True
        return False

    text = Text()
    lines_used = [0]

    def walk(folder: Path, prefix: str = "", rel: str = ""):
        if lines_used[0] >= max_lines:
            return
        try:
            items = sorted(
                [i for i in folder.iterdir() if not should_ignore(i.name)],
                key=lambda x: (x.is_file(), x.name.lower())
            )
        except PermissionError:
            return

        for i, item in enumerate(items):
            if lines_used[0] >= max_lines:
                text.append("  ... (more files)\n", style="dim")
                return
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "
            item_rel = (rel + "/" + item.name).lstrip("/")
            color = _status_color(item_rel, status_map)

            if item.is_dir():
                text.append(f"{prefix}{connector}", style="dim")
                text.append(f"{item.name}/\n", style=f"bold {color}")
                lines_used[0] += 1
                walk(item, prefix + ("    " if is_last else "│   "), item_rel)
            else:
                size = item.stat().st_size
                size_str = f" ({size}B)" if size < 1024 else f" ({size//1024}KB)"
                text.append(f"{prefix}{connector}", style="dim")
                text.append(item.name, style=color)
                text.append(f"{size_str}\n", style="dim")
                lines_used[0] += 1

    # Root
    root_color = "bold cyan"
    text.append(f"📁 {p.name}/\n", style=root_color)
    walk(p, rel="")
    return text


def print_file_tree(project_path: str):
    """File tree print karo with legend."""
    from rich.panel import Panel

    tree = render_file_tree(project_path)
    legend = Text()
    legend.append("● ", style="bright_green"); legend.append("new  ", style="dim")
    legend.append("● ", style="yellow"); legend.append("modified  ", style="dim")
    legend.append("● ", style="red"); legend.append("deleted  ", style="dim")
    legend.append("● ", style="cyan"); legend.append("renamed  ", style="dim")
    legend.append("● ", style="white"); legend.append("unchanged", style="dim")

    combined = Text()
    combined.append_text(tree)
    combined.append("\n")
    combined.append_text(legend)

    console.print(Panel(
        combined,
        title="[dim]Files[/dim]",
        border_style="dim",
        padding=(0, 1),
    ))

    # Background processes check & print
    try:
        from aashoo.agent.tools import get_active_processes_list
        active = get_active_processes_list()
        if active:
            bg_text = Text()
            for p in active:
                bg_text.append(f"[{p['id']}] ", style="bold cyan")
                bg_text.append(f"PID {p['pid']}: ", style="dim")
                bg_text.append(f"{p['command']} ", style="bold green")
                bg_text.append(f"({p['start_time'].split()[-1]})\n", style="dim")
            
            console.print(Panel(
                bg_text.rstrip(),
                title="[bold yellow]🚀 Active Background Processes[/bold yellow]",
                border_style="yellow",
                padding=(0, 1),
            ))
    except Exception:
        pass