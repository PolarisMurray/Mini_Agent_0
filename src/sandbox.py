import os
import resource
import subprocess
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from mini_agent.config import WORKDIR

# =========================================================
# Sandbox
#
#   permission.py decides WHETHER a command may run.
#   sandbox.py limits WHAT it can do once it runs:
#     - SandboxPolicy: which files it may write, whether it may use the network
#       (enforced by the OS through macOS sandbox-exec, not by string matching)
#     - cwd locked to the workspace
#     - clean env, so API keys from .env never reach the shell
#     - timeout + CPU / file-size limits
#     - output cut short so it cannot flood the context
# =========================================================

TIMEOUT = 30
MAX_OUTPUT_CHARS = 10000
MAX_FILE_BYTES = 50 * 1024 * 1024
SAFE_ENV_KEYS = ("PATH", "HOME", "LANG", "TERM")

SEATBELT = "/usr/bin/sandbox-exec"


# ---------------------------------------------------------
# Policy: what a command is allowed to do
# ---------------------------------------------------------

class SandboxMode(Enum):
    READ_ONLY = "read-only"              # read anything, write nothing
    WORKSPACE_WRITE = "workspace-write"  # write only inside WORKDIR and /tmp
    FULL_ACCESS = "full-access"          # no sandbox at all


@dataclass
class SandboxPolicy:
    mode: SandboxMode = SandboxMode.WORKSPACE_WRITE
    network: bool = False


def build_seatbelt_profile(policy: SandboxPolicy) -> str:
    # Seatbelt rules: the LAST matching rule wins, so order matters.
    # Paths come in as -D parameters, never pasted into the text,
    # so a path with quotes in it cannot break the profile.
    rules = [
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
        '(allow file-write* (literal "/dev/null"))',
    ]

    if policy.mode == SandboxMode.WORKSPACE_WRITE:
        rules += [
            '(allow file-write* (subpath (param "WORKDIR")) (subpath "/private/tmp"))',
            # Writing .git/hooks would let code run outside the sandbox later.
            '(deny file-write* (subpath (param "GIT_DIR")))',
        ]

    if not policy.network:
        rules.append("(deny network*)")

    return "\n".join(rules)


# ---------------------------------------------------------
# Result
# ---------------------------------------------------------

@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False

    def to_text(self) -> str:
        if self.timed_out:
            return f"Error: command timed out after {TIMEOUT}s"

        output = self.stdout
        if self.stderr:
            output += "\nSTDERR:\n" + self.stderr

        if len(output) > MAX_OUTPUT_CHARS:
            extra = len(output) - MAX_OUTPUT_CHARS
            output = output[:MAX_OUTPUT_CHARS] + f"\n... (truncated, {extra} more chars)"

        output += f"\nEXIT CODE: {self.exit_code}"
        return output


class Sandbox:
    def run(self, command: str) -> SandboxResult:
        raise NotImplementedError


def limit_resources():
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT, TIMEOUT))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))


# ---------------------------------------------------------
# Backends
# ---------------------------------------------------------

class LocalSandbox(Sandbox):
    def __init__(self, policy: SandboxPolicy = SandboxPolicy(), workdir: Path = WORKDIR):
        self.policy = policy
        self.workdir = Path(workdir).resolve()

    def build_argv(self, command: str) -> list[str]:
        argv = ["/bin/sh", "-c", command]

        if self.policy.mode == SandboxMode.FULL_ACCESS:
            return argv

        if not Path(SEATBELT).exists():
            raise RuntimeError(
                f"{SEATBELT} not found (macOS only). "
                "Use DockerSandbox or SandboxMode.FULL_ACCESS."
            )

        # Same idea as Codex: do not change the command, wrap it.
        #   sh -c "ls"  ->  sandbox-exec -p <profile> -D... -- sh -c "ls"
        return [
            SEATBELT,
            "-p", build_seatbelt_profile(self.policy),
            f"-DWORKDIR={self.workdir}",
            f"-DGIT_DIR={self.workdir / '.git'}",
            "--",
            *argv,
        ]

    def run(self, command: str) -> SandboxResult:
        env = {key: os.environ[key] for key in SAFE_ENV_KEYS if key in os.environ}
        try:
            proc = subprocess.run(
                self.build_argv(command),
                cwd=self.workdir,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
                preexec_fn=limit_resources,
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(stdout="", stderr="", exit_code=-1, timed_out=True)
        return SandboxResult(proc.stdout, proc.stderr, proc.returncode)


class DockerSandbox(Sandbox):
    def __init__(
        self,
        policy: SandboxPolicy = SandboxPolicy(),
        image: str = "python:3.12-slim",
        workdir: Path = WORKDIR,
    ):
        self.policy = policy
        self.image = image
        self.workdir = Path(workdir).resolve()

    def run(self, command: str) -> SandboxResult:
        name = f"mini-agent-{uuid.uuid4().hex[:12]}"
        mount = f"{self.workdir}:/workspace"
        if self.policy.mode == SandboxMode.READ_ONLY:
            mount += ":ro"

        docker_cmd = [
            "docker", "run", "--rm",
            "--name", name,
            "--network", "bridge" if self.policy.network else "none",
            "--memory", "512m",
            "--cpus", "1",
            "-v", mount,
            "-w", "/workspace",
            self.image,
            "sh", "-c", command,
        ]
        try:
            proc = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            return SandboxResult(stdout="", stderr="", exit_code=-1, timed_out=True)
        return SandboxResult(proc.stdout, proc.stderr, proc.returncode)


SANDBOX: Sandbox = LocalSandbox()
