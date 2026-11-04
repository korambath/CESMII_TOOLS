import dotenv from "dotenv";
import os from "node:os";
import path from "node:path";
import Anthropic from "@anthropic-ai/sdk";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";

// --------------------------------------------------
// 1. Load environment variables
// --------------------------------------------------

dotenv.config({
  path: path.join(os.homedir(), ".config", ".env"),
});

// Initialize Anthropic client
const client = new Anthropic();

const MODEL = "claude-opus-5-5";

// A long server-side tool turn can pause; resume it at most this many times
const MAX_CONTINUATIONS = 5;

// --------------------------------------------------
// 2. Built-in (server) tools
//
// Anthropic runs these tools on its own servers, so there is
// no function to write and no tool result to send back.
// Each mode gets its own tool set. Code execution is kept
// separate from the web tools: the _20260318 web tools
// already run code to filter results, and a second sandbox
// can confuse the model.
//
// Add "response_inclusion": "excluded" to a web tool to drop
// the raw results the filtering code already used. They
// stay in by default here so you can see them.
// --------------------------------------------------

type ModeName = "search" | "fetch" | "code";

interface Mode {
  description: string;
  system: string;
  tools: Anthropic.Messages.ToolUnion[];
  example: string;
}

const MODES: Record<ModeName, Mode> = {
  search: {
    description: "Web search: Claude searches the internet and cites sources",
    system: "Use web search for anything current. Cite your sources.",
    tools: [{ type: "web_search_20260318", name: "web_search", max_uses: 5 }],
    example: "What is Anthropic's latest model release? Answer in one sentence.",
  },
  fetch: {
    description: "Web fetch: Claude reads the full content of a URL you give it",
    system: "Use web fetch to read any URL the user gives you before answering.",
    tools: [{ type: "web_fetch_20260318", name: "web_fetch", max_uses: 5 }],
    example: "Summarize https://www.anthropic.com/news in three bullet points.",
  },
  code: {
    description: "Code execution: Claude writes and runs Python in a sandbox",
    system: "Run code to compute answers instead of working them out by hand.",
    tools: [{ type: "code_execution_20260120", name: "code_execution" }],
    example:
      "Calculate the mean and standard deviation of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]",
  },
};

function shorten(value: unknown, limit = 300): string {
  // Trim long tool inputs and outputs for display
  const text = (typeof value === "string" ? value : JSON.stringify(value)).trim();
  return text.length <= limit ? text : text.slice(0, limit) + " ...";
}

// --------------------------------------------------
// 3. Display one response block
// --------------------------------------------------

function showBlock(
  block: Anthropic.Messages.ContentBlock,
  previousType: string | undefined
): void {
  switch (block.type) {
    case "thinking":
      if (block.thinking) console.log(`\n[Thinking] ${block.thinking}`);
      break;

    case "server_tool_use":
      if (block.name === "code_execution") {
        // The web tools run code to filter results before Claude reads them
        console.log("\n[Filtering] Claude ran code over the web results");
      } else {
        // The tool call Claude made (query, URL, or command)
        console.log(`\n[Tool call] ${block.name} — ${shorten(block.input)}`);
      }
      break;

    case "web_search_tool_result":
      if (Array.isArray(block.content)) {
        console.log(`[Search results] ${block.content.length} found`);
        for (const result of block.content.slice(0, 5)) {
          console.log(`  - ${result.title} (${result.url})`);
        }
      } else {
        console.log(`[Search error] ${block.content.error_code}`);
      }
      break;

    case "web_fetch_tool_result": {
      const result = block.content;
      if (result.type === "web_fetch_result") {
        console.log(`[Fetched] ${result.content.title ?? "untitled"} (${result.url})`);
      } else {
        console.log(`[Fetch error] ${result.error_code}`);
      }
      break;
    }

    case "bash_code_execution_tool_result": {
      const result = block.content;
      if (result.type === "bash_code_execution_result") {
        if (result.stdout) console.log(`[stdout]\n${shorten(result.stdout, 2000)}`);
        if (result.return_code !== 0) {
          console.log(
            `[stderr] (exit ${result.return_code})\n${shorten(result.stderr, 2000)}`
          );
        }
      } else {
        console.log(`[Code execution error] ${result.error_code}`);
      }
      break;
    }

    case "text_editor_code_execution_tool_result":
      console.log(`[File operation] ${block.content.type}`);
      break;

    case "text":
      // With the web tools, the answer arrives split into several
      // text blocks, so print them back to back as one paragraph
      if (previousType !== "text") process.stdout.write("\n");
      process.stdout.write(block.text);
      break;
  }
}

// --------------------------------------------------
// 4. Interactive loop
// --------------------------------------------------

function printHelp(): void {
  console.log("\nCommands:");
  for (const [name, mode] of Object.entries(MODES)) {
    console.log(`  /${name.padEnd(7)} ${mode.description}`);
  }
  console.log("  /reset   Start a new conversation in the current mode");
  console.log("  quit     Exit");
}

const rl = readline.createInterface({ input, output });

console.log("Built-in tools demo (web search, web fetch, code execution)");
printHelp();

let mode: ModeName = "search";
let history: Anthropic.Messages.MessageParam[] = [];
let containerId: string | undefined; // code mode reuses its sandbox across turns

console.log(`\nMode: ${mode}. Try: ${MODES[mode].example}`);

while (true) {
  const userInput = (await rl.question(`\n[${mode}] You: `)).trim();

  if (!userInput) continue;

  if (["quit", "exit"].includes(userInput.toLowerCase())) {
    console.log("\nGoodbye!");
    break;
  }

  // Switching mode changes the tools, so start a fresh conversation
  const command = userInput.toLowerCase().replace(/^\//, "");
  if (userInput.startsWith("/") && command in MODES) {
    mode = command as ModeName;
    history = [];
    containerId = undefined;
    console.log(`Mode: ${mode}. Try: ${MODES[mode].example}`);
    continue;
  }

  if (userInput.toLowerCase() === "/reset") {
    history = [];
    containerId = undefined;
    console.log("Conversation cleared.");
    continue;
  }

  if (userInput.startsWith("/")) {
    printHelp();
    continue;
  }

  // Keep the history append-only so thinking blocks stay valid
  const turnStart = history.length;
  history.push({ role: "user", content: userInput });

  try {
    let paused = false;

    for (let attempt = 0; attempt <= MAX_CONTINUATIONS; attempt++) {
      const response = await client.messages.create({
        model: MODEL,
        max_tokens: 16000,
        thinking: { type: "adaptive", display: "summarized" },
        output_config: { effort: "medium" },
        system: MODES[mode].system,
        tools: MODES[mode].tools,
        messages: history,
        ...(containerId ? { container: containerId } : {}),
      });

      if (response.container) containerId = response.container.id;

      let previousType: string | undefined;
      for (const block of response.content) {
        if (block.type !== "text" && previousType === "text") console.log();
        showBlock(block, previousType);
        previousType = block.type;
      }
      console.log();

      if (response.stop_reason === "refusal") {
        history.splice(turnStart);
        console.log("\nClaude declined to answer that request.");
        paused = false;
        break;
      }

      history.push({ role: "assistant", content: response.content });

      // The server stopped its tool loop early. Sending the
      // history back as-is lets it resume where it left off.
      paused = response.stop_reason === "pause_turn";
      if (!paused) break;
    }

    if (paused) {
      console.log("\n(Stopped: the turn was still paused after several continuations.)");
    }
  } catch (err) {
    history.splice(turnStart);
    console.error("\nError:", err instanceof Error ? err.message : err);
  }
}

rl.close();
