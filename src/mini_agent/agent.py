import json

from mini_agent.config import client, MODEL_ID
from mini_agent.tools import TOOL_REGISTRY, TOOLS_SCHEMAS

# =========================================================
# Agent Loop
# =========================================================


def agent_loop(messages, system):

    while True:

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                *messages,
            ],
            tools=TOOLS_SCHEMAS,
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
                tool = TOOL_REGISTRY[tool_name]
                output = tool.execute(arguments)

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
