from __future__ import annotations

import json
from typing import Callable
from mini_agent.config import client, MODEL_ID, MEMORY_FILE
# =========================================================
# Memory
#
#   Read : at session start, memory.md goes into the context.
#   Write: at session end, the model distills new user facts
#          from the conversation and merges them into memory.md.
# =========================================================

DISTILL_PROMPT = """
You maintain a memory file of long-lasting facts about the user:
name, background, preferences, ongoing projects, and similar.

Merge the current memory with any NEW facts from the conversation.
- Keep only facts about the user that will still matter later.
- Update facts that changed; remove duplicates.
- Skip one-off task details.

Output only a short markdown bullet list.
If there are no facts at all, output exactly: NONE
"""

Message = {}
LLMFn = Callable[[str], str]

# -----------------------------
# estimations of tokens
# -----------------------------
def estimate_tokens(text: str) -> int:
    """
    Roughly estimate how many tokens a piece of text will use.

    Estimation rules:
      - ASCII characters (English letters, digits, punctuation):
        about 4 characters = 1 token
      - Non-ASCII characters (e.g. Chinese, Japanese, emoji):
        1 character = 1 token
      - Add 1 extra at the end
    """

    # Step 1: Count how many ASCII characters there are
    # Step 2: Work out how many non-ASCII characters there are
    # Step 3: Convert each group into tokens
    # Step 4: Add them together, plus 1 extra
    ascii_count = 0
    for ch in text:
        code = ord(ch)
        if code < 128:
            ascii_count = ascii_count + 1

    total_count = len(text)
    non_ascii_count = total_count - ascii_count

    
    ascii_tokens = ascii_count // 4
    non_ascii_tokens = non_ascii_count

    total_tokens = ascii_tokens + non_ascii_tokens + 1

    return total_tokens


# Try it out
print(estimate_tokens("Hello 世界"))   # Prints 4



def load_memory():
    if not MEMORY_FILE.exists():
        return ""

    return MEMORY_FILE.read_text(encoding="utf-8").strip()


def format_transcript(messages):
    """
    Keep only user / assistant text; tool calls are noise here.
    """

    lines = []

    for message in messages:
        # Assistant messages are SDK objects, the rest are dicts.
        if not isinstance(message, dict):
            message = message.model_dump()

        if message["role"] in ("user", "assistant") and message.get("content"):
            lines.append(f"{message['role']}: {message['content']}")

    return "\n".join(lines)


def save_memory(messages):
    transcript = format_transcript(messages)

    if not transcript:
        return

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {
                "role": "system",
                "content": DISTILL_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Current memory:\n{load_memory() or '(empty)'}\n\n"
                    f"Conversation:\n{transcript}"
                ),
            },
        ],
    )

    new_memory = response.choices[0].message.content.strip()

    if new_memory != "NONE":
        MEMORY_FILE.write_text(new_memory + "\n", encoding="utf-8")


# =========================================================
# Context window: sliding window + compact
#
#   Before each model call, if the history is too long:
#     1. Keep the most recent messages as they are (the window).
#     2. Summarize everything older into a short summary (compact).
#     3. history = [summary + first recent message, ...rest of recent]
# =========================================================

MAX_CONTEXT_TOKENS = 30000   # compact when the history grows past this
KEEP_RECENT_TOKENS = 10000   # how much recent history to keep verbatim

COMPACT_PROMPT = """
Summarize the earlier part of a coding-agent conversation so the agent can continue the task.
Keep: the user's goal, decisions made, files read or changed, important tool results,
and what is still left to do.
Drop: chit-chat and full file contents.
Output a concise markdown bullet list.
"""

SUMMARY_PREFIX = "[Summary of earlier conversation]\n"


def to_dict(message):
    # Assistant messages are SDK objects, the rest are dicts.
    if isinstance(message, dict):
        return message
    return message.model_dump(exclude_none=True)


def message_tokens(message) -> int:
    message = to_dict(message)
    text = str(message.get("content") or "")

    for call in message.get("tool_calls") or []:
        text += call["function"]["arguments"]

    return estimate_tokens(text)


def find_cut(messages) -> int:
    """
    Index where the kept window starts.
    Always a user message, so a tool result is never split from its tool call.
    """

    user_indexes = [
        i for i, m in enumerate(messages) if to_dict(m)["role"] == "user"
    ]

    for i in user_indexes:
        if sum(map(message_tokens, messages[i:])) <= KEEP_RECENT_TOKENS:
            return i

    # Even the current turn alone is too big: keep it whole anyway.
    return user_indexes[-1] if user_indexes else 0


def format_for_compact(messages):
    """
    Unlike format_transcript, keep tool calls and (cut) tool results,
    because the summary must remember what the agent already did.
    """

    lines = []

    for message in map(to_dict, messages):
        content = str(message.get("content") or "")

        if message["role"] == "tool":
            content = content[:500]

        for call in message.get("tool_calls") or []:
            name = call["function"]["name"]
            args = call["function"]["arguments"][:200]
            content += f"\n[called {name}({args})]"

        if content:
            lines.append(f"{message['role']}: {content}")

    return "\n".join(lines)


def compact(messages) -> None:
    if sum(map(message_tokens, messages)) <= MAX_CONTEXT_TOKENS:
        return

    cut = find_cut(messages)
    if cut == 0:
        return

    old, recent = messages[:cut], messages[cut:]

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": COMPACT_PROMPT},
            {"role": "user", "content": format_for_compact(old)},
        ],
    )
    summary = response.choices[0].message.content.strip()

    # Merge into the first kept user message instead of adding a new one,
    # since some models reject two user messages in a row.
    recent[0] = {
        "role": "user",
        "content": f"{SUMMARY_PREFIX}{summary}\n\n{recent[0]['content']}",
    }

    # In place: agent_loop holds a reference to this same list.
    messages[:] = recent
    print(f"\033[2m✻ compacted {len(old)} old messages into a summary\033[0m")
