import dotenv from "dotenv";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import Anthropic, { toFile } from "@anthropic-ai/sdk";
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

const HERE = path.dirname(fileURLToPath(import.meta.url));

// The custom skill: a folder with SKILL.md at its root
const SKILL_DIR = path.join(HERE, "status-report-skill");
const SKILL_DISPLAY_NAME = "Status Report Generator";

// Sample input for the custom skill
const SAMPLE_LOG = path.join(HERE, "sample-activity-log.txt");

// Files that skills create (slides, spreadsheets, ...) are saved here
const OUTPUT_DIR = path.join(HERE, "skill_outputs");

// Anthropic's ready-made skills for documents
const ANTHROPIC_SKILLS = ["docx", "xlsx", "pptx", "pdf"];

// A long skill turn can pause; resume it at most this many times
const MAX_CONTINUATIONS = 5;

// Skills run inside the code execution container
const TOOLS: Anthropic.Messages.ToolUnion[] = [
  { type: "code_execution_20250825", name: "code_execution" },
];

// --------------------------------------------------
// 2. Upload the custom skill (once)
//
// Skills live in your workspace and are referenced by ID.
// Reuse the skill if it is already there, so each run
// doesn't upload a new copy.
// --------------------------------------------------

async function filesFromDir(dir: string) {
  // Every file keeps the folder name as its prefix
  // (status-report-skill/SKILL.md, status-report-skill/scripts/...)
  const entries = await readdir(dir, { recursive: true, withFileTypes: true });
  const base = path.basename(dir);
  return Promise.all(
    entries
      .filter((entry) => entry.isFile())
      .map(async (entry) => {
        const fullPath = path.join(entry.parentPath, entry.name);
        const name = path.posix.join(base, ...path.relative(dir, fullPath).split(path.sep));
        return toFile(await readFile(fullPath), name);
      })
  );
}

async function getOrCreateSkill(): Promise<string> {
  for await (const skill of client.skills.list({ source: "custom" })) {
    if (skill.display_name === SKILL_DISPLAY_NAME) {
      console.log(`Using your uploaded skill ${skill.id}`);
      return skill.id;
    }
  }

  const skill = await client.skills.create({
    display_name: SKILL_DISPLAY_NAME,
    files: await filesFromDir(SKILL_DIR),
  });
  console.log(`Uploaded ${path.basename(SKILL_DIR)} as skill ${skill.id}`);
  return skill.id;
}

async function uploadNewVersion(skillId: string): Promise<void> {
  // Upload the skill folder again after you edit SKILL.md
  const version = await client.skills.versions.create(skillId, {
    files: await filesFromDir(SKILL_DIR),
  });
  console.log(`Uploaded new version ${version.id}. Requests use "latest", so it applies now.`);
}

function buildSkills(customSkillId: string): Anthropic.Messages.SkillParams[] {
  // Claude sees only each skill's name and description up front,
  // and loads the full SKILL.md when a request needs it
  return [
    { type: "custom", skill_id: customSkillId, version: "latest" },
    ...ANTHROPIC_SKILLS.map((name) => ({
      type: "anthropic" as const,
      skill_id: name,
      version: "latest",
    })),
  ];
}

// --------------------------------------------------
// 3. Display the response and save created files
// --------------------------------------------------

function shorten(value: unknown, limit = 300): string {
  // Trim long tool inputs and outputs for display
  const text = (typeof value === "string" ? value : JSON.stringify(value)).trim();
  return text.length <= limit ? text : text.slice(0, limit) + " ...";
}

function showBlock(block: Anthropic.Messages.ContentBlock): string[] {
  // Print a response block. Return the IDs of any files it created.
  const fileIds: string[] = [];

  switch (block.type) {
    case "thinking":
      if (block.thinking) console.log(`\n[Thinking] ${block.thinking}`);
      break;

    case "server_tool_use": {
      const toolInput = block.input as Record<string, unknown>;
      console.log(`\n[${block.name}] ${shorten(toolInput.command ?? toolInput.path ?? toolInput)}`);
      break;
    }

    case "bash_code_execution_tool_result": {
      const result = block.content;
      if (result.type === "bash_code_execution_result") {
        if (result.stdout) console.log(shorten(result.stdout, 1000));
        if (result.return_code !== 0) {
          console.log(`[stderr] (exit ${result.return_code}) ${shorten(result.stderr, 1000)}`);
        }
        for (const item of result.content) {
          if (item.type === "bash_code_execution_output") fileIds.push(item.file_id);
        }
      } else {
        console.log(`[Code execution error] ${result.error_code}`);
      }
      break;
    }

    case "text_editor_code_execution_tool_result":
      console.log(`[file] ${block.content.type}`);
      break;

    case "text":
      console.log(`\n${block.text}`);
      break;
  }

  return fileIds;
}

async function saveFile(fileId: string): Promise<void> {
  // Download a file a skill created, using the Files API
  const metadata = await client.files.retrieveMetadata(fileId);
  // Keep only the base name so a file can't be written outside OUTPUT_DIR
  const name = path.basename(metadata.filename);
  if (!name || name === "." || name === "..") {
    console.log(`Skipping file with invalid name: ${JSON.stringify(metadata.filename)}`);
    return;
  }
  await mkdir(OUTPUT_DIR, { recursive: true });
  const filePath = path.join(OUTPUT_DIR, name);
  const response = await client.files.download(fileId);
  await writeFile(filePath, Buffer.from(await response.arrayBuffer()));
  console.log(`[Saved] ${filePath}`);
}

// --------------------------------------------------
// 4. Interactive loop
// --------------------------------------------------

function printHelp(): void {
  console.log("\nAsk for anything; Claude picks the skill that fits. Commands:");
  console.log("  /sample   Send the sample activity log for a status report");
  console.log("  /update   Upload a new version of the skill after editing SKILL.md");
  console.log("  /reset    Start a new conversation and container");
  console.log("  /delete   Delete the custom skill from your workspace");
  console.log("  quit      Exit");
}

const rl = readline.createInterface({ input, output });

console.log("Skills demo");
console.log(
  `Custom skill: ${path.basename(SKILL_DIR)}. Anthropic skills: ${ANTHROPIC_SKILLS.join(", ")}`
);

const customSkillId = await getOrCreateSkill();
const skills = buildSkills(customSkillId);
printHelp();
console.log("\nTry: /sample, or: Make a 3-slide deck about our holiday release plan");

let history: Anthropic.Messages.MessageParam[] = [];
let containerId: string | undefined; // reused so later turns see earlier files

while (true) {
  let userInput = (await rl.question("\nYou: ")).trim();

  if (!userInput) continue;

  const command = userInput.toLowerCase();

  if (["quit", "exit"].includes(command)) {
    console.log("\nGoodbye!");
    break;
  }

  if (command === "/reset") {
    history = [];
    containerId = undefined;
    console.log("Conversation cleared.");
    continue;
  }

  if (command === "/update") {
    await uploadNewVersion(customSkillId);
    continue;
  }

  if (command === "/delete") {
    const confirm = await rl.question(
      `Delete skill ${customSkillId} and all its versions? (yes/no): `
    );
    if (confirm.trim().toLowerCase() === "yes") {
      // Deleting a skill also deletes all of its versions
      await client.skills.delete(customSkillId);
      console.log("Skill deleted. Goodbye!");
      break;
    }
    continue;
  }

  if (command === "/sample") {
    userInput = "Write this week's status report:\n\n" + (await readFile(SAMPLE_LOG, "utf8"));
    console.log(`(Sending ${path.basename(SAMPLE_LOG)})`);
  } else if (command.startsWith("/")) {
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
        container: containerId ? { id: containerId, skills } : { skills },
        tools: TOOLS,
        messages: history,
      });

      if (response.container) containerId = response.container.id;

      const fileIds = response.content.flatMap(showBlock);
      for (const fileId of fileIds) await saveFile(fileId);

      if (response.stop_reason === "refusal") {
        history.splice(turnStart);
        console.log("\nClaude declined to answer that request.");
        paused = false;
        break;
      }

      history.push({ role: "assistant", content: response.content });

      // A long skill run paused. Sending the history back
      // with the same container lets it continue.
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
