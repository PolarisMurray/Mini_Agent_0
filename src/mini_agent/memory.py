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
