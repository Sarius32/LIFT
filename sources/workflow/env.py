import os
from pathlib import Path

from dotenv import load_dotenv

import logging_

LOGGER = logging_.get_logger(__name__)
_setup = False

API_KEY, MODEL, PUT_NAME, MAX_ITER = None, None, None, None


def _setup_env():
    global _setup, API_KEY, MODEL, PUT_NAME, MAX_ITER

    if _setup:
        return

    # Check for .env file
    env_file = Path("./input/.env")
    if not env_file.exists():
        LOGGER.error(".env file not found at ./input/.env!\nLIFT requires .env file in this location!")
        exit(-1)

    load_dotenv(Path("./input/.env"), verbose=True)

    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LIFT_MODEL": os.getenv("LIFT_MODEL"),
        "LIFT_PUT": os.getenv("LIFT_PUT"),
        "LIFT_MAX_ITER": os.getenv("LIFT_MAX_ITER"),
    }

    for var_name, value in required_vars.items():
        if value is None:
            LOGGER.error(f"{var_name} not set in .env file!")
            exit(-1)

    API_KEY = required_vars["OPENAI_API_KEY"]
    MODEL = required_vars["LIFT_MODEL"]
    PUT_NAME = required_vars["LIFT_PUT"]
    MAX_ITER = int(required_vars["LIFT_MAX_ITER"])

    _setup = True


_setup_env()

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
