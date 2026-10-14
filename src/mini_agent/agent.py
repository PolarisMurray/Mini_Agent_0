import json

from mini_agent.config import client, MODEL_ID
from mini_agent.tools import TOOL_REGISTRY, TOOLS_SCHEMAS
from openai.types.chat import ChatCompletionMessage

MAX_TURNS = 50  # safety limit, so a confused model cannot loop forever

# =========================================================
# Agent Loop
# =========================================================


def preview(text, width=100):
    """
    First line of a tool output, cut short, for the terminal.
    """

    lines = str(text).strip().splitlines() or ["(no output)"]
    first = lines[0][:width]

    if len(lines) > 1:
        first += f"  (+{len(lines) - 1} lines)"

    return first


def agent_loop(
    messages,
    system,
    tools=TOOL_REGISTRY,
    schemas=TOOLS_SCHEMAS,
    stop_tools=(),
):
    """
    Call the model again and again until it answers without a tool.

    tools / schemas : which tools the model may use (default: all).
    stop_tools      : names of tools that end the loop when called,
                      e.g. submit_plan. Their arguments are handed back.

    Returns ("answer", text), or (tool_name, arguments) for a stop tool.
    """

    for _ in range(MAX_TURNS):

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                *messages,
            ],
            tools=schemas,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # Add the model response to conversation history.
        messages.append(assistant_message)

        # Reasoning models put their hidden thinking here (if any).
        reasoning = getattr(assistant_message, "reasoning_content", None)
        if reasoning:
            print(f"\033[2m✻ {reasoning.strip()}\033[0m")

        # The text next to tool calls is the model's visible reasoning,
        # e.g. "Let me look at the registry first."
        if assistant_message.content:
            print(f"\n⏺ {assistant_message.content.strip()}")

        # No tool call: the model is done.
        if not assistant_message.tool_calls:
            return "answer", assistant_message.content

        stop = None

        # Execute every requested tool call.
        for tool_call in assistant_message.tool_calls:

            tool_name = tool_call.function.name

            try:
                arguments = json.loads(
                    tool_call.function.arguments
                )

                if tool_name in stop_tools:
                    # Do not run anything; hand the arguments back.
                    stop = (tool_name, arguments)
                    output = "OK"

                elif tool_name not in tools:
                    output = (
                        f"Tool error: {tool_name} is not "
                        f"available right now."
                    )
                    print(f"  ⎿ {tool_name} ✗ blocked in this mode")

                else:
                    print(f"  ⎿ {tool_name} {arguments}")
                    output = str(tools[tool_name].execute(arguments))
                    print(f"    {preview(output)}")

            except Exception as e:
                output = (
                    f"Tool error: "
                    f"{type(e).__name__}: {e}"
                )
                print(f"    {output}")

            # Send the tool result back to the model.
            # Every tool call needs an answer, even after a stop tool.
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": output,
                }
            )

        if stop:
            return stop

    return "max_turns", None
