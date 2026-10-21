import glob as g

from mini_agent.config import WORKDIR


def safe_path(path):
    """
    Make sure the requested path stays inside WORKDIR.
    """

    target = (WORKDIR / path).resolve()

    if not target.is_relative_to(WORKDIR):
        raise ValueError(
            f"Path is outside the working directory: {path}"
        )

    return target


def run_read(path, limit=None):
    target = safe_path(path)

    lines = target.read_text(
        encoding="utf-8"
    ).splitlines()

    if limit is not None:
        lines = lines[:limit]

    return "\n".join(lines)


def run_write(path, content):
    target = safe_path(path)

    # Create parent folders if they do not exist.
    target.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    target.write_text(
        content,
        encoding="utf-8"
    )

    return f"Wrote {len(content)} characters to {path}"


def run_edit(path, old_text, new_text):
    target = safe_path(path)

    text = target.read_text(
        encoding="utf-8"
    )

    if old_text not in text:
        return "Error: text not found"

    new_content = text.replace(
        old_text,
        new_text,
        1
    )

    target.write_text(
        new_content,
        encoding="utf-8"
    )

    return f"Edited {path}"


def run_glob(pattern):
    matches = sorted(
        set(
            g.glob(
                pattern,
                root_dir=WORKDIR,
                recursive=True
            )
        )
    )

    shown = matches[:200]

    if len(matches) > 200:
        shown.append(
            "... (more matches omitted; narrow the pattern)"
        )

    return "\n".join(shown)
