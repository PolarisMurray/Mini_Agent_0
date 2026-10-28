# Mini_Agent

A minimal coding agent built from scratch in Python on top of the OpenAI SDK (talking to DeepSeek).
It has tool calling, a plan mode, skills, and long-term memory. Context compaction, permissions and a sandbox are in progress.

## Architecture

<p align="center">
  <img src="docs/architecture.svg" alt="Mini Agent architecture: session, agent loop, tools, and plan mode" width="100%">
</p>

**Session ([main.py](src/main.py)).**
When a session starts, the system prompt is built once from three parts: the base prompt, the skill index from `skills/`, and the long-term facts in `memory.md`.
After that, each query either goes to the agent loop or, if it starts with `/plan`, to plan mode.
Empty input ends the session, and `save_memory()` asks the model to merge any new facts about the user into `memory.md`.

**Agent loop ([agent.py](src/agent.py)).**
The loop calls the model and checks whether it asked for tools.
If it did, each tool call is dispatched through `TOOL_REGISTRY` and the result is appended to `messages`, and the loop runs again.
When the model answers without calling a tool, the turn is over.
There are two planned hooks in the loop: `compact()` before every model call, and `check_permissions()` before every tool call.

**Tools ([tools/](src/tools/)).**
Every tool is a `Tool(name, description, function, read_only)` in the registry, and `schemas.py` holds the JSON schema the model sees for each one.
The file tools go through `safe_path()`, so they cannot reach outside the working directory.

**Plan mode ([plan.py](src/plan.py)).**
Plan mode runs three phases: PLAN → REVIEW → EXECUTE.
- In PLAN, the model may only use read-only tools, and it hands in its steps by calling `submit_plan`.
- In REVIEW, the user runs the plan, rejects it, or types feedback, which sends it back to PLAN.
- In EXECUTE, the model has every tool plus `update_step`. It can call `request_replan` to go back to PLAN, at most 3 times.

Each phase is just `agent_loop` with a different tool set and a "stop tool" that ends the loop.

**Context management ([memory.py](src/memory.py)).**
When the history grows past `MAX_CONTEXT_TOKENS`, `compact()` keeps the last `KEEP_RECENT_TOKENS` of messages as they are and has the model summarize everything older.
The cut always lands on a user message, so a tool result is never separated from its tool call.

**Permissions ([permission.py](src/permission.py)).**
Every tool call has to pass three gates:
1. A deny list blocks some commands outright.
2. A rules table flags risky calls, such as destructive shell words or file writes outside the workspace.
3. Flagged calls go to the user for a y/n answer.

**Sandbox ([sandbox.py](src/sandbox.py)).**
The sandbox limits what an allowed command can do once it runs:
- the working directory is locked to the workspace,
- the environment is clean, so API keys stay out of the shell,
- there is a timeout plus CPU and file-size limits,
- output is truncated.

There are two backends: `LocalSandbox`, and `DockerSandbox` for stronger isolation.

## Status

| Component | File | Status |
|---|---|---|
| Session, system prompt | `main.py`, `prompts.py` | Done |
| Agent loop | `agent.py` | Done |
| Tool registry + 6 tools | `tools/` | Done |
| Skills (index + `load_skill`) | `skills.py`, `skills/` | Done |
| Plan mode | `plan.py` | Done |
| Long-term memory | `memory.py` | Done |
| Sliding window + compact | `memory.py` | Written, not called from `agent_loop` yet |
| Permission gates | `permission.py` | Written, not called from `agent_loop` yet |
| Sandbox | `sandbox.py` | Skeleton (TODOs only) |

## Project layout

```
Mini_agent/
├── src/
│   ├── main.py          # session: build context, route queries, save memory
│   ├── agent.py         # agent loop: model call → tools → repeat
│   ├── config.py        # API client, model id, paths
│   ├── prompts.py       # system prompt, plan / execute prompts
│   ├── plan.py          # plan mode: PLAN → REVIEW → EXECUTE
│   ├── skills.py        # discover skills, build the index, load_skill
│   ├── memory.py        # long-term memory + sliding window / compact
│   ├── permission.py    # 3 gates: deny list, rules table, ask user
│   ├── sandbox.py       # sandboxed command execution (skeleton)
│   └── tools/
│       ├── base.py      # Tool dataclass
│       ├── registry.py  # TOOL_REGISTRY
│       ├── schemas.py   # JSON schemas sent to the model
│       ├── shell.py     # bash
│       └── filesystem.py# read_file, write_file, edit_file, glob
├── skills/              # one folder per skill, each with a SKILL.md
├── memory.md            # long-term facts about the user
└── docs/architecture.svg
```

## Getting started

```bash
cp .env.example .env     # set DEEPSEEK_API_KEY and MODEL_ID
pip install -e .
mini-agent
```

Type a task to chat, `/plan <task>` for plan mode, and press Enter on an empty line to quit.

## Next steps

- Call `compact(messages)` at the top of each turn in `agent_loop`.
- Call `check_permissions(tool_name, arguments)` before `tool.execute()`, and send a denial back to the model as the tool result.
- Implement `sandbox.py`, then have `run_bash` return `SANDBOX.run(command).to_text()`.
