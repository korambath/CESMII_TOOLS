from pathlib import Path

from anthropic import Anthropic
from anthropic.lib import files_from_dir
from dotenv import load_dotenv

# --------------------------------------------------
# 1. Load environment variables
# --------------------------------------------------

load_dotenv(Path.home() / ".config" / ".env")

# Initialize Anthropic client
client = Anthropic()

MODEL = "claude-opus-5-5"

HERE = Path(__file__).resolve().parent

# The custom skill: a folder with SKILL.md at its root
SKILL_DIR = HERE / "status-report-skill"
SKILL_DISPLAY_NAME = "Status Report Generator"

# Sample input for the custom skill
SAMPLE_LOG = HERE / "sample-activity-log.txt"

# Files that skills create (slides, spreadsheets, ...) are saved here
OUTPUT_DIR = HERE / "skill_outputs"

# Anthropic's ready-made skills for documents
ANTHROPIC_SKILLS = ["docx", "xlsx", "pptx", "pdf"]

# A long skill turn can pause; resume it at most this many times
MAX_CONTINUATIONS = 5

# Skills run inside the code execution container
TOOLS = [{"type": "code_execution_20250825", "name": "code_execution"}]


# --------------------------------------------------
# 2. Upload the custom skill (once)
#
# Skills live in your workspace and are referenced by ID.
# Reuse the skill if it is already there, so each run
# doesn't upload a new copy.
# --------------------------------------------------


def find_custom_skill():
    for skill in client.skills.list(source="custom"):
        if skill.display_name == SKILL_DISPLAY_NAME:
            return skill
    return None


def get_or_create_skill() -> str:
    skill = find_custom_skill()
    if skill:
        print(f"Using your uploaded skill {skill.id}")
        return skill.id

    skill = client.skills.create(
        display_name=SKILL_DISPLAY_NAME,
        files=files_from_dir(SKILL_DIR),
    )
    print(f"Uploaded {SKILL_DIR.name} as skill {skill.id}")
    return skill.id


def upload_new_version(skill_id: str) -> None:
    """Upload the skill folder again after you edit SKILL.md."""
    version = client.skills.versions.create(
        skill_id=skill_id,
        files=files_from_dir(SKILL_DIR),
    )
    print(f"Uploaded new version {version.id}. Requests use \"latest\", so it applies now.")


def build_skills(custom_skill_id: str) -> list[dict]:
    # Claude sees only each skill's name and description up front,
    # and loads the full SKILL.md when a request needs it
    skills = [{"type": "custom", "skill_id": custom_skill_id, "version": "latest"}]
    skills += [
        {"type": "anthropic", "skill_id": name, "version": "latest"}
        for name in ANTHROPIC_SKILLS
    ]
    return skills


# --------------------------------------------------
# 3. Display the response and save created files
# --------------------------------------------------


def shorten(text: str, limit: int = 300) -> str:
    """Trim long tool inputs and outputs for display."""
    text = str(text).strip()
    return text if len(text) <= limit else text[:limit] + " ..."


def show_block(block) -> list[str]:
    """Print a response block. Return the IDs of any files it created."""
    file_ids: list[str] = []

    if block.type == "thinking":
        if block.thinking:
            print(f"\n[Thinking] {block.thinking}")

    elif block.type == "server_tool_use":
        command = block.input.get("command") or block.input.get("path") or block.input
        print(f"\n[{block.name}] {shorten(command)}")

    elif block.type == "bash_code_execution_tool_result":
        result = block.content
        if result.type == "bash_code_execution_result":
            if result.stdout:
                print(shorten(result.stdout, 1000))
            if result.return_code != 0:
                print(f"[stderr] (exit {result.return_code}) {shorten(result.stderr, 1000)}")
            file_ids += [f.file_id for f in result.content if f.type == "bash_code_execution_output"]
        else:
            print(f"[Code execution error] {result.error_code}")

    elif block.type == "text_editor_code_execution_tool_result":
        print(f"[file] {block.content.type}")

    elif block.type == "text":
        print(f"\n{block.text}")

    return file_ids


def save_file(file_id: str) -> None:
    """Download a file a skill created, using the Files API."""
    metadata = client.files.retrieve_metadata(file_id)
    # Keep only the base name so a file can't be written outside OUTPUT_DIR
    name = Path(metadata.filename).name
    if name in ("", ".", ".."):
        print(f"Skipping file with invalid name: {metadata.filename!r}")
        return
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / name
    client.files.download(file_id).write_to_file(path)
    print(f"[Saved] {path}")


# --------------------------------------------------
# 4. Interactive loop
# --------------------------------------------------


def print_help() -> None:
    print("\nAsk for anything; Claude picks the skill that fits. Commands:")
    print("  /sample   Send the sample activity log for a status report")
    print("  /update   Upload a new version of the skill after editing SKILL.md")
    print("  /reset    Start a new conversation and container")
    print("  /delete   Delete the custom skill from your workspace")
    print("  quit      Exit")


def main() -> None:
    print("Skills demo")
    print(f"Custom skill: {SKILL_DIR.name}. Anthropic skills: {', '.join(ANTHROPIC_SKILLS)}")

    custom_skill_id = get_or_create_skill()
    skills = build_skills(custom_skill_id)
    print_help()
    print("\nTry: /sample, or: Make a 3-slide deck about our holiday release plan")

    history: list[dict] = []
    container_id: str | None = None  # reused so later turns see earlier files

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        command = user_input.lower()

        if command in ("quit", "exit"):
            print("\nGoodbye!")
            break

        if command == "/reset":
            history = []
            container_id = None
            print("Conversation cleared.")
            continue

        if command == "/update":
            upload_new_version(custom_skill_id)
            continue

        if command == "/delete":
            confirm = input(f"Delete skill {custom_skill_id} and all its versions? (yes/no): ")
            if confirm.strip().lower() == "yes":
                # Deleting a skill also deletes all of its versions
                client.skills.delete(custom_skill_id)
                print("Skill deleted. Goodbye!")
                break
            continue

        if command == "/sample":
            user_input = "Write this week's status report:\n\n" + SAMPLE_LOG.read_text()
            print(f"(Sending {SAMPLE_LOG.name})")

        elif command.startswith("/"):
            print_help()
            continue

        # Keep the history append-only so thinking blocks stay valid
        turn_start = len(history)
        history.append({"role": "user", "content": user_input})

        try:
            for _ in range(MAX_CONTINUATIONS + 1):
                container = {"skills": skills}
                if container_id:
                    container["id"] = container_id

                response = client.messages.create(
                    model=MODEL,
                    max_tokens=16000,
                    thinking={"type": "adaptive", "display": "summarized"},
                    output_config={"effort": "medium"},
                    container=container,
                    tools=TOOLS,
                    messages=history,
                )

                if response.container:
                    container_id = response.container.id

                file_ids: list[str] = []
                for block in response.content:
                    file_ids += show_block(block)
                for file_id in file_ids:
                    save_file(file_id)

                if response.stop_reason == "refusal":
                    del history[turn_start:]
                    print("\nClaude declined to answer that request.")
                    break

                history.append({"role": "assistant", "content": response.content})

                # A long skill run paused. Sending the history back
                # with the same container lets it continue.
                if response.stop_reason != "pause_turn":
                    break
            else:
                print("\n(Stopped: the turn was still paused after several continuations.)")

        except Exception as err:
            del history[turn_start:]
            print(f"\nError: {err}")


if __name__ == "__main__":
    main()
