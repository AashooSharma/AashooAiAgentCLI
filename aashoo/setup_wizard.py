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
    "groq_api_keys": [],
    "google_api_keys": [],
    "openai_api_keys": [],
    "anthropic_api_keys": [],
    "active_groq_key_idx": 0,
    "active_google_key_idx": 0,
    "active_openai_key_idx": 0,
    "active_anthropic_key_idx": 0,
    # Per-provider model selection (saved independently per provider)
    "groq_model": "llama-3.3-70b-versatile",
    "google_model": "gemini-2.5-flash",
    "openai_model": "gpt-4o",
    "anthropic_model": "claude-3-5-sonnet-latest",
    "ollama_model": "llama3",
    "projects_dir": str(Path.home() / "aashoo-projects"),
    "theme": "dark",
    "auto_allow_low_risk": True,
    "setup_complete": False,
}

PROVIDER_MODELS = {
    "groq": [
        "llama-3.3-70b-versatile",
        "mixtral-8x7b-32768",
        "gemma2-9b-it",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
    ],
    "google": [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-3.5-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "o1-mini",
        "o1-preview",
        "gpt-4-turbo",
    ],
    "anthropic": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "ollama": [
        "gemma3:4b",
        "llama3",
        "mistral",
        "qwen2.5-coder",
        "phi3",
        "codegemma",
    ]
}


def load_config() -> dict:
    """Config load karo — nahi hai to default return karo."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)

                # Dynamic migration: old singular api_key keys list mein convert karo
                for prov in ["groq", "google", "openai", "anthropic"]:
                    old_key = f"{prov}_api_key"
                    array_key = f"{prov}_api_keys"
                    if old_key in data and data[old_key] and not data.get(array_key):
                        data[array_key] = [data[old_key]]

                # Migration: old single 'model' field ko per-provider fields mein convert karo
                if "model" in data:
                    old_model = data["model"]
                    old_provider = data.get("llm_provider", "groq")
                    prov_key = f"{old_provider}_model"
                    if prov_key not in data:
                        data[prov_key] = old_model
                    # old 'model' field hata do (optional, kept for backward compat)
                    data.pop("model", None)

                # Naye keys merge karo jo purani config mein nahi hain
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
        "[dim]Ek baar setup karo, API keys daalo aur project par kaam shuru karo[/dim]",
        border_style="cyan"
    ))

    console.print()
    config = DEFAULT_CONFIG.copy()

    # Step 1: LLM Provider
    console.print("[bold yellow]Step 1/5 — LLM Provider choose karo[/bold yellow]")
    console.print("""
  [cyan]1[/cyan] — Groq API       [dim](fast, free tier available)[/dim]
  [cyan]2[/cyan] — Google AI      [dim](Gemini models, 1M+ tokens limit)[/dim]
  [cyan]3[/cyan] — OpenAI         [dim](GPT models)[/dim]
  [cyan]4[/cyan] — Anthropic      [dim](Claude models)[/dim]
  [cyan]5[/cyan] — Ollama         [dim](local, free, needs Ollama running)[/dim]
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
    provider = provider_map[choice]
    config["llm_provider"] = provider

    console.print()

    # Step 2: API Keys (Multiple keys setup support)
    console.print("[bold yellow]Step 2/5 — API Key(s) enter karo[/bold yellow]")

    if provider == "ollama":
        console.print("[dim]Ollama local hai, koi API key nahi chahiye[/dim]")
        ollama_url = Prompt.ask(
            "Ollama URL",
            default="http://localhost:11434"
        )
        config["ollama_url"] = ollama_url
    else:
        provider_name = provider.capitalize()
        key_env_map = {
            "groq": "GROQ_API_KEY",
            "google": "GOOGLE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
        }
        env_var = key_env_map.get(provider, "API_KEY")

        # Env se primary key try karo
        existing = os.environ.get(env_var, "")
        keys = []
        if existing:
            console.print(f"[green]✓ {env_var} environment variable mili[/green]")
            use_env = Confirm.ask("Yahi API key primary key ki tarah use karein?", default=True)
            if use_env:
                keys.append(existing)

        if not keys:
            console.print(
                f"[dim]Multiple keys de sakte hain (comma ',' se separate karke) rate limits bypass karne ke liye.[/dim]"
            )
            api_input = Prompt.ask(f"{provider_name} API Key(s)", password=True)
            keys = [k.strip() for k in api_input.split(",") if k.strip()]

        config[f"{provider}_api_keys"] = keys
        config[f"active_{provider}_key_idx"] = 0
        console.print(f"[green]✓ {len(keys)} API Key(s) add ho gayi hain.[/green]")

    console.print()

    # Step 3: Model selection
    console.print("[bold yellow]Step 3/5 — Model choose karo[/bold yellow]")
    models_list = PROVIDER_MODELS.get(provider, ["llama-3.3-70b-versatile"])
    
    for idx, model_opt in enumerate(models_list, 1):
        console.print(f"  [cyan]{idx}[/cyan] — {model_opt}")

    model_choice = Prompt.ask(
        "Apna model select karo",
        choices=[str(i) for i in range(1, len(models_list) + 1)],
        default="1"
    )
    selected_model = models_list[int(model_choice) - 1]
    config[f"{provider}_model"] = selected_model
    console.print(f"[green]✓ Selected Model: {selected_model}[/green]")

    console.print()

    # Step 4: Projects folder
    console.print("[bold yellow]Step 4/5 — Projects folder[/bold yellow]")
    default_dir = str(Path.home() / "aashoo-projects")
    projects_dir = Prompt.ask(
        "Projects folder path",
        default=default_dir
    )
    config["projects_dir"] = projects_dir
    Path(projects_dir).mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓ Folder ready: {projects_dir}[/green]")

    console.print()

    # Step 5: Preferences
    console.print("[bold yellow]Step 5/5 — Preferences[/bold yellow]")
    config["auto_allow_low_risk"] = Confirm.ask(
        "Low-risk tools (read_file, web_search, list_directory) auto-allow karein?",
        default=True
    )

    console.print()

    # Save
    config["setup_complete"] = True
    save_config(config)

    console.print(Panel(
        "[bold green]✓ Setup complete![/bold green]\n\n"
        f"Provider : [cyan]{config['llm_provider']}[/cyan]\n"
        f"Model    : [cyan]{config['model']}[/cyan]\n"
        f"Projects : [cyan]{config['projects_dir']}[/cyan]\n\n"
        "[dim]Config saved: ~/.aashoo/config.json[/dim]\n"
        "[dim]Change karne ke liye run karein: aashoo --setup[/dim]",
        border_style="green"
    ))

    console.print()
    input("Enter dabao continue karne ke liye...")
    return config