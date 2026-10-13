from mini_agent.skills import load_skill
from mini_agent.tools.base import Tool
from mini_agent.tools.shell import run_bash
from mini_agent.tools.filesystem import (
    run_read,
    run_write,
    run_edit,
    run_glob,
)

# =========================================================
# Tool registry
# =========================================================

TOOL_REGISTRY: dict[str, Tool] = {}

TOOL_REGISTRY["bash"] = Tool(
    name="bash",
    description="Run a bash command.",
    function=run_bash,
)

TOOL_REGISTRY["read_file"] = Tool(
    name="read_file",
    description="Read the contents of a text file.",
    function=run_read,
)

TOOL_REGISTRY["write_file"] = Tool(
    name="write_file",
    description="Write content to a text file.",
    function=run_write,
)

TOOL_REGISTRY["edit_file"] = Tool(
    name="edit_file",
    description="Replace text in a file.",
    function=run_edit,
)

TOOL_REGISTRY["glob"] = Tool(
    name="glob",
    description="Find files matching a glob pattern.",
    function=run_glob,
)

TOOL_REGISTRY["load_skill"] = Tool(
    name="load_skill",
    description="Load a skill's SKILL.md or one of its extra files.",
    function=load_skill,
)
