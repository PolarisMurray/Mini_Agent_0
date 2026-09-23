import os
import subprocess

from openai import OpenAI
from dotenv import load_dotenv

# Part 1, Configure the OpenAI client
load_dotenv()  # Load environment variables from .env file
API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

if not API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is not set in the environment variables.")

if not MODEL_ID:
    raise ValueError("MODEL_ID is not set in the environment variables.")

client = OpenAI(
    api_key = API_KEY,
    base_url = "https://api.deepseek.com",)

# Part 2, System Prompt

SYSTEM = """
You are a coding agent.

You may use the bash tool when you need to inspect files,
run commands, or modify files.

When the task is finished, respond normally without calling a tool.
"""

# Part 3, Define the tools
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run bash commands in the current working directory.",
            "parameters": {
              "type": "object",
              "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run."
                }
            },
            "required": ["command"],
        },
    },
    }
]

def run_bash(command):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = result.stdout

    if result.stderr:
        output += "\nSTDERR:\n" + result.stderr

    return output


def agent_loop(messages):
    while True:

        response = client.chat.completions.create(
            model = MODEL_ID,
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM,
                },
                *messages,
            ],
            tools = TOOLS,
            tool_choice = "auto",
        )

        assistant_message = response.choices[0].message

        messages.append(assistant_message)

        # If the model does not call a tool,
        # print the final answer and stop.
        if not assistant_message.tool_calls:
            print(assistant_message.content)
            return

        # Execute every requested tool call.
        for tool_call in assistant_message.tool_calls:

            if tool_call.function.name == "bash":

                command = tool_call.function.arguments

                import json
                arguments = json.loads(command)

                bash_command = arguments["command"]

                print(f"\nRunning: {bash_command}")

                output = run_bash(bash_command)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": output,
                    }
                )


query = input("What do you want the agent to do?\n> ")

messages = [
    {
        "role": "user",
        "content": query,
    }
]

agent_loop(messages)