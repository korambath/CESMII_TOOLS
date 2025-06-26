
# Enabling and Configuring MCP Servers in VS Code

Reference: [VS Code Copilot MCP Servers Documentation](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)

---

## 1. Enable MCP Support in VS Code

To enable MCP support in VS Code, set the `chat.mcp.enabled` setting in your `settings.json` file.

Path to settings file (on macOS):

```
~/Library/Application\ Support/Code/User/settings.json
```

Add or ensure the following entry:

```json
{
    "chat.mcp.discovery.enabled": true
}
```

---

## 2. Add an MCP Server to Your Workspace

- Create a `.vscode/mcp.json` file in your workspace.
- In VS Code, click **"Add Server"** (select the `mcp.json` package).
- Select **NPM package**.
- Type `@playwright/mcp`, press Enter, and Allow when prompted.

---

## 3. Example: Add the Claude Example

Your `.vscode/mcp.json` might look like this:

```json
{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@latest"
      ]
    },
    "weather": {
      "command": "/Users/<change>/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/<change>/MCPDev/mcpsrvclt/src/Ex0",
        "run",
        "weather.py"
      ]
    }
  }
}
```

> **Note:**  
> Replace `<change>` with your actual username or relevant path.
```
