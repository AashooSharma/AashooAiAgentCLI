"""
Agent loop — Plan-first → Approval → Execute
"""

import json
from rich.console import Console
from rich.live import Live
from rich.text import Text

from aashoo.llm.base import BaseLLM
from aashoo.agent.tools import (
    TOOLS_SCHEMA, AVAILABLE_FUNCTIONS,
    TOOL_RISK, TOOL_ICONS,
)
from aashoo.agent import memory
from aashoo.ui import tui
from aashoo.ui.file_tree import print_file_tree

console = Console()

MAX_ITERATIONS = 10

SYSTEM_PROMPT = """Tu Aashoo ka personal AI coding agent hai.

## Kaam karne ka tarika

### Jab user koi PROJECT ya TASK describe kare:
HAMESHA pehle ek detailed plan banao markdown mein:
```
## Plan

**Project:** [naam]
**Description:** [kya banana hai]

### Steps:
1. [step 1 — kya file/folder banana hai]
2. [step 2]
3. ...

### Files jo banengi:
- `filename.py` — [kya hoga isme]
- `folder/file.js` — [kya hoga]

**Estimated steps:** X
```

Plan banane ke BAAD ruko — user approve karega tab execute karo.

### Jab user simple edit/question kare:
Direct karo — plan ki zarurat nahi.

### Tool usage rules:
1. File edit karne se pehle HAMESHA read_file ya read_file_lines karo
2. edit_file ya edit_file_lines prefer karo write_file se (partial edit/line range edit better hai)
3. search_codebase se relevant code dhundho pehle
4. run_tests ya run_command se test karo changes ke baad
5. git_status check karo important changes ke baad

### Agar user deny kare with reason:
- Reason padho carefully
- Alternative approach lo
- KABHI same tool same args se dobara mat maango
- User ke suggestion ko follow karo

### Language:
Hinglish mein casual baat karo. Technical terms English mein theek hai.

Available tools: read_file, write_file, edit_file, list_directory, run_command, git_status, git_diff, git_commit, web_search, undo_last, search_codebase, find_files, read_file_lines, edit_file_lines, get_file_outline, run_tests
"""

PLAN_TRIGGER_KEYWORDS = [
    "banao", "create", "build", "make", "develop", "bana",
    "project", "app", "application", "website", "api",
    "setup", "initialize", "start", "new", "naya",
]


def _needs_plan(user_message: str) -> bool:
    """Kya is message ke liye plan banana chahiye?"""
    msg_lower = user_message.lower()
    word_count = len(msg_lower.split())

    # Chota message — plan nahi chahiye
    if word_count < 4:
        return False

    # Keywords check
    has_trigger = any(kw in msg_lower for kw in PLAN_TRIGGER_KEYWORDS)

    # Agar message mein multiple cheezein hain
    is_complex = word_count > 10

    return has_trigger or is_complex


def _build_messages(project_path: str, user_message: str) -> list[dict]:
    history = memory.load_history(project_path, limit=30)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        if msg["role"] != "system":
            messages.append(msg)
    messages.append({"role": "user", "content": user_message})
    return messages


def _check_permission(
    project_path: str,
    tool_name: str,
    args: dict,
    auto_allow_low_risk: bool,
    denied_tools: set,
) -> tuple[bool, str]:
    """
    Returns: (allowed, reason)
    """
    # Already always-allowed?
    if memory.is_always_allowed(project_path, tool_name):
        return (True, "")

    # Already denied?
    tool_key = f"{tool_name}:{json.dumps(args, sort_keys=True)}"
    if tool_key in denied_tools:
        console.print(
            f"  [red]✗ {tool_name} — already denied, skip[/red]"
        )
        return (False, "Already denied by user earlier.")

    risk = TOOL_RISK.get(tool_name, "high")

    # Low risk auto-allow
    if risk == "low" and auto_allow_low_risk:
        console.print(
            f"  [dim]→ {TOOL_ICONS.get(tool_name,'🔧')} "
            f"{tool_name} (auto-allowed)[/dim]"
        )
        return (True, "")

    # User se poochho
    icon = TOOL_ICONS.get(tool_name, "🔧")
    decision, reason = tui.permission_prompt(tool_name, args, icon)

    if decision == "always":
        memory.set_always_allow(project_path, tool_name)
        console.print(
            f"  [dim]✓ '{tool_name}' always-allow mein add kiya[/dim]"
        )
        return (True, "")

    elif decision == "allow":
        return (True, "")

    elif decision == "deny_reason":
        console.print(f"  [yellow]Reason: {reason}[/yellow]")
        denied_tools.add(tool_key)
        return (False, reason)

    elif decision == "deny_all":
        # Special marker
        return (False, "__STOP_AGENT__")

    else:  # deny
        denied_tools.add(tool_key)
        return (False, "User ne deny kar diya.")


def _get_plan_from_llm(llm: BaseLLM, messages: list[dict]) -> str:
    """
    LLM se sirf plan mangao — tools nahi.
    """
    plan_messages = messages.copy()
    plan_messages[-1] = plan_messages[-1].copy()
    plan_messages[-1]["content"] = (
        messages[-1]["content"] +
        "\n\n[INSTRUCTION: Pehle sirf ek detailed plan banao "
        "markdown mein. Koi tool use mat karo abhi. "
        "Sirf plan text return karo.]"
    )
    try:
        response = llm.chat(plan_messages, tools=None)
        return response["content"]
    except Exception:
        return ""


def run_agent(
    project: dict,
    llm: BaseLLM,
    user_message: str,
    auto_allow_low_risk: bool = True,
):
    project_path = project["path"]

    from aashoo.agent.tools import set_project_context
    set_project_context(project_path)

    memory.save_message(project_path, "user", user_message)
    memory.upsert_project(project["name"], project_path)

    messages = _build_messages(project_path, user_message)
    denied_tools: set = set()

    console.print()

    # ═══════════════════════════════════════
    # STEP 1: Plan-first (complex tasks ke liye)
    # ═══════════════════════════════════════
    if _needs_plan(user_message):
        with console.status(
            "[dim]Plan bana raha hoon...[/dim]",
            spinner="dots"
        ):
            plan_text = _get_plan_from_llm(llm, messages)

        if plan_text:
            decision, feedback = tui.show_plan_approval(plan_text)

            if decision == "approve":
                # Plan approved — execute karo
                messages.append({
                    "role": "assistant",
                    "content": plan_text
                })
                messages.append({
                    "role": "user",
                    "content": (
                        "Plan approved hai. Ab is plan ke according "
                        "ek ek step execute karo."
                    )
                })

            elif decision == "edit":
                # User ne feedback diya
                messages.append({
                    "role": "assistant",
                    "content": plan_text
                })
                messages.append({
                    "role": "user",
                    "content": (
                        f"Plan mein yeh changes chahiye: {feedback}\n"
                        "Updated plan ke according kaam karo."
                    )
                })
                console.print(
                    f"[cyan]Feedback liya: {feedback}[/cyan]"
                )

            elif decision == "reject":
                if feedback:
                    messages[-1]["content"] = feedback
                    console.print(
                        f"[yellow]Plan reject. "
                        f"New direction: {feedback}[/yellow]"
                    )
                else:
                    console.print("[yellow]Plan reject kiya.[/yellow]")
                    return

    # ═══════════════════════════════════════
    # STEP 2: Agent execution loop
    # ═══════════════════════════════════════
    for iteration in range(MAX_ITERATIONS):
        with console.status(
            "[dim]Agent kaam kar raha hai...[/dim]",
            spinner="dots"
        ):
            try:
                response = llm.chat(messages, tools=TOOLS_SCHEMA)
            except Exception as e:
                err = str(e)
                if "tool_use_failed" in err or "tool_use" in err or "tool" in err:
                    try:
                        response = llm.chat(messages, tools=None)
                    except Exception as e2:
                        console.print(f"[red]Error: {e2}[/red]")
                        return
                else:
                    console.print(f"[red]LLM Error: {e}[/red]")
                    return

        content = response["content"]
        tool_calls = response["tool_calls"]

        # Final text answer
        if not tool_calls:
            if content:
                tui.print_agent_message(content)
                memory.save_message(
                    project_path, "assistant", content
                )
            return

        # Agent ka explanation/commentary
        if content and content.strip():
            tui.print_plan(content)

        messages.append({
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ],
        })

        # Tool calls process karo
        stop_agent = False

        for tc in tool_calls:
            if stop_agent:
                break

            func_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            icon = TOOL_ICONS.get(func_name, "🔧")

            # Path/cwd fix
            if func_name in ("run_command", "git_status",
                             "git_diff", "git_commit"):
                args["cwd"] = project_path

            if func_name == "list_directory":
                if not args.get("path") or \
                   args.get("path") in (".", "./", ""):
                    args["path"] = project_path
                else:
                    from pathlib import Path
                    p = Path(args["path"])
                    if not p.is_absolute():
                        args["path"] = str(
                            Path(project_path) / p
                        )

            tui.print_tool_call(func_name, args, icon)

            # Permission
            allowed, reason = _check_permission(
                project_path, func_name, args,
                auto_allow_low_risk, denied_tools
            )

            if reason == "__STOP_AGENT__":
                console.print(
                    "[red]Agent stopped by user.[/red]"
                )
                stop_agent = True
                result = "Agent stopped by user."

            elif not allowed:
                # Reason ke saath deny
                if reason and reason != "Already denied by user earlier.":
                    result = (
                        f"User ne '{func_name}' deny kiya. "
                        f"User ka message: '{reason}'. "
                        f"Is reason ke according alternative dhundho. "
                        f"Same tool dobara mat maango."
                    )
                    console.print(
                        f"  [yellow]→ Agent ko reason diya: "
                        f"{reason}[/yellow]"
                    )
                else:
                    result = (
                        f"User ne '{func_name}' deny kiya. "
                        f"Alternative approach lo. "
                        f"Same action dobara mat karo."
                    )

            else:
                # Execute
                func = AVAILABLE_FUNCTIONS.get(func_name)
                with console.status(
                    f"[dim]{icon} {func_name}...[/dim]",
                    spinner="dots"
                ):
                    result = (func(**args) if func
                              else f"Unknown tool: {func_name}")

                tui.print_tool_result(
                    func_name, str(result), icon
                )

                if func_name in ("write_file", "edit_file",
                                 "git_commit", "undo_last",
                                 "edit_file_lines"):
                    print_file_tree(project_path)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": func_name,
                "content": str(result),
            })

        if stop_agent:
            return

    console.print(
        "[yellow]⚠ Max iterations reach ho gaye.[/yellow]"
    )