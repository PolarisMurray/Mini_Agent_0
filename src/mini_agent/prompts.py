# =========================================================
# System Prompt
# =========================================================

SYSTEM = """
You are a coding agent.

You have the following tools:

- bash: run shell commands
- read_file: read text files
- write_file: create or overwrite text files
- edit_file: replace text inside files
- glob: find files by pattern
- load_skill: load the instructions of a skill

Use tools when needed to inspect, run, or modify the project.

When the task is finished, respond normally without calling a tool.
"""


# =========================================================
# Context = base prompt + skill index (L1) + memory
# =========================================================

def build_system_prompt(skills_index, memory):
    return f"""{SYSTEM}
# Skills

Before you answer, check whether a skill below matches the task.
If one does, call load_skill(name) FIRST and follow it.
A skill may point to extra files; load them with
load_skill(name, file) only when you really need them.

{skills_index}

# Memory (facts about the user from past sessions)

{memory or "(empty)"}
"""
