import os
import resource
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from mini_agent.config import WORKDIR

# (顶部注释和常量保持不变)
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


class LocalSandbox(Sandbox):
    def __init__(self, workdir: Path = WORKDIR):
        self.workdir = workdir

    def run(self, command: str) -> SandboxResult:
        env = {key: os.environ[key] for key in SAFE_ENV_KEYS if key in os.environ}
        try:
            proc = subprocess.run(
                command,
                shell=True,
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
    def __init__(self, image: str = "python:3.12-slim", workdir: Path = WORKDIR):
        self.image = image
        self.workdir = workdir

    def run(self, command: str) -> SandboxResult:
        name = f"mini-agent-{uuid.uuid4().hex[:12]}"
        docker_cmd = [
            "docker", "run", "--rm",
            "--name", name,
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1",
            "-v", f"{Path(self.workdir).resolve()}:/workspace",
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