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
    from rich.prompt import Prompt
    prov = config.get('llm_provider', 'groq')
    active_model = config.get(f"{prov}_model") or config.get('model', 'N/A')
    console.print(Panel.fit(
        "[bold white]Kya karna hai?[/bold white]\n\n"
        "  [cyan bold]1[/cyan bold]  New Project\n"
        "  [cyan bold]2[/cyan bold]  Open Project\n"
        "  [cyan bold]3[/cyan bold]  GitHub Clone\n"
        "  [cyan bold]4[/cyan bold]  Settings\n"
        "  [cyan bold]5[/cyan bold]  Exit\n",
        border_style="cyan",
        title=f"[dim]{prov.upper()} | {active_model}[/dim]",
        title_align="right"
    ))
    try:
        choice = Prompt.ask(
            "[bold]Choice[/bold]",
            choices=["1", "2", "3", "4", "5"],
            default="5"
        )
    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Bye! Phir milenge.[/dim]\n")
        sys.exit(0)
    return choice


def get_ollama_models() -> list:
    """Run `ollama list` aur available models return karo."""
    import subprocess
    from aashoo.setup_wizard import PROVIDER_MODELS
    fallback = PROVIDER_MODELS.get("ollama", ["llama3"])
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5
        )
        lines = result.stdout.strip().splitlines()
        models = []
        for line in lines[1:]:  # skip header
            parts = line.split()
            if parts:
                models.append(parts[0])  # e.g. "gemma3:4b"
        return models if models else fallback
    except Exception:
        return fallback


def settings_menu(config: dict):
    """Settings sub-menu — config safely update karo bina wizard re-run ke."""
    from rich.prompt import Prompt, Confirm
    from aashoo.setup_wizard import PROVIDER_MODELS, save_config

    while True:
        console.print()
        console.print(Panel(
            f"[bold]Current Config[/bold]\n\n"
            f"Provider  : [cyan]{config['llm_provider']}[/cyan]\n"
            f"Model     : [cyan]{config.get(f"{config['llm_provider']}_model") or config.get('model', 'N/A')}[/cyan]\n"
            f"Projects  : [cyan]{config['projects_dir']}[/cyan]\n"
            f"Auto-allow: [cyan]{config.get('auto_allow_low_risk', True)}[/cyan]\n\n"
            "[dim]Config file: ~/.aashoo/config.json[/dim]",
            border_style="dim"
        ))

        console.print(
            "  [cyan bold]1[/cyan bold]  API Key add karo (kisi bhi provider ke liye)\n"
            "  [cyan bold]2[/cyan bold]  Active model switch karo\n"
            "  [cyan bold]3[/cyan bold]  Auto-allow preference toggle karo\n"
            "  [cyan bold]4[/cyan bold]  Pura Setup Wizard dobara run karo (config overwrite hogi!)\n"
            "  [cyan bold]5[/cyan bold]  Back\n"
        )

        try:
            s_choice = Prompt.ask("[bold]Choice[/bold]", choices=["1","2","3","4","5"], default="5")
        except (KeyboardInterrupt, EOFError):
            break

        if s_choice == "1":
            # ── Add API Key (any provider) ──
            providers = ["groq", "google", "openai", "anthropic"]
            console.print("\nKis provider ki key add karni hai?")
            for i, p in enumerate(providers, 1):
                console.print(f"  [cyan]{i}[/cyan] — {p.upper()}")
            try:
                p_choice = Prompt.ask("Provider", choices=[str(i) for i in range(1, len(providers)+1)])
            except (KeyboardInterrupt, EOFError):
                continue
            chosen_prov = providers[int(p_choice) - 1]

            try:
                new_key = Prompt.ask(
                    f"Enter {chosen_prov.capitalize()} API Key(s) [dim](comma se alag karo multiple ke liye)[/dim]",
                    password=True
                ).strip()
            except (KeyboardInterrupt, EOFError):
                continue

            if new_key:
                new_keys = [k.strip() for k in new_key.split(",") if k.strip()]
                arr_key = f"{chosen_prov}_api_keys"
                if arr_key not in config:
                    config[arr_key] = []
                config[arr_key].extend(new_keys)
                # duplicate remove
                config[arr_key] = list(dict.fromkeys(config[arr_key]))
                save_config(config)
                console.print(f"[green]✓ {len(new_keys)} key(s) {chosen_prov.upper()} ke liye add ho gayi.[/green]")
            else:
                console.print("[dim]Cancelled.[/dim]")

        elif s_choice == "2":
            # ── Switch active model ──
            prov = config["llm_provider"]
            if prov == "ollama":
                models_list = get_ollama_models()
                console.print("[dim]Ollama se live models fetch ho rahi hain...[/dim]")
            else:
                models_list = PROVIDER_MODELS.get(prov, [])

            if not models_list:
                console.print("[red]Koi model nahi mili.[/red]")
                continue

            console.print(f"\nAvailable models for [cyan]{prov.upper()}[/cyan]:")
            for i, m in enumerate(models_list, 1):
                prov_model = config.get(f"{prov}_model") or config.get("model")
                active_marker = " [green]* (active)[/green]" if m == prov_model else ""
                console.print(f"  [cyan]{i}[/cyan] — {m}{active_marker}")

            console.print(f"  [cyan]{len(models_list)+1}[/cyan] — Custom model naam likhein")

            try:
                m_choice = Prompt.ask(
                    "Choose",
                    choices=[str(i) for i in range(1, len(models_list)+2)]
                )
            except (KeyboardInterrupt, EOFError):
                continue

            if int(m_choice) == len(models_list) + 1:
                try:
                    custom_model = Prompt.ask("Custom model naam").strip()
                except (KeyboardInterrupt, EOFError):
                    continue
                if custom_model:
                    config[f"{prov}_model"] = custom_model
            else:
                config[f"{prov}_model"] = models_list[int(m_choice) - 1]

            save_config(config)
            console.print(f"[green]✓ Model switched to [bold]{config[f'{prov}_model']}[/bold].[/green]")

        elif s_choice == "3":
            # ── Toggle auto-allow ──
            current = config.get("auto_allow_low_risk", True)
            config["auto_allow_low_risk"] = not current
            save_config(config)
            state = "ON" if config["auto_allow_low_risk"] else "OFF"
            console.print(f"[green]✓ Auto-allow {state} ho gaya.[/green]")

        elif s_choice == "4":
            # ── Full wizard (overwrites) ──
            if Confirm.ask("[red]Puri config overwrite ho jaayegi. Sure hain?[/red]", default=False):
                run_wizard()
            break

        elif s_choice == "5":
            break


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
    from aashoo.llm import get_llm_client
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
    llm = get_llm_client(config)

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
    
    HAS_PT = False
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.formatted_text import HTML

        kb = KeyBindings()

        @kb.add('c-s')  # Ctrl+S to submit prompt
        def _(event):
            event.current_buffer.validate_and_handle()

        pt_session = PromptSession(key_bindings=kb, multiline=True)
        HAS_PT = True
    except ImportError:
        pass

    while True:
        try:
            from aashoo.agent.tools import get_active_processes_list
            bg_procs = get_active_processes_list()
            if bg_procs:
                console.print("\n[bold yellow]⚙️ Running Background Tasks:[/bold yellow]")
                for bp in bg_procs:
                    console.print(f"  [dim]• [{bp['id']}] (PID {bp['pid']}): {bp['command']}[/dim]")
            
            if HAS_PT:
                user_input = pt_session.prompt(
                    HTML('\n<ansicyan><b>You</b></ansicyan> <ansigray>(Enter = new line, Ctrl+S = submit):</ansigray>\n')
                ).strip()
            else:
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

        elif user_input.lower() in ("/switch", "/api"):
            # Switch menu
            console.print(Panel.fit(
                "[bold white]Dynamic Configuration Switcher[/bold white]\n\n"
                "  [cyan bold]1[/cyan bold]  Switch Provider\n"
                "  [cyan bold]2[/cyan bold]  Switch API Key (for current provider)\n"
                "  [cyan bold]3[/cyan bold]  Switch Model (for current provider)\n"
                "  [cyan bold]4[/cyan bold]  Add New API Key\n"
                "  [cyan bold]5[/cyan bold]  Cancel\n",
                border_style="yellow",
                title=f"[dim]Active: {config['llm_provider'].upper()} | {config.get('model')}[/dim]",
                title_align="right"
            ))
            
            from rich.prompt import Prompt
            try:
                switch_choice = Prompt.ask("[bold]Switch Option[/bold]", choices=["1", "2", "3", "4", "5"], default="5")
            except (KeyboardInterrupt, EOFError):
                continue
                
            if switch_choice == "1":
                providers = ["groq", "google", "openai", "anthropic", "ollama"]
                console.print("\nAvailable Providers:")
                for i, p in enumerate(providers, 1):
                    console.print(f"  [cyan]{i}[/cyan] — {p.upper()}")
                p_choice = Prompt.ask("Choose provider", choices=[str(i) for i in range(1, len(providers)+1)])
                new_prov = providers[int(p_choice)-1]
                
                if new_prov != "ollama":
                    keys = config.get(f"{new_prov}_api_keys", [])
                    if not keys:
                        console.print(f"[yellow]Koi API key nahi hai {new_prov.upper()} ke liye. Pehle key add karein.[/yellow]")
                        api_input = Prompt.ask(f"Enter {new_prov.capitalize()} API Key", password=True)
                        if api_input.strip():
                            config[f"{new_prov}_api_keys"] = [api_input.strip()]
                            config[f"active_{new_prov}_key_idx"] = 0
                        else:
                            console.print("[red]Cancelled switching provider.[/red]")
                            continue
                            
                config["llm_provider"] = new_prov
                from aashoo.setup_wizard import PROVIDER_MODELS
                # Per-provider model restore karo agar already saved hai
                config["llm_provider"] = new_prov
                if not config.get(f"{new_prov}_model"):
                    config[f"{new_prov}_model"] = PROVIDER_MODELS[new_prov][0]
                
                from aashoo.setup_wizard import save_config
                save_config(config)
                llm = get_llm_client(config)
                active_model = config.get(f"{new_prov}_model")
                console.print(f"[green]✓ Switched to [bold]{new_prov.upper()}[/bold] using model [bold]{active_model}[/bold].[/green]")
                
            elif switch_choice == "2":
                prov = config["llm_provider"]
                if prov == "ollama":
                    console.print("[yellow]Ollama local hai, isme multiple API keys switch nahi hoti.[/yellow]")
                    continue
                    
                keys = config.get(f"{prov}_api_keys", [])
                if not keys:
                    console.print(f"[red]No API keys stored for {prov.upper()}. Add one first.[/red]")
                    continue
                    
                console.print(f"\nSaved {prov.upper()} API Keys:")
                for i, k in enumerate(keys):
                    starred = k[:6] + "..." + k[-4:] if len(k) > 10 else k
                    active_marker = " [green]*[/green]" if i == config.get(f"active_{prov}_key_idx", 0) else ""
                    console.print(f"  [cyan]{i}[/cyan] — {starred}{active_marker}")
                    
                k_choice = Prompt.ask("Choose active key", choices=[str(i) for i in range(len(keys))])
                config[f"active_{prov}_key_idx"] = int(k_choice)
                
                from aashoo.setup_wizard import save_config
                save_config(config)
                llm = get_llm_client(config)
                console.print(f"[green]✓ Active key index set to [bold]{k_choice}[/bold].[/green]")
                
            elif switch_choice == "3":
                prov = config["llm_provider"]
                from aashoo.setup_wizard import PROVIDER_MODELS
                if prov == "ollama":
                    console.print("[dim]Ollama se live models fetch ho rahi hain...[/dim]")
                    models_list = get_ollama_models()
                else:
                    models_list = PROVIDER_MODELS.get(prov, ["llama-3.3-70b-versatile"])

                console.print(f"\nAvailable models for {prov.upper()}:")
                for i, m in enumerate(models_list, 1):
                    prov_model = config.get(f"{prov}_model") or config.get("model")
                    active_marker = " [green]* (active)[/green]" if m == prov_model else ""
                    console.print(f"  [cyan]{i}[/cyan] — {m}{active_marker}")
                console.print(f"  [cyan]{len(models_list)+1}[/cyan] — Custom model naam likhein")

                try:
                    m_choice = Prompt.ask(
                        "Choose model",
                        choices=[str(i) for i in range(1, len(models_list)+2)]
                    )
                except (KeyboardInterrupt, EOFError):
                    continue

                if int(m_choice) == len(models_list) + 1:
                    try:
                        custom_model = Prompt.ask("Custom model naam").strip()
                    except (KeyboardInterrupt, EOFError):
                        continue
                    if custom_model:
                        config[f"{prov}_model"] = custom_model
                else:
                    config[f"{prov}_model"] = models_list[int(m_choice) - 1]

                from aashoo.setup_wizard import save_config
                save_config(config)
                llm = get_llm_client(config)
                console.print(f"[green]✓ Switched model to [bold]{config[f'{prov}_model']}[/bold].[/green]")
                
            elif switch_choice == "4":
                # ── Add API Key — provider choose karo pehle ──
                api_providers = ["groq", "google", "openai", "anthropic"]
                console.print("\nKis provider ki key add karni hai?")
                for i, p in enumerate(api_providers, 1):
                    console.print(f"  [cyan]{i}[/cyan] — {p.upper()}")
                try:
                    ap_choice = Prompt.ask(
                        "Provider choose karo",
                        choices=[str(i) for i in range(1, len(api_providers)+1)]
                    )
                except (KeyboardInterrupt, EOFError):
                    continue
                chosen_prov = api_providers[int(ap_choice) - 1]

                try:
                    new_key = Prompt.ask(
                        f"Enter {chosen_prov.capitalize()} API Key(s) [dim](comma se alag karo)[/dim]",
                        password=True
                    ).strip()
                except (KeyboardInterrupt, EOFError):
                    continue

                if new_key:
                    new_keys = [k.strip() for k in new_key.split(",") if k.strip()]
                    arr_key = f"{chosen_prov}_api_keys"
                    if arr_key not in config:
                        config[arr_key] = []
                    config[arr_key].extend(new_keys)
                    config[arr_key] = list(dict.fromkeys(config[arr_key]))  # dedupe
                    config[f"active_{chosen_prov}_key_idx"] = 0

                    from aashoo.setup_wizard import save_config
                    save_config(config)
                    llm = get_llm_client(config)
                    console.print(f"[green]✓ {len(new_keys)} key(s) {chosen_prov.upper()} ke liye add aur save ho gayi.[/green]")

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
    try:
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
                try:
                    settings_menu(config)
                except (KeyboardInterrupt, EOFError):
                    pass
                # config reload karo agar wizard ne change kiya
                config = load_config()

            elif choice == "5":
                console.print("\n[dim]Bye! Phir milenge.[/dim]\n")
                sys.exit(0)

    except (KeyboardInterrupt, EOFError):
        console.print("\n[dim]Bye! Phir milenge.[/dim]\n")
        sys.exit(0)


if __name__ == "__main__":
    main()