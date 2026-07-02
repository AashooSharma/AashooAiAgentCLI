"""
First-run setup wizard.
Config save hoti hai: ~/.aashoo/config.json
"""

import os
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich import print as rprint

console = Console()

CONFIG_DIR = Path.home() / ".aashoo"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "llm_provider": "groq",
    "groq_api_key": "",
    "model": "llama-3.3-70b-versatile",
    "projects_dir": str(Path.home() / "aashoo-projects"),
    "theme": "dark",
    "auto_allow_low_risk": True,
    "setup_complete": False,
}


def load_config() -> dict:
    """Config load karo — nahi hai to default return karo."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # naye keys merge karo jo purani config mein nahi hain
                for k, v in DEFAULT_CONFIG.items():
                    if k not in data:
                        data[k] = v
                return data
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Config file mein save karo."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def is_setup_done() -> bool:
    return CONFIG_FILE.exists() and load_config().get("setup_complete", False)


def run_wizard():
    """First-run setup wizard."""
    console.clear()

    console.print(Panel.fit(
        "[bold cyan]Aashoo Agent — Setup Wizard[/bold cyan]\n"
        "[dim]Ek baar setup karo, phir har baar seedha kaam pe lagao[/dim]",
        border_style="cyan"
    ))

    console.print()
    config = DEFAULT_CONFIG.copy()

    # Step 1: LLM Provider
    console.print("[bold yellow]Step 1/4 — LLM Provider choose karo[/bold yellow]")
    console.print("""
  [cyan]1[/cyan] — Groq API       [dim](fast, free tier available)[/dim]
  [cyan]2[/cyan] — Google AI      [dim](Gemini models)[/dim]
  [cyan]3[/cyan] — OpenAI         [dim](GPT models)[/dim]
  [cyan]4[/cyan] — Anthropic      [dim](Claude models)[/dim]
  [cyan]5[/cyan] — Ollama         [dim](local, free, needs Ollama installed)[/dim]
    """)

    provider_map = {
        "1": "groq",
        "2": "google",
        "3": "openai",
        "4": "anthropic",
        "5": "ollama",
    }

    choice = Prompt.ask(
        "[bold]Choice[/bold]",
        choices=["1", "2", "3", "4", "5"],
        default="1"
    )
    config["llm_provider"] = provider_map[choice]

    console.print()

    # Step 2: API Key
    console.print("[bold yellow]Step 2/4 — API Key enter karo[/bold yellow]")

    if config["llm_provider"] == "ollama":
        console.print("[dim]Ollama local hai, koi API key nahi chahiye[/dim]")
        config["groq_api_key"] = "ollama"
        ollama_url = Prompt.ask(
            "Ollama URL",
            default="http://localhost:11434"
        )
        config["ollama_url"] = ollama_url
    else:
        provider_name = config["llm_provider"].capitalize()
        key_env_map = {
            "groq": "GROQ_API_KEY",
            "google": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = key_env_map.get(config["llm_provider"], "API_KEY")

        # env se check karo pehle
        existing = os.environ.get(env_var, "")
        if existing:
            console.print(f"[green]✓ {env_var} environment variable mili[/green]")
            use_env = Confirm.ask("Yahi use karein?", default=True)
            if use_env:
                config["groq_api_key"] = existing
            else:
                api_key = Prompt.ask(f"{provider_name} API Key", password=True)
                config["groq_api_key"] = api_key
        else:
            console.print(f"[dim]Groq free tier: https://console.groq.com[/dim]")
            api_key = Prompt.ask(f"{provider_name} API Key", password=True)
            config["groq_api_key"] = api_key

    console.print()

    # Step 3: Projects folder
    console.print("[bold yellow]Step 3/4 — Projects folder[/bold yellow]")
    default_dir = str(Path.home() / "aashoo-projects")
    projects_dir = Prompt.ask(
        "Projects folder path",
        default=default_dir
    )
    config["projects_dir"] = projects_dir
    Path(projects_dir).mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓ Folder ready: {projects_dir}[/green]")

    console.print()

    # Step 4: Preferences
    console.print("[bold yellow]Step 4/4 — Preferences[/bold yellow]")
    config["auto_allow_low_risk"] = Confirm.ask(
        "Low-risk tools (read_file, web_search) auto-allow karein?",
        default=True
    )

    console.print()

    # Save
    config["setup_complete"] = True
    save_config(config)

    console.print(Panel(
        "[bold green]✓ Setup complete![/bold green]\n\n"
        f"Provider : [cyan]{config['llm_provider']}[/cyan]\n"
        f"Projects : [cyan]{config['projects_dir']}[/cyan]\n\n"
        "[dim]Config saved: ~/.aashoo/config.json[/dim]\n"
        "[dim]Change karne ke liye: aashoo --setup[/dim]",
        border_style="green"
    ))

    console.print()
    input("Enter dabao continue karne ke liye...")
    return config