from mini_agent.agent import agent_loop
from mini_agent.memory import load_memory, save_memory
from mini_agent.plan import run_plan_mode
from mini_agent.prompts import build_system_prompt
from mini_agent.skills import skills_index

# =========================================================
# Session: read context -> chat -> write memory
# =========================================================


def main():
    # Read: skill index (L1) + memory go into the context once.
    system = build_system_prompt(skills_index(), load_memory())

    messages = []

    while True:
        try:
            query = input(
                "\nWhat do you want the agent to do? "
                "(/plan <task> for plan mode, empty to quit)\n> "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not query:
            break

        # The user chooses plan mode with /plan <task>.
        if query.startswith("/plan"):
            task = query.removeprefix("/plan").strip()

            if task:
                run_plan_mode(task, messages, system)
            else:
                print("Usage: /plan <task>")

            continue

        messages.append(
            {
                "role": "user",
                "content": query,
            }
        )

        agent_loop(messages, system)

    # Write: distill this session into memory.md.
    save_memory(messages)


if __name__ == "__main__":
    main()
