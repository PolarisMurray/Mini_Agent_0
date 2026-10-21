import json
import textwrap
from pathlib import Path
from typing import Literal


WORKDIR = Path.cwd().resolve()

## 3 Gates: Black list, Rules Table, Ask_User
# Gate1
DENY_LIST = ["rm", "shutdown", "sudo"]
def check_deny_list(command: str) -> str | None:
    for word in DENY_LIST:
        if word in command.split():
            return f"Destructive command {word} detected from the deny list, no execution"
    return None

# Gate 2, checking rule tables
def is_outside_workspace(path: str) -> bool:
    # WORKDIR = /home/user/project
    # path = ../secret.txt
    # full_path = /home/user/project/../secret.txt
    full_path = WORKDIR / path
    resolved_path = full_path.resolve()

    return not resolved_path.is_relative_to(WORKDIR)


def contains_destructive_words(command: str) -> bool | None:
    ## rm lockfile; del all your disk
    for sep in SEPERATORS:
        command = command.replace(sep, "\n")
    for segement in command.split("\n"):
        word = segement.split()
        if word and word[0].lower() in DESTRUCTIVE_WORDS:
            return True
        
    return False

PSEMISSION_RULES_TABLE = [
    {
        "tool": "bash",
        "check": lambda args: contains_destructive_words(args.get("command", "")),
        "message": "Destructive command detect",
    },

    {
        "tool": "write_file",
        "check": lambda args: is_outside_workspace(args.get("path", "")),
        "message": "Confirm working in other directory/Workplace",
    },

    {
        "tool": "edit_file",
        "check": lambda args: is_outside_workspace(args.get("path", "")),
        "message": "Confirm working in other directory/Workplace",
    },
]

SEPERATORS = ["\n", ";", "/", "&", "(", ")"]
DESTRUCTIVE_WORDS = {"rm", "del"}


def check_rules(command: str, args: dict) -> str | None:
    for rule in PSEMISSION_RULES_TABLE:
        if rule["tool"] == command and rule["check"](args):
            return rule["message"]
    return None


# Gate 3
def ask_user(command: str, reason: str) -> str | None:
    answer = input(f"[Permission] {command}: {reason}. Allow? (y/n) ").strip().lower()
    if answer == "y":
        return None
    return f"User denied {command}: {reason}"


def check_permissions(command: str, args: dict) -> str | None:
    if command == "bash":
        denied = check_deny_list(args.get("command", ""))
        if denied:
            return denied

    reason = check_rules(command, args)
    if reason:
        return ask_user(command, reason)
    return None