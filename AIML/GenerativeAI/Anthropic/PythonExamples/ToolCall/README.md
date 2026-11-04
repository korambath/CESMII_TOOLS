# Claude tool use examples

Three interactive command-line programs that show how Claude uses tools and skills. Each one comes in Python and TypeScript, and the two versions behave the same way.

| Program | Files | Kind of tool |
|---|---|---|
| Weather assistant | `multiToolCalls.py`, `multiToolCalls.ts` | **Client tools**: functions in your code that Claude asks you to run |
| Built-in tools demo | `builtintoolsexamples.py`, `builtintoolsexamples.ts` | **Server tools**: tools Anthropic runs for you (web search, web fetch, code execution) |
| Skills demo | `skillsexample.py`, `skillsexample.ts` | **Skills**: instructions and scripts Claude loads when a task needs them |

Both programs use `claude-opus-5-5` with adaptive thinking. Claude's thinking summaries print as `[Thinking] ...` lines.

## Setup

### API key

Both programs load environment variables from `~/.config/.env`. That file needs your Anthropic API key:

```
ANTHROPIC_API_KEY=your-key-here
```

### Python

Use Python 3.13 or later. The dependencies (`anthropic`, `python-dotenv`, and `httpx`, which comes with `anthropic`) are already in the project's `pyproject.toml`. Run the programs with `uv` from the project root (`avappsdev`):

```bash
uv run python src-tools/multiToolCalls.py
```

```bash
uv run python src-tools/builtintoolsexamples.py
```

```bash
uv run python src-tools/skillsexample.py
```

### TypeScript

You need Node.js and `tsx`. Install the packages in the folder you run from:

```bash
npm install @anthropic-ai/sdk zod dotenv
```

The files use top-level `await`, so Node has to treat them as ES modules. Add a `package.json` with `"type": "module"` next to them. Otherwise `tsx` fails with "Top-level await is currently not supported with the cjs output format".

```json
{ "type": "module" }
```

Then run:

```bash
tsx multiToolCalls.ts
```

```bash
tsx builtintoolsexamples.ts
```

```bash
tsx skillsexample.ts
```

The skills demo also needs `status-report-skill/` and `sample-activity-log.txt` next to `skillsexample.ts`.

To type-check without running:

```bash
npx tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --skipLibCheck multiToolCalls.ts builtintoolsexamples.ts skillsexample.ts
```

## Weather assistant (`multiToolCalls`)

A chat assistant for weather and local time in any city. On startup it detects your machine's timezone and lets you pick another one. Times are then shown in both the city's timezone and yours.

### Tools

Each tool is a function in the file. Claude decides which ones to call and the SDK tool runner runs them.

| Tool | What it does | Data source |
|---|---|---|
| `get_weather` | Current conditions: temperature, humidity, precipitation, wind speed | Open-Meteo forecast API |
| `get_forecast` | 3-day forecast: highs and lows, precipitation and its chance, wind, weather code | Open-Meteo forecast API |
| `get_time_of_day` | Local time and whether it is morning, afternoon, evening or night | Open-Meteo (for the city's timezone) |
| `get_weather_alerts` | Weather alerts for the next 3 days (see below) | Open-Meteo daily forecast |

City names are converted to coordinates with the OpenStreetMap Nominatim geocoder. Neither service needs an API key. Every web request times out after 15 seconds.

### Weather alerts

Open-Meteo has no official alerts feed, so `get_weather_alerts` works the alerts out from the forecast numbers. The thresholds roughly follow US National Weather Service criteria:

| Alert | Advisory | Warning |
|---|---|---|
| Thunderstorm or hail | – | weather code 95 / 96 / 99 |
| Freezing rain or drizzle | – | weather code 56 / 57 / 66 / 67 |
| Fog or freezing fog | weather code 45 / 48 | – |
| Heavy rain | 25 mm or more, or a heavy-rain weather code | 50 mm or more |
| Snow | 5 cm or more | 15 cm or more |
| Wind gusts | 45 mph or more | 58 mph or more |
| Heat (feels-like) | 100°F or more | 105°F or more |
| Cold (feels-like) | 0°F or below | −15°F or below |
| UV index | 8 or more | 11 or more |

To change them, edit `check_day_for_alerts` (Python) or `checkDayForAlerts` (TypeScript). Every result is marked as derived from the forecast, and Claude is told to say they are not official warnings and to point you to your local weather service. These alerts can't cover things the forecast doesn't show, such as flash floods, air quality or wildfires.

### Example questions

```
Weather in LA
Forecast for NYC
What time is it in Tokyo?
Any weather alerts for Phoenix?
What about Tokyo?          <- follow-ups reuse the last city
```

Type `quit` or `exit` to stop.

## Built-in tools demo (`builtintoolsexamples`)

An interactive version of the examples in the Claude Platform 101 course lesson [Built-in tools](https://academy.claude.com/courses/claude-platform-101/built-in-tools), with web fetch added. Anthropic runs these tools on its own servers, so there is no tool function to write and no result to send back. The answer comes back in the same response.

### Modes

| Command | Tool | What Claude does |
|---|---|---|
| `/search` (default) | `web_search_20260318` | Searches the web |
| `/fetch` | `web_fetch_20260318` | Reads the full content of a URL you give it |
| `/code` | `code_execution_20260120` | Writes and runs Python or shell commands in a sandbox |
| `/reset` | – | Starts a new conversation in the current mode |
| `quit` | – | Exits |

Each mode keeps its conversation, so follow-up questions work. Switching mode starts a new conversation because the tools change. In code mode the sandbox is reused between questions, so a follow-up can use files from earlier.

### Example questions

```
[search] What is Anthropic's latest model release? Answer in one sentence.
[fetch]  Summarize https://www.anthropic.com/news in three bullet points.
[code]   Calculate the mean and standard deviation of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
[code]   Now save those numbers to data.txt and print the file
```

### What the output shows

| Line | Meaning |
|---|---|
| `[Tool call] web_search — {...}` | The query, URL or command Claude used |
| `[Search results]` / `[Fetched]` | What came back from the web |
| `[Filtering]` | The web tools ran code to keep only the relevant parts of the results (dynamic filtering) |
| `[stdout]` / `[stderr]` | Output of code Claude ran in the sandbox |

### Notes on these tool versions

- **Dynamic filtering.** The `20260209` and later web tools let Claude run code over results before reading them. That's why code execution is not added alongside them: they already have their own sandbox, and a second one can confuse Claude.
- **`response_inclusion`.** New in `20260318`. Setting `"response_inclusion": "excluded"` on a web tool drops raw results the filtering already used, which saves output tokens. The demo leaves it on the default, `"full"`, so you can see the results.
- **Citations.** With dynamic filtering, the `citations` field on text blocks came back empty in testing. The answer arrives split into several text blocks, which the demo prints as one paragraph, and Claude includes source links in the text.
- **Paused turns.** A long server-side turn can stop with `stop_reason: "pause_turn"`. The demo sends the conversation back so the server continues, up to 5 times.

## Skills demo (`skillsexample`)

An interactive version of the Claude Platform 101 course lesson [Skills](https://academy.claude.com/courses/claude-platform-101/skills). The lesson refers to a `src/lesson-08-skills.ts` file that isn't published, so this is written from the lesson and the [Skills guide](https://platform.claude.com/docs/en/build-with-claude/skills-guide).

A skill is a folder with a `SKILL.md` file, plus optional scripts and resources. A tool defines what Claude *can* do. A skill describes *how* you want a task done, such as a report format or a review checklist. Claude starts with only each skill's name and description, and loads the full `SKILL.md` when a request needs it.

### What it does

On startup the demo uploads the custom skill in `status-report-skill/` to your Anthropic workspace as "Status Report Generator". If a skill with that name is already there, it reuses it, so you don't get a new copy each run. Each request then attaches five skills through the `container` parameter:

| Skill | Type | Use |
|---|---|---|
| `status-report` | custom (this folder) | Turns an activity log into a weekly status report in a fixed format |
| `docx`, `xlsx`, `pptx`, `pdf` | Anthropic | Create Word, Excel, PowerPoint and PDF files |

Claude picks the one that fits each request. Skills run inside the code execution container, so every request includes the `code_execution_20250825` tool. Skills are generally available, so this uses the regular `client.messages.create` with no beta header.

Files that a skill creates are downloaded with the Files API into `skill_outputs/`. The container is reused between questions, so a follow-up can work on a file made earlier.

### The custom skill

```
status-report-skill/
├── SKILL.md              # name, description, steps, report format and rules
└── scripts/
    └── log_stats.py      # counts done / in progress / blocked items in a log
```

`SKILL.md` tells Claude to save the log, run `scripts/log_stats.py` to count items, then write the report with fixed sections (Summary, Done this week, In progress, Blockers, Next week) and a rule for the overall status. The format comes from the skill, so your prompt only has to supply the log.

To change the report, edit `SKILL.md` and type `/update` to upload a new version. Requests use `"version": "latest"`, so the change applies right away.

### Commands

| Command | What it does |
|---|---|
| `/sample` | Sends `sample-activity-log.txt` and asks for a status report |
| `/update` | Uploads a new version of the skill from the folder |
| `/reset` | Starts a new conversation and container |
| `/delete` | Deletes the custom skill and all its versions from your workspace (asks first) |
| `quit` | Exits |

### Example questions

```
/sample
Now turn that report into a 3-slide pptx deck
Make a spreadsheet of the blockers with owner and days open
```

## How conversation history works

All three programs keep the full conversation, including tool calls, tool results and thinking blocks, and only ever add to it. This matters for two reasons:

- Follow-ups such as "what about tomorrow?" need the earlier turns.
- Claude's thinking blocks are signed and tied to the exact conversation that produced them. If earlier turns are edited or left out, the API rejects the request with a 400 error ("Invalid `signature` in `thinking` block").

If a request fails or Claude declines, that turn is removed from the history so the next question starts clean.

## Costs

Every question is a paid API call. On top of token costs, web search is charged at $10 per 1,000 searches. Code execution is free when used through the web tools' filtering, and is billed by container time when used directly, after a monthly free allowance.
