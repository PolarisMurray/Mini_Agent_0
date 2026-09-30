import os
import json
import glob as g
import subprocess

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv


# =========================================================
# Part 1, Configure the OpenAI client
# =========================================================

load_dotenv()  # Load environment variables from .env file

API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

if not API_KEY:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set in the environment variables."
    )

if not MODEL_ID:
    raise ValueError(
        "MODEL_ID is not set in the environment variables."
    )

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
)


# =========================================================
# Part 2, Working Directory
# =========================================================

WORKDIR = Path.cwd().resolve()


def safe_path(path):
    """
    Make sure the requested path stays inside WORKDIR.
    """

    target = (WORKDIR / path).resolve()

    if not target.is_relative_to(WORKDIR):
        raise ValueError(
            f"Path is outside the working directory: {path}"
        )

    return target


# =========================================================
# Part 3, System Prompt
# =========================================================

SYSTEM = """
You are a coding agent.

You have the following tools:

- bash: run shell commands
- read_file: read text files
- write_file: create or overwrite text files
- edit_file: replace text inside files
- glob: find files by pattern

Use tools when needed to inspect, run, or modify the project.

When the task is finished, respond normally without calling a tool.
"""


# =========================================================
# Part 4, Define the tools
# =========================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a bash command in the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run."
                    }
                },
                "required": ["command"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the file relative to "
                            "the working directory."
                        )
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Optional maximum number of lines to read."
                        )
                    }
                },
                "required": ["path"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a text file. "
                "Creates the file or overwrites it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the file relative to "
                            "the working directory."
                        )
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "The complete text content to write "
                            "into the file."
                        )
                    }
                },
                "required": ["path", "content"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Replace one exact piece of text "
                "in an existing file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the file relative to "
                            "the working directory."
                        )
                    },
                    "old_text": {
                        "type": "string",
                        "description": (
                            "The exact existing text to find."
                        )
                    },
                    "new_text": {
                        "type": "string",
                        "description": (
                            "The replacement text."
                        )
                    }
                },
                "required": [
                    "path",
                    "old_text",
                    "new_text"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": (
                "Find files and directories matching "
                "a glob pattern."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Glob pattern such as "
                            "'*.py' or '**/*.py'."
                        )
                    }
                },
                "required": ["pattern"]
            }
        }
    }
]


# =========================================================
# Part 5, Implement the tools
# =========================================================

def run_bash(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr

        output += f"\nEXIT CODE: {result.returncode}"

        return output

    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds."

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def run_read(path, limit=None):
    target = safe_path(path)

    lines = target.read_text(
        encoding="utf-8"
    ).splitlines()

    if limit is not None:
        lines = lines[:limit]

    return "\n".join(lines)


def run_write(path, content):
    target = safe_path(path)

    # Create parent folders if they do not exist.
    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target.write_text(
        content,
        encoding="utf-8"
    )

    return f"Wrote {len(content)} characters to {path}"


def run_edit(path, old_text, new_text):
    target = safe_path(path)

    text = target.read_text(
        encoding="utf-8"
    )

    if old_text not in text:
        return "Error: text not found"

    new_content = text.replace(
        old_text,
        new_text,
        1
    )

    target.write_text(
        new_content,
        encoding="utf-8"
    )

    return f"Edited {path}"


def run_glob(pattern):
    matches = sorted(
        set(
            g.glob(
                pattern,
                root_dir=WORKDIR,
                recursive=True
            )
        )
    )

    shown = matches[:200]

    if len(matches) > 200:
        shown.append(
            "... (more matches omitted; narrow the pattern)"
        )

    return "\n".join(shown)


# =========================================================
# Part 6, Agent Loop
# =========================================================

def agent_loop(messages):

    while True:

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM,
                },
                *messages,
            ],
            tools=TOOLS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # Add the model response to conversation history.
        messages.append(assistant_message)

        # If the model does not call a tool,
        # print the final answer and stop.
        if not assistant_message.tool_calls:
            print(assistant_message.content)
            return

        # Execute every requested tool call.
        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            arguments = json.loads(
                tool_call.function.arguments
            )

            print(f"\nTool: {tool_name}")
            print(f"Arguments: {arguments}")

            try:

                if tool_name == "bash":
                    output = run_bash(
                        arguments["command"]
                    )

                elif tool_name == "read_file":
                    output = run_read(
                        arguments["path"],
                        arguments.get("limit")
                    )

                elif tool_name == "write_file":
                    output = run_write(
                        arguments["path"],
                        arguments["content"]
                    )

                elif tool_name == "edit_file":
                    output = run_edit(
                        arguments["path"],
                        arguments["old_text"],
                        arguments["new_text"]
                    )

                elif tool_name == "glob":
                    output = run_glob(
                        arguments["pattern"]
                    )

                else:
                    output = (
                        f"Error: unknown tool '{tool_name}'"
                    )

            except Exception as e:
                output = (
                    f"Tool error: "
                    f"{type(e).__name__}: {e}"
                )

            print(f"Output:\n{output}")

            # Send the tool result back to the model.
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": output,
                }
            )


# =========================================================
# Part 7, User Input
# =========================================================

query = input(
    "What do you want the agent to do?\n> "
)

messages = [
    {
        "role": "user",
        "content": query,
    }
]

agent_loop(messages)