import os

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
    api_base = "https://api.deepseek.ai/v1",)

# Part 2, System Prompt

SYSTEM_PROMPT = """
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