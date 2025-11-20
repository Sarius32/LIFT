import os
from pathlib import Path

import logging_

LOGGER = logging_.get_logger(__name__)

# Project Settings
if os.getenv("OPENAI_API_KEY", -1) == -1:
    LOGGER.error("OPENAI_API_KEY not set in .env file!")
    exit(-1)
if os.getenv("LIFT_MODEL", -1) == -1:
    LOGGER.error("LIFT_MODEL not set in .env file!")
    exit(-1)
if os.getenv("LIFT_PUT", -1) == -1:
    LOGGER.error("LIFT_PUT not set in .env file!")
    exit(-1)
if os.getenv("LIFT_MAX_ITER", -1) == -1:
    LOGGER.error("LIFT_MAX_ITER not set in .env file!")
    exit(-1)

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("LIFT_MODEL")
PUT_NAME = os.getenv("LIFT_PUT")
MAX_ITER = int(os.getenv("LIFT_MAX_ITER"))

# Workflow paths
LIFT_PATH = Path("").resolve()
LIFT_ARCHIVE = (LIFT_PATH / ".archive").resolve()
ARCHIVE_CON = (LIFT_ARCHIVE / "conversations").resolve()
DATA_PATH = Path(LIFT_PATH / "input").resolve()

# Project Paths
PROJECT_PATH = Path(LIFT_PATH / "project").resolve()
PUT_PATH = (PROJECT_PATH / PUT_NAME).resolve()
TESTS_PATH = (PROJECT_PATH / "tests").resolve()
REPORTS_PATH = (PROJECT_PATH / "reports").resolve()


def log():
    LOGGER.debug(
        "Setup environment:\n"
        f"  OPENAI_API_KEY: {API_KEY[:6]}… (hidden)\n"
        f"  LIFT_MODEL:     {MODEL}\n"
        f"  LIFT_PUT:       {PUT_NAME}\n"
        f"  LIFT_MAX_ITER:  {MAX_ITER}"
    )
