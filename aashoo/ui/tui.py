"""
Terminal UI helpers — permission prompt, message display, spinner.
Rich-based (Phase 1). Phase 2 mein Textual replace karega.
"""

import json
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.syntax import Syntax
from rich.prompt import Prompt
from rich import print as rprint

console = Console()


def print_user_message(text: str):
    console.print(
        Panel(
            Text(text, style="white"),
            title="[bold cyan]You[/bold cyan]",
            title_align="right",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def print_agent_message(text: str):
    """Agent ka text message print karo (markdown-aware)."""
    from rich.markdown import Markdown
    console.print(
        Panel(
            Markdown(text),
            title="[bold green]Aashoo Agent[/bold green]",
            title_align="left",
            border_style="green",
            padding=(0, 1),
        )
    )


def print_tool_call(tool_name: str, args: dict, icon: str = "🔧"):
    """Tool call dikhao."""
    args_str = json.dumps(args, indent=2, ensure_ascii=False)
    console.print(
        Panel(
            Syntax(args_str, "json", theme="monokai", line_numbers=False),
            title=f"[yellow]{icon} {tool_name}[/yellow]",
            title_align="left",
            border_style="yellow",
            padding=(0, 1),
        )
    )


def print_tool_result(tool_name: str, result: str, icon: str = "🔧"):
    """Tool result dikhao."""
    # Code-like output ke liye syntax highlighting
    style = "dim"
    display = Text(result[:1500], style="dim")
    if result.startswith("✓"):
        style = "green"
        display = Text(result, style="green")
    elif result.startswith("Error"):
        display = Text(result, style="red")

    console.print(
        Panel(
            display,
            title=f"[dim]{icon} {tool_name} → result[/dim]",
            title_align="left",
            border_style="dim",
            padding=(0, 1),
        )
    )


def permission_prompt(tool_name: str, args: dict, icon: str = "🔧") -> tuple[str, str]:
    """
    Permission maango.
    Returns: (decision, reason)
    decision: 'allow' | 'always' | 'deny' | 'deny_reason' | 'deny_all'
    reason: user ka message (deny_reason case mein)
    """
    args_preview = json.dumps(args, ensure_ascii=False)
    if len(args_preview) > 200:
        args_preview = args_preview[:200] + "..."

    console.print(Panel(
        f"[bold yellow]{icon} {tool_name}[/bold yellow]\n\n"
        f"[dim]{args_preview}[/dim]\n\n"
        "[cyan][A][/cyan] Allow  "
        "[cyan][!][/cyan] Always allow  "
        "[red][D][/red] Deny  "
        "[yellow][R][/yellow] Deny + Reason  "
        "[red][X][/red] Stop agent",
        title="[bold red]⚠ Permission Required[/bold red]",
        border_style="red",
        padding=(0, 1),
    ))

    while True:
        try:
            choice = Prompt.ask(
                "[bold]Choice[/bold]",
                default="A"
            ).strip().upper()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[red]Denied[/red]")
            return ("deny", "")

        if choice in ("A", "ALLOW", ""):
            return ("allow", "")
        elif choice in ("!", "ALWAYS"):
            return ("always", "")
        elif choice in ("D", "DENY"):
            return ("deny", "")
        elif choice in ("R", "REASON"):
            try:
                reason = Prompt.ask(
                    "[yellow]Reason / Alternative suggestion[/yellow]"
                ).strip()
            except (KeyboardInterrupt, EOFError):
                reason = ""
            return ("deny_reason", reason)
        elif choice in ("X", "STOP"):
            return ("deny_all", "")
        else:
            console.print(
                "[dim]A=Allow  !=Always  "
                "D=Deny  R=Deny+Reason  X=Stop[/dim]"
            )


def show_plan_approval(plan_text: str) -> tuple[str, str]:
    """
    Plan dikhao aur approval lo.
    Returns: ('approve' | 'edit' | 'reject'), feedback_or_reason
    """
    from rich.markdown import Markdown

    console.print(Panel(
        Markdown(plan_text),
        title="[bold blue]📋 Agent ka Plan[/bold blue]",
        title_align="left",
        border_style="blue",
        padding=(0, 1),
    ))

    console.print(
        "\n[cyan][Y][/cyan] Approve — plan ke according kaam shuru karo\n"
        "[cyan][E][/cyan] Edit — plan mein changes chahiye\n"
        "[red][N][/red] Reject — yeh plan nahi chahiye\n"
    )

    while True:
        try:
            choice = Prompt.ask(
                "[bold]Choice[/bold]",
                default="Y"
            ).strip().upper()
        except (KeyboardInterrupt, EOFError):
            return ("reject", "")

        if choice in ("Y", "YES", ""):
            return ("approve", "")
        elif choice in ("E", "EDIT"):
            try:
                feedback = Prompt.ask(
                    "[cyan]Plan mein kya change chahiye[/cyan]"
                ).strip()
            except (KeyboardInterrupt, EOFError):
                feedback = ""
            return ("edit", feedback)
        elif choice in ("N", "NO", "REJECT"):
            try:
                reason = Prompt.ask(
                    "[red]Kya chahiye instead[/red]",
                    default=""
                ).strip()
            except (KeyboardInterrupt, EOFError):
                reason = ""
            return ("reject", reason)
        else:
            console.print("[dim]Y=Approve  E=Edit  N=Reject[/dim]")
            


def print_plan(plan_text: str):
    """Agent ka plan display karo execute karne se pehle."""
    from rich.markdown import Markdown
    console.print(Panel(
        Markdown(plan_text),
        title="[bold blue]📋 Agent Plan[/bold blue]",
        title_align="left",
        border_style="blue",
        padding=(0, 1),
    ))


def print_separator():
    console.print("─" * console.width, style="dim")


def print_command_help():
    console.print(Panel(
        "[cyan]/help[/cyan]       — ye list dikhao\n"
        "[cyan]/clear[/cyan]      — screen clear karo\n"
        "[cyan]/history[/cyan]    — conversation history dikhao\n"
        "[cyan]/undo[/cyan]       — last file change revert karo\n"
        "[cyan]/tree[/cyan]       — file tree refresh karo\n"
        "[cyan]/bg[/cyan]         — background processes list karo\n"
        "[cyan]/bg-stop N[/cyan]  — background process N ko stop karo\n"
        "[cyan]/editor[/cyan]     — Monaco Web Editor launch karo\n"
        "[cyan]/code[/cyan]       — Monaco Web Editor launch karo\n"
        "[cyan]/switch[/cyan]     — Dynamic Provider/Model/API Key switcher\n"
        "[cyan]/exit[/cyan]       — project se bahar jao\n",
        title="[bold]Commands[/bold]",
        border_style="dim",
    ))