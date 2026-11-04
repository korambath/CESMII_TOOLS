from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv(Path.home() / ".config" / ".env")

# Initialize Anthropic client
client = Anthropic()

MODEL = "claude-opus-5-5"

# A long server-side tool turn can pause; resume it at most this many times
MAX_CONTINUATIONS = 5

# --------------------------------------------------
# 2. Built-in (server) tools
#
# Anthropic runs these tools on its own servers, so there is
# no function to write and no tool result to send back.
# Each mode gets its own tool set. Code execution is kept
# separate from the web tools: the _20260318 web tools
# already run code to filter results, and a second sandbox
# can confuse the model.
#
# Add "response_inclusion": "excluded" to a web tool to drop
# the raw results the filtering code already used. They
# stay in by default here so you can see them.
# --------------------------------------------------

MODES = {
    "search": {
        "description": "Web search: Claude searches the internet and cites sources",
        "tools": [{"type": "web_search_20260318", "name": "web_search", "max_uses": 5}],
        "system": "Use web search for anything current. Cite your sources.",
        "example": "What is Anthropic's latest model release? Answer in one sentence.",
    },
    "fetch": {
        "description": "Web fetch: Claude reads the full content of a URL you give it",
        "tools": [{"type": "web_fetch_20260318", "name": "web_fetch", "max_uses": 5}],
        "system": "Use web fetch to read any URL the user gives you before answering.",
        "example": "Summarize https://www.anthropic.com/news in three bullet points.",
    },
    "code": {
        "description": "Code execution: Claude writes and runs Python in a sandbox",
        "tools": [{"type": "code_execution_20260120", "name": "code_execution"}],
        "system": "Run code to compute answers instead of working them out by hand.",
        "example": "Calculate the mean and standard deviation of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]",
    },
}


def shorten(text: str, limit: int = 300) -> str:
    """Trim long tool inputs and outputs for display."""
    text = str(text).strip()
    return text if len(text) <= limit else text[:limit] + " ..."


# --------------------------------------------------
# 3. Display one response block
# --------------------------------------------------


def show_block(block, previous_type: str | None) -> None:
    """Print a response block."""
    if block.type == "thinking":
        if block.thinking:
            print(f"\n[Thinking] {block.thinking}")

    elif block.type == "server_tool_use":
        if block.name == "code_execution":
            # The web tools run code to filter results before Claude reads them
            print("\n[Filtering] Claude ran code over the web results")
        else:
            # The tool call Claude made (query, URL, or command)
            print(f"\n[Tool call] {block.name} — {shorten(block.input)}")

    elif block.type == "web_search_tool_result":
        if isinstance(block.content, list):
            print(f"[Search results] {len(block.content)} found")
            for result in block.content[:5]:
                print(f"  - {result.title} ({result.url})")
        else:
            print(f"[Search error] {block.content.error_code}")

    elif block.type == "web_fetch_tool_result":
        result = block.content
        if result.type == "web_fetch_result":
            title = getattr(result.content, "title", None) or "untitled"
            print(f"[Fetched] {title} ({result.url})")
        else:
            print(f"[Fetch error] {result.error_code}")

    elif block.type == "bash_code_execution_tool_result":
        result = block.content
        if result.type == "bash_code_execution_result":
            if result.stdout:
                print(f"[stdout]\n{shorten(result.stdout, 2000)}")
            if result.return_code != 0:
                print(f"[stderr] (exit {result.return_code})\n{shorten(result.stderr, 2000)}")
        else:
            print(f"[Code execution error] {result.error_code}")

    elif block.type == "text_editor_code_execution_tool_result":
        print(f"[File operation] {block.content.type}")

    elif block.type == "text":
        # With the web tools, the answer arrives split into several
        # text blocks, so print them back to back as one paragraph
        if previous_type != "text":
            print()
        print(block.text, end="")


# --------------------------------------------------
# 4. Interactive loop
# --------------------------------------------------


def print_help() -> None:
    print("\nCommands:")
    for name, mode in MODES.items():
        print(f"  /{name:<7} {mode['description']}")
    print("  /reset   Start a new conversation in the current mode")
    print("  quit     Exit")


def main() -> None:
    print("Built-in tools demo (web search, web fetch, code execution)")
    print_help()

    mode = "search"
    history: list[dict] = []
    container_id: str | None = None  # code mode reuses its sandbox across turns

    print(f"\nMode: {mode}. Try: {MODES[mode]['example']}")

    while True:
        try:
            user_input = input(f"\n[{mode}] You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print("\nGoodbye!")
            break

        # Switching mode changes the tools, so start a fresh conversation
        command = user_input.lower().lstrip("/")
        if user_input.startswith("/") and command in MODES:
            mode = command
            history = []
            container_id = None
            print(f"Mode: {mode}. Try: {MODES[mode]['example']}")
            continue

        if user_input.lower() == "/reset":
            history = []
            container_id = None
            print("Conversation cleared.")
            continue

        if user_input.startswith("/"):
            print_help()
            continue

        # Keep the history append-only so thinking blocks stay valid
        turn_start = len(history)
        history.append({"role": "user", "content": user_input})

        try:
            for _ in range(MAX_CONTINUATIONS + 1):
                extra = {"container": container_id} if container_id else {}
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=16000,
                    thinking={"type": "adaptive", "display": "summarized"},
                    output_config={"effort": "medium"},
                    system=MODES[mode]["system"],
                    tools=MODES[mode]["tools"],
                    messages=history,
                    **extra,
                )

                if response.container:
                    container_id = response.container.id

                previous_type = None
                for block in response.content:
                    if block.type != "text" and previous_type == "text":
                        print()
                    show_block(block, previous_type)
                    previous_type = block.type
                print()

                if response.stop_reason == "refusal":
                    del history[turn_start:]
                    print("\nClaude declined to answer that request.")
                    break

                history.append({"role": "assistant", "content": response.content})

                # The server stopped its tool loop early. Sending the
                # history back as-is lets it resume where it left off.
                if response.stop_reason != "pause_turn":
                    break
            else:
                print("\n(Stopped: the turn was still paused after several continuations.)")

        except Exception as err:
            del history[turn_start:]
            print(f"\nError: {err}")


if __name__ == "__main__":
    main()
