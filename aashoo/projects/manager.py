"""
Project create, open, list, GitHub clone karna.
Har project ka data: ~/.aashoo/memory.db mein
Projects files: ~/aashoo-projects/<project-name>/
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()


def get_projects_list(projects_dir: str) -> list[dict]:
    """Projects folder se saare projects list karo."""
    base = Path(projects_dir)
    if not base.exists():
        return []

    projects = []
    for item in sorted(base.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            # git repo hai ya nahi
            is_git = (item / ".git").exists()
            # last modified
            try:
                mtime = item.stat().st_mtime
                last_mod = datetime.fromtimestamp(mtime).strftime("%d %b %Y")
            except Exception:
                last_mod = "unknown"

            # file count
            try:
                file_count = sum(1 for f in item.rglob("*")
                                 if f.is_file() and ".git" not in str(f))
            except Exception:
                file_count = 0

            projects.append({
                "name": item.name,
                "path": str(item),
                "is_git": is_git,
                "last_modified": last_mod,
                "file_count": file_count,
            })

    return projects


def create_project(projects_dir: str) -> dict | None:
    """Naya project create karo."""
    console.print()
    console.print("[bold cyan]— New Project —[/bold cyan]")

    name = Prompt.ask("[bold]Project naam[/bold]")
    name = name.strip().replace(" ", "-").lower()

    if not name:
        console.print("[red]Invalid naam[/red]")
        return None

    project_path = Path(projects_dir) / name

    if project_path.exists():
        console.print(f"[yellow]'{name}' pehle se exist karta hai[/yellow]")
        open_existing = Confirm.ask("Isko open karein?", default=True)
        if open_existing:
            return {
                "name": name,
                "path": str(project_path),
                "is_git": (project_path / ".git").exists(),
            }
        return None

    # Folder create karo
    project_path.mkdir(parents=True)

    # Git init
    init_git = Confirm.ask("Git initialize karein?", default=True)
    if init_git:
        try:
            subprocess.run(
                ["git", "init"],
                cwd=str(project_path),
                capture_output=True
            )
            # .gitignore default
            gitignore_content = (
                "__pycache__/\n*.pyc\n.env\nvenv/\n"
                "node_modules/\n.DS_Store\n*.log\n"
            )
            (project_path / ".gitignore").write_text(gitignore_content)
            console.print("[green]✓ Git initialized[/green]")
        except FileNotFoundError:
            console.print("[yellow]⚠ Git nahi mila, skip kiya[/yellow]")

    # .agentignore default
    agentignore_content = (
        "# Aashoo Agent — in files/folders ko ignore karo\n"
        "__pycache__/\n*.pyc\n.env\nvenv/\n"
        "node_modules/\n.git/\n*.log\n*.bin\n*.exe\n"
    )
    (project_path / ".agentignore").write_text(agentignore_content)

    console.print(f"[green]✓ Project '{name}' ready: {project_path}[/green]")

    return {
        "name": name,
        "path": str(project_path),
        "is_git": init_git,
    }


def open_project(projects_dir: str) -> dict | None:
    """Existing project open karo."""
    projects = get_projects_list(projects_dir)

    if not projects:
        console.print(
            f"[yellow]Koi project nahi mila: {projects_dir}[/yellow]\n"
            "[dim]Pehle 'New Project' se ek create karo[/dim]"
        )
        return None

    console.print()
    console.print("[bold cyan]— Open Project —[/bold cyan]")

    # Table dikhao
    table = Table(show_header=True, header_style="bold cyan",
                  border_style="dim", box=None)
    table.add_column("#", style="dim", width=4)
    table.add_column("Project", style="bold white")
    table.add_column("Files", justify="right", style="dim")
    table.add_column("Last Modified", style="dim")
    table.add_column("Git", justify="center")

    for i, p in enumerate(projects, 1):
        git_status = "[green]✓[/green]" if p["is_git"] else "[dim]✗[/dim]"
        table.add_row(
            str(i),
            p["name"],
            str(p["file_count"]),
            p["last_modified"],
            git_status,
        )

    console.print(table)
    console.print()

    choices = [str(i) for i in range(1, len(projects) + 1)]
    choice = Prompt.ask(
        "Project number select karo",
        choices=choices
    )

    selected = projects[int(choice) - 1]
    return selected


def clone_github(projects_dir: str) -> dict | None:
    """GitHub repo clone karo."""
    console.print()
    console.print("[bold cyan]— GitHub Clone —[/bold cyan]")

    url = Prompt.ask("[bold]GitHub URL[/bold]")
    url = url.strip()

    if not url:
        console.print("[red]Invalid URL[/red]")
        return None

    # Naam extract karo URL se
    repo_name = url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    project_path = Path(projects_dir) / repo_name

    if project_path.exists():
        console.print(f"[yellow]'{repo_name}' pehle se exist karta hai[/yellow]")
        open_existing = Confirm.ask("Isko open karein?", default=True)
        if open_existing:
            return {
                "name": repo_name,
                "path": str(project_path),
                "is_git": True,
            }
        return None

    console.print(f"[dim]Cloning {url}...[/dim]")

    try:
        result = subprocess.run(
            ["git", "clone", url, str(project_path)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            console.print(f"[red]Clone failed:[/red] {result.stderr}")
            return None

        console.print(f"[green]✓ Cloned: {project_path}[/green]")
        return {
            "name": repo_name,
            "path": str(project_path),
            "is_git": True,
        }

    except FileNotFoundError:
        console.print("[red]Git nahi mila. Install karo: pkg install git (Termux) ya apt install git[/red]")
        return None