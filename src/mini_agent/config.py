import os

from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# =========================================================
# Configure the OpenAI client
# =========================================================

load_dotenv()  # Load environment variables from .env file
API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL_ID = os.getenv("MODEL_ID")

if not API_KEY:
    raise ValueError(
        "DEEPSEEK_API_KEY is not set in the environment variables."
    )

if not MODEL_ID:
    raise ValueError(
        "MODEL_ID is not set in the environment variables."
    )

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
)


# =========================================================
# Working Directory
# =========================================================

WORKDIR = Path.cwd().resolve()


# =========================================================
# Project paths, skills/ and memory.md live next to src/
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = PROJECT_ROOT / "skills"
MEMORY_FILE = PROJECT_ROOT / "memory.md"
