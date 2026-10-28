import os
import resource
import subprocess
from dataclasses import dataclass
from pathlib import Path

from mini_agent.config import WORKDIR

# =========================================================
# Sandbox
#
#   permission.py decides WHETHER a command may run.
#   sandbox.py limits WHAT it can do once it runs:
#     - cwd locked to the workspace
#     - clean env, so API keys from .env never reach the shell
#     - timeout + CPU / file-size limits
#     - output cut short so it cannot flood the context
# =========================================================

TIMEOUT = 30
MAX_OUTPUT_CHARS = 10000
MAX_FILE_BYTES = 50 * 1024 * 1024
SAFE_ENV_KEYS = ("PATH", "HOME", "LANG", "TERM")


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False

    def to_text(self) -> str:
        # Turn the result into the text sent back to the model,
        # in the same format run_bash uses today.
        # TODO: if timed_out, return a timeout error message
        # TODO: start from stdout; if there is stderr, append "\nSTDERR:\n" + stderr
        # TODO: if longer than MAX_OUTPUT_CHARS, cut it and add a "(truncated)" note
        # TODO: append f"\nEXIT CODE: {exit_code}" and return
        pass


class Sandbox:
    # Base class: every sandbox takes a command and returns a SandboxResult.
    def run(self, command: str) -> SandboxResult:
        raise NotImplementedError


def limit_resources():
    # Runs inside the child process, right before the command starts
    # (passed to subprocess.run as preexec_fn).
    # TODO: limit CPU seconds with resource.RLIMIT_CPU (use TIMEOUT)
    # TODO: limit the size of files it can write with resource.RLIMIT_FSIZE (use MAX_FILE_BYTES)
    pass


class LocalSandbox(Sandbox):
    # Runs the command on this machine, with limits.
    def __init__(self, workdir: Path = WORKDIR):
        self.workdir = workdir

    def run(self, command: str) -> SandboxResult:
        # TODO: build a clean env: only the keys in SAFE_ENV_KEYS from os.environ
        # TODO: subprocess.run(command, shell=True, cwd=self.workdir, env=env,
        #       capture_output=True, text=True, timeout=TIMEOUT,
        #       preexec_fn=limit_resources)
        # TODO: on subprocess.TimeoutExpired, return SandboxResult with timed_out=True
        # TODO: otherwise return SandboxResult(stdout, stderr, returncode)
        pass


class DockerSandbox(Sandbox):
    # Stronger isolation: a throwaway container with no network,
    # where only the workspace is mounted.
    def __init__(self, image: str = "python:3.12-slim", workdir: Path = WORKDIR):
        self.image = image
        self.workdir = workdir

    def run(self, command: str) -> SandboxResult:
        # TODO: build the docker command:
        #       docker run --rm --network none --memory 512m --cpus 1
        #       -v {workdir}:/workspace -w /workspace {image} sh -c {command}
        # TODO: run it with subprocess.run (as a list, no shell=True), with a timeout
        # TODO: on timeout, the container keeps running: give it a --name and `docker kill` it
        # TODO: return SandboxResult(stdout, stderr, returncode)
        pass


# The sandbox the bash tool uses; swap in DockerSandbox() later.
SANDBOX: Sandbox = LocalSandbox()
