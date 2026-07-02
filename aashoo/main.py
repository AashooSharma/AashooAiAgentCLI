"""
Aashoo Agent — Entry point
Command: aashoo
"""

import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from aashoo.setup_wizard import is_setup_done, run_wizard, load_config
from aashoo.projects.manager import create_project, open_project, clone_github

console = Console()

def get_random_logo() -> str:
    default_logo = r"""
   ___         _                    ___                    _   
  / _ \  __ _ | |_   ___  ___     / _ \  __ _  ___  _ _ | |_ 
 | (_) |/ _` ||   \ / _ \/ _ \   | (_) |/ _` |/ -_)| ' \|  _|
  \___/ \__,_||_||_|\___/\___/    \___/ \__, |\___||_||_|\__|
                                         |___/                 
"""
    try:
        from pathlib import Path
        import random
        
        logo_path = Path(__file__).resolve().parent.parent / "logo.txt"
        if not logo_path.exists():
            return default_logo
            
        content = logo_path.read_text(encoding="utf-8", errors="replace")
        raw_blocks = content.split("\n\n")
        logos = []
        for block in raw_blocks:
            lines = [l for l in block.splitlines() if l.strip()]
            if len(lines) >= 3:
                logos.append(block.strip("\r\n"))
                
        if logos:
            return random.choice(logos)
    except Exception:
        pass
    return default_logo


def rainbow_text(text: str) -> str:
    """ASCII art text ko vertical rainbow gradient ke sath colorize karta hai."""
    import colorsys
    import random
    start_hue = random.random()
    lines = text.splitlines()
    colored_lines = []
    num_lines = len(lines)
    for i, line in enumerate(lines):
        if not line.strip():
            colored_lines.append(line)
            continue
        hue = (start_hue + (i / max(1, num_lines) * 0.8)) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        r_int = int(r * 255)
        g_int = int(g * 255)
        b_int = int(b * 255)
        colored_lines.append(f"[rgb({r_int},{g_int},{b_int})]{line}[/]")
    return "\n".join(colored_lines)


ACTIVE_LOGO = get_random_logo()


def print_logo():
    console.print(rainbow_text(ACTIVE_LOGO))
    console.print(
        "[dim]  Personal AI Coding Agent — v0.1.0  |  "
        "github.com/sdbabhishek/aashoo-agent[/dim]\n"
    )


def main_menu(config: dict) -> str:
    """Main menu show karo aur choice return karo."""
    console.print(Panel.fit(
        "[bold white]Kya karna hai?[/bold white]\n\n"
        "  [cyan bold]1[/cyan bold]  New Project\n"
        "  [cyan bold]2[/cyan bold]  Open Project\n"
        "  [cyan bold]3[/cyan bold]  GitHub Clone\n"
        "  [cyan bold]4[/cyan bold]  Settings\n"
        "  [cyan bold]5[/cyan bold]  Exit\n",
        border_style="cyan",
        title=f"[dim]{config['llm_provider'].upper()} | "
              f"{config.get('model', 'llama-3.3-70b-versatile')}[/dim]",
        title_align="right"
    ))

    from rich.prompt import Prompt
    choice = Prompt.ask(
        "[bold]Choice[/bold]",
        choices=["1", "2", "3", "4", "5"],
        default="1"
    )
    return choice


def settings_menu(config: dict):
    """Settings dikhao aur re-run wizard option do."""
    from rich.prompt import Confirm
    console.print()
    console.print(Panel(
        f"[bold]Current Config[/bold]\n\n"
        f"Provider  : [cyan]{config['llm_provider']}[/cyan]\n"
        f"Model     : [cyan]{config.get('model', 'llama-3.3-70b-versatile')}[/cyan]\n"
        f"Projects  : [cyan]{config['projects_dir']}[/cyan]\n"
        f"Auto-allow: [cyan]{config.get('auto_allow_low_risk', True)}[/cyan]\n\n"
        "[dim]Config file: ~/.aashoo/config.json[/dim]",
        border_style="dim"
    ))

    if Confirm.ask("\nSetup wizard dobara run karein?", default=False):
        run_wizard()


# def start_agent_session(project: dict, config: dict):
#     """
#     Agent session start karo selected project ke liye.
#     Yeh Batch 2-3 mein properly implement hoga.
#     Abhi placeholder dikhata hai.
#     """
#     console.clear()
#     print_logo()

#     console.print(Panel.fit(
#         f"[bold green]Project: {project['name']}[/bold green]\n"
#         f"[dim]Path: {project['path']}[/dim]\n"
#         f"[dim]Git: {'Yes' if project.get('is_git') else 'No'}[/dim]",
#         border_style="green"
#     ))

#     console.print(
#         "\n[bold yellow]⚠ Agent loop Batch 2 mein aayega.[/bold yellow]\n"
#         "[dim]Abhi project setup correctly hua hai. "
#         "Next batch mein yahan real agent chat chalega.[/dim]\n"
#     )

#     # Placeholder loop — Batch 2 mein replace hoga
#     from rich.prompt import Prompt
#     while True:
#         try:
#             user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
#             if user_input.lower() in ("/exit", "exit", "quit", "/quit"):
#                 console.print("[dim]Session ended.[/dim]")
#                 break
#             console.print(
#                 f"[dim]Agent response yahan aayega "
#                 f"(Batch 2 ke baad)... tu likha: {user_input}[/dim]"
#             )
#         except KeyboardInterrupt:
#             console.print("\n[dim]Session ended.[/dim]")
#             break

def start_agent_session(project: dict, config: dict):
    """Real agent session."""
    from aashoo.llm.groq import GroqLLM
    from aashoo.agent.loop import run_agent
    from aashoo.agent.tools import cleanup_background_processes
    from aashoo.ui.editor_server import stop_editor_server
    from aashoo.agent import memory
    from aashoo.ui.file_tree import print_file_tree
    from aashoo.ui.tui import (
        print_command_help, print_separator,
        print_user_message
    )

    # LLM initialize
    llm = GroqLLM(
        api_key=config["groq_api_key"],
        model=config.get("model", "llama-3.3-70b-versatile"),
    )

    auto_allow = config.get("auto_allow_low_risk", True)

    console.clear()
    print_logo()

    console.print(Panel.fit(
        f"[bold green]📂 {project['name']}[/bold green]\n"
        f"[dim]{project['path']}[/dim]",
        border_style="green"
    ))

    # File tree dikhao
    print_file_tree(project["path"])

    console.print(
        "\n[dim]Type karo ya /help commands ke liye[/dim]\n"
    )

    # Chat loop
    from rich.prompt import Prompt
    while True:
        try:
            user_input = Prompt.ask(
                "\n[bold cyan]You[/bold cyan]"
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            cleanup_background_processes()
            stop_editor_server()
            break

        if not user_input:
            continue

        # Built-in commands
        if user_input.lower() in ("/exit", "exit", "quit", "/quit"):
            console.print("[dim]Project se bahar aa gaye.[/dim]")
            cleanup_background_processes()
            stop_editor_server()
            break

        elif user_input.lower() == "/bg":
            from aashoo.agent.tools import list_background_processes
            result = list_background_processes()
            console.print(f"\n[yellow]{result}[/yellow]")

        elif user_input.lower().startswith("/bg-stop "):
            from aashoo.agent.tools import stop_background_process
            try:
                pid_str = user_input.split(" ", 1)[1].strip()
                pid = int(pid_str)
                result = stop_background_process(pid)
                console.print(f"[yellow]{result}[/yellow]")
                print_file_tree(project["path"])
            except (ValueError, IndexError):
                console.print("[red]Usage: /bg-stop <process_id>[/red]")

        elif user_input.lower() in ("/editor", "/code"):
            import webbrowser
            from aashoo.ui.editor_server import start_editor_server
            url = start_editor_server(project["path"])
            console.print(f"\n[green]🚀 Web Editor running at: [bold]{url}[/bold][/green]")
            try:
                webbrowser.open(url)
            except Exception:
                pass

        elif user_input.lower() == "/help":
            print_command_help()

        elif user_input.lower() == "/clear":
            console.clear()
            print_logo()
            print_file_tree(project["path"])

        elif user_input.lower() == "/tree":
            print_file_tree(project["path"])

        elif user_input.lower() == "/history":
            msgs = memory.load_history(project["path"], limit=20)
            if not msgs:
                console.print("[dim]Koi history nahi.[/dim]")
            else:
                for m in msgs:
                    role_style = "cyan" if m["role"] == "user" else "green"
                    console.print(
                        f"[{role_style}]{m['role']}[/{role_style}]: "
                        f"{m['content'][:100]}..."
                        if len(m['content']) > 100
                        else f"[{role_style}]{m['role']}[/{role_style}]: {m['content']}"
                    )

        elif user_input.lower() == "/undo":
            from aashoo.agent.tools import undo_last
            result = undo_last()
            console.print(f"[yellow]{result}[/yellow]")
            print_file_tree(project["path"])

        else:
            # Agent ko bhejo
            print_user_message(user_input)
            run_agent(project, llm, user_input, auto_allow)
            

def main():
    """Main entry point."""

    # --setup flag check karo
    if "--setup" in sys.argv:
        run_wizard()
        return

    # First run check
    if not is_setup_done():
        console.clear()
        print_logo()
        console.print(
            "[bold yellow]Pehli baar chal raha hai — setup wizard start ho raha hai...[/bold yellow]\n"
        )
        config = run_wizard()
    else:
        config = load_config()

    # Main loop
    while True:
        console.clear()
        print_logo()

        choice = main_menu(config)

        if choice == "1":
            # New Project
            project = create_project(config["projects_dir"])
            if project:
                start_agent_session(project, config)

        elif choice == "2":
            # Open Project
            project = open_project(config["projects_dir"])
            if project:
                start_agent_session(project, config)

        elif choice == "3":
            # GitHub Clone
            project = clone_github(config["projects_dir"])
            if project:
                start_agent_session(project, config)

        elif choice == "4":
            # Settings
            settings_menu(config)
            # config reload karo agar wizard ne change kiya
            config = load_config()

        elif choice == "5":
            console.print("\n[dim]Bye! Phir milenge.[/dim]\n")
            sys.exit(0)


if __name__ == "__main__":
    main()