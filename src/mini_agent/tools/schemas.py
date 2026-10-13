# =========================================================
# Tool schemas (sent to the model)
# =========================================================

TOOLS_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a bash command in the current working directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run."
                    }
                },
                "required": ["command"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the file relative to "
                            "the working directory."
                        )
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Optional maximum number of lines to read."
                        )
                    }
                },
                "required": ["path"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a text file. "
                "Creates the file or overwrites it."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the file relative to "
                            "the working directory."
                        )
                    },
                    "content": {
                        "type": "string",
                        "description": (
                            "The complete text content to write "
                            "into the file."
                        )
                    }
                },
                "required": ["path", "content"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": (
                "Replace one exact piece of text "
                "in an existing file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Path to the file relative to "
                            "the working directory."
                        )
                    },
                    "old_text": {
                        "type": "string",
                        "description": (
                            "The exact existing text to find."
                        )
                    },
                    "new_text": {
                        "type": "string",
                        "description": (
                            "The replacement text."
                        )
                    }
                },
                "required": [
                    "path",
                    "old_text",
                    "new_text"
                ]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": (
                "Find files and directories matching "
                "a glob pattern."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": (
                            "Glob pattern such as "
                            "'*.py' or '**/*.py'."
                        )
                    }
                },
                "required": ["pattern"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": (
                "Load a skill's instructions (SKILL.md). "
                "Pass `file` to load an extra file the skill points to."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill name from the skill list."
                    },
                    "file": {
                        "type": "string",
                        "description": (
                            "Optional extra file inside the skill, "
                            "e.g. 'reference/advanced.md'."
                        )
                    }
                },
                "required": ["name"]
            }
        }
    }
]
