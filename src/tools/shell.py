import subprocess

from mini_agent.config import WORKDIR


def run_bash(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout

        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr

        output += f"\nEXIT CODE: {result.returncode}"

        return output

    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30 seconds."

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
