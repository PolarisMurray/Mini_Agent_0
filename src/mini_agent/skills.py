from dataclasses import dataclass
from pathlib import Path

from mini_agent.config import SKILLS_DIR

# =========================================================
# Skills, progressive disclosure
#
#   L1  name + description  -> always in the system prompt
#   L2  SKILL.md body       -> loaded when the skill is triggered
#   L3  extra files         -> loaded only when L2 points to them
#
# Layout:  skills/<name>/SKILL.md
#          skills/<name>/reference/*.md
# =========================================================


@dataclass
class Skill:
    name: str
    description: str
    path: Path  # folder holding SKILL.md (L2) and extra files (L3)


def parse_frontmatter(text):
    """
    Split '---\\nkey: value\\n---\\nbody' into (meta, body).
    """

    if not text.startswith("---"):
        return {}, text

    _, header, body = text.split("---", 2)

    meta = {}
    for line in header.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()

    return meta, body.strip()


def discover_skills():
    """
    Scan every skills/*/SKILL.md, but keep only the L1 metadata.
    The body is NOT kept here; it is read again on demand.
    """

    skills = {}

    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        meta, _ = parse_frontmatter(
            skill_md.read_text(encoding="utf-8")
        )
        skills[meta["name"]] = Skill(
            name=meta["name"],
            description=meta["description"],
            path=skill_md.parent,
        )

    return skills


SKILLS = discover_skills()


def skills_index():
    """
    L1: one line per skill, so the model knows WHEN to use it.
    """

    return "\n".join(
        f"- {skill.name}: {skill.description}"
        for skill in SKILLS.values()
    )


def load_skill(name, file=None):
    """
    The `load_skill` tool.
    No file   -> L2, the SKILL.md body.
    With file -> L3, an extra file inside the skill folder.
    """

    skill = SKILLS.get(name)

    if skill is None:
        return (
            f"Error: unknown skill '{name}'. "
            f"Available: {', '.join(SKILLS)}"
        )

    # L2
    if file is None:
        _, body = parse_frontmatter(
            (skill.path / "SKILL.md").read_text(encoding="utf-8")
        )
        return body

    # L3, must stay inside this skill's folder
    target = (skill.path / file).resolve()

    if not target.is_relative_to(skill.path) or not target.is_file():
        return f"Error: file '{file}' not found in skill '{name}'"

    return target.read_text(encoding="utf-8")
