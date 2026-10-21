from mini_agent.agent import agent_loop
from mini_agent.prompts import PLAN_PROMPT, EXECUTE_PROMPT
from mini_agent.tools import Tool, TOOL_REGISTRY, TOOLS_SCHEMAS

# =========================================================
# Plan mode
#
#   PLAN    : read-only tools. The model explores, breaks the task
#             into steps, and calls submit_plan.
#   REVIEW  : the user approves, quits, or types feedback (-> PLAN).
#   EXECUTE : all tools. The model works through the steps, marks
#             each with update_step, and calls request_replan when
#             the plan turns out to be wrong (-> PLAN).
# =========================================================

MAX_REPLANS = 3

ICONS = {"todo": "☐", "done": "☑", "failed": "☒"}


# =========================================================
# Plan tool schemas (sent to the model)
# =========================================================

SUBMIT_PLAN = {
    "type": "function",
    "function": {
        "name": "submit_plan",
        "description": "Submit your step-by-step plan for the user to review.",
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "string",
                                "description": "What to do in this step."
                            },
                            "check": {
                                "type": "string",
                                "description": (
                                    "How to verify this step is done."
                                )
                            }
                        },
                        "required": ["task", "check"]
                    }
                }
            },
            "required": ["steps"]
        }
    }
}

UPDATE_STEP = {
    "type": "function",
    "function": {
        "name": "update_step",
        "description": "Mark a plan step as done or failed after checking it.",
        "parameters": {
            "type": "object",
            "properties": {
                "step": {
                    "type": "integer",
                    "description": "Step number, starting at 1."
                },
                "status": {
                    "type": "string",
                    "enum": ["done", "failed"]
                },
                "note": {
                    "type": "string",
                    "description": (
                        "What the check showed, or what went wrong."
                    )
                }
            },
            "required": ["step", "status", "note"]
        }
    }
}

REQUEST_REPLAN = {
    "type": "function",
    "function": {
        "name": "request_replan",
        "description": (
            "Stop executing and go back to planning, "
            "because the plan does not work."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "What went wrong and what you learned."
                }
            },
            "required": ["reason"]
        }
    }
}


# =========================================================
# Helpers
# =========================================================


def user(content):
    return {"role": "user", "content": content}


def schemas_for(names):
    """
    Pick the schemas of the given tools, so the model only sees those.
    """

    all_schemas = TOOLS_SCHEMAS + [SUBMIT_PLAN, UPDATE_STEP, REQUEST_REPLAN]

    return [s for s in all_schemas if s["function"]["name"] in names]


def render_plan(steps):
    lines = ["Plan:"]

    for i, step in enumerate(steps, 1):
        lines.append(f"  {ICONS[step['status']]} {i}. {step['task']}")
        lines.append(f"       check: {step['check']}")

        if step["note"]:
            lines.append(f"       note : {step['note']}")

    return "\n".join(lines)


def make_update_step(steps):
    """
    update_step needs to change THIS plan, so build it around `steps`.
    """

    def update_step(step, status, note):
        if not 1 <= step <= len(steps):
            return f"Error: there is no step {step}."

        steps[step - 1]["status"] = status
        steps[step - 1]["note"] = note

        print(render_plan(steps))

        return f"Step {step} marked {status}."

    return Tool(
        name="update_step",
        description="Mark a plan step as done or failed.",
        function=update_step,
    )


# =========================================================
# Phases
# =========================================================


def make_plan(messages, system):
    """
    PLAN: loop until the model calls submit_plan. Returns the steps.
    """

    read_only = {
        name: tool
        for name, tool in TOOL_REGISTRY.items()
        if tool.read_only
    }

    while True:
        kind, data = agent_loop(
            messages,
            system + PLAN_PROMPT,
            tools=read_only,
            schemas=schemas_for([*read_only, "submit_plan"]),
            stop_tools={"submit_plan"},
        )

        if kind == "submit_plan" and data.get("steps"):
            return [
                {
                    "task": s["task"],
                    "check": s["check"],
                    "status": "todo",
                    "note": "",
                }
                for s in data["steps"]
            ]

        # The model answered in text, usually a question for the user.
        reply = input(
            "\nreply(enter = let him give the plan\n> "
        ).strip()

        messages.append(
            user(reply or "Call submit_plan with your plan now.")
        )


def execute(messages, system, steps):
    """
    EXECUTE: run with all tools plus update_step / request_replan.
    """

    messages.append(
        user(
            "The user approved the plan. Execute it now.\n\n"
            + render_plan(steps)
        )
    )

    tools = {**TOOL_REGISTRY, "update_step": make_update_step(steps)}

    return agent_loop(
        messages,
        system + EXECUTE_PROMPT,
        tools=tools,
        schemas=schemas_for([*tools, "request_replan"]),
        stop_tools={"request_replan"},
    )


# =========================================================
# Plan mode: PLAN -> REVIEW -> EXECUTE, back to PLAN on feedback
# =========================================================


def run_plan_mode(task, messages, system):
    messages.append(user(task))

    replans = 0

    while True:
        # PLAN
        print("\n── 计划阶段（只读）──")
        steps = make_plan(messages, system)

        # REVIEW
        print("\n" + render_plan(steps))
        answer = input(
            "\n执行这个计划？[回车/y] 执行  [n] 放弃  或直接输入修改意见\n> "
        ).strip()

        if answer.lower() == "n":
            messages.append(user("The user rejected the plan."))
            print("已放弃。")
            return

        if answer.lower() not in ("", "y"):
            messages.append(
                user(f"Revise the plan. User feedback: {answer}")
            )
            continue

        # EXECUTE
        print("\n── 执行阶段 ──")
        kind, data = execute(messages, system, steps)

        if kind != "request_replan":
            return

        # REPLAN: feedback said the plan is wrong
        replans += 1
        print(f"\n⟳ 重新计划（第 {replans} 次）：{data['reason']}")

        if replans > MAX_REPLANS:
            print("重新计划次数太多，停下来交给你决定。")
            return

        messages.append(
            user(
                f"The plan did not work: {data['reason']}\n\n"
                + render_plan(steps)
                + "\n\nMake a new plan for the remaining work only. "
                "Do not repeat the approach that failed."
            )
        )
