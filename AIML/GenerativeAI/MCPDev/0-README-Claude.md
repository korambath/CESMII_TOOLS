
# Instructions to Install MCP Server Client and Run the Weather Example

**References:**
- [Reference 1](https://github.com/modelcontextprotocol/quickstart-resources/tree/main)
- [Reference 2](https://modelcontextprotocol.io/quickstart/server)

---

## Steps

1. **Install `uv`:**

   ```sh
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   This will install `uv` in `~/.local/bin/uv`.

2. **Update `uv`:**

   ```sh
   uv self update
   ```

   Example output:
   ```
   info: Checking for updates...
   success: You're on the latest version of uv (v0.7.14)
   ```

3. **Create a new project directory:**

   ```sh
   mkdir MCPDev
   cd MCPDev
   ```

4. **Initialize a new project:**

   ```sh
   uv init mcpsrcclt
   ```

   Output:
   ```
   Initialized project `mcpsrvclt` at `<PATH>/MCPDev/mcpsrvclt`
   ```

5. **List project files:**

   ```sh
   ls -a mcpsrvclt
   ```

   Output:
   ```
   .		..		.git		.gitignore	.python-version	main.py		pyproject.toml	README.md
   ```

6. **Create a virtual environment:**

   ```sh
   uv venv
   ```

7. **Activate the virtual environment:**

   ```sh
   source .venv/bin/activate
   ```

8. **(Optional) Specify Python version:**

   ```sh
   uv venv --python 3.13
   ```

   Output:
   ```
   Using CPython 3.13.5
   Creating virtual environment at: .venv
   Activate with: source .venv/bin/activate
   ```

9. **Update `pyproject.toml`:**

   Edit `pyproject.toml` and set:

   ```
   requires-python = ">=3.13"
   ```

10. **Activate the virtual environment (again, if needed):**

    ```sh
    source .venv/bin/activate
    ```

11. **Pin Python version:**

    ```sh
    uv python pin 3.13
    ```

    Output:
    ```
    Updated `.python-version` from `3.11` -> `3.13`
    ```

12. **Verify Python version:**

    ```sh
    echo 'import sys; print(sys.version)' | uv run -
    ```

    Example output:
    ```
    3.13.5 (main, Jun 12 2025, 12:22:43) [Clang 20.1.4 ]
    ```

13. **Check Python version:**

    ```sh
    python --version
    ```

14. **Install MCP CLI:**

    ```sh
    uv add "mcp[cli]"
    ```

15. **Install `requests`:**

    ```sh
    uv add requests
    ```

16. **Install `openai-agents`:**

    ```sh
    uv add openai-agents
    ```

17. **Install `google-genai`:**

    ```sh
    uv add google-genai
    ```

18. **Install `geopy`:**

    ```sh
    uv add geopy
    ```

19. **Create source directories and download the weather example:**

    ```sh
    mkdir src
    cd src
    mkdir Ex0
    cd Ex0
    wget https://raw.githubusercontent.com/modelcontextprotocol/quickstart-resources/refs/heads/main/weather-server-python/weather.py
    ```

    - [Ref: https://github.com/modelcontextprotocol/quickstart-resources/tree/main]
    - [Ref: https://modelcontextprotocol.io/quickstart/server]

20. **Test the weather example:**

    ```sh
    uv run weather.py
    ```

    No output is expected. Use `CTRL-C` to stop.

21. **Install Claude Desktop**

22. **Update the configuration file:**

    Edit the file:

    ```
    ~/Library/Application\ Support/Claude/claude_desktop_config.json
    ```

    Add or update the following section:

    ```json
    {
      "mcpServers": {
        "weather": {
          "command": "/Users/<Change>/.local/bin/uv",
          "args": [
            "--directory",
            "/Users/<Change>/MCPDev/mcpsrvclt/src/Ex0",
            "run",
            "weather.py"
          ]
        }
      }
    }
    ```

---

**References:**
- [Reference 1](https://github.com/modelcontextprotocol/quickstart-resources/tree/main)
- [Reference 2](https://modelcontextprotocol.io/quickstart/server)