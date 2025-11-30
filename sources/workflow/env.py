import os
from pathlib import Path

from dotenv import load_dotenv

import logging_

LOGGER = logging_.get_logger(__name__)
_setup = False

API_KEY, PUT_NAME, MAX_ITER = None, None, None
GEN_MODEL, DEBUG_MODEL, EVAL_MODEL = "", "", ""


def _setup_env():
    global _setup, API_KEY, GEN_MODEL, DEBUG_MODEL, EVAL_MODEL, PUT_NAME, MAX_ITER

    if _setup:
        return

    # Check for .env file
    env_file = Path("./input/.env")
    if not env_file.exists():
        LOGGER.error(".env file not found at ./input/.env!\nLIFT requires .env file in this location!")
        exit(-1)

    load_dotenv(env_file, verbose=True)

    required_vars = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "LIFT_PUT": os.getenv("LIFT_PUT"),
        "LIFT_MAX_ITER": os.getenv("LIFT_MAX_ITER"),
    }

    for var_name, value in required_vars.items():
        if value is None:
            LOGGER.error(f"{var_name} not set in .env file!")
            exit(-1)

    API_KEY = required_vars["OPENAI_API_KEY"]
    PUT_NAME = required_vars["LIFT_PUT"]
    MAX_ITER = int(required_vars["LIFT_MAX_ITER"])

    # get models
    all_model = os.getenv("LIFT_MODEL")
    gen_model = os.getenv("LIFT_GEN_MODEL")
    debug_model = os.getenv("LIFT_DEBUG_MODEL")
    eval_model = os.getenv("LIFT_EVAL_MODEL")

    if not all_model:
        if not gen_model or not debug_model or not eval_model:
            LOGGER.error("Either set all agent models individually (LIFT_GEN_MODEL,LIFT_DEBUG_MODEL,LIFT_EVAL_MODEL) "
                         "or define fallback model using LIFT_MODEL in .env file!")
            exit(-1)

    GEN_MODEL = gen_model or all_model
    DEBUG_MODEL = debug_model or all_model
    EVAL_MODEL = eval_model or all_model

    _setup = True


_setup_env()

# Workflow paths
LIFT_PATH = Path("").resolve()
LIFT_ARCHIVE = (LIFT_PATH / ".archive").resolve()
ARCHIVE_CON = (LIFT_ARCHIVE / "conversations").resolve()
DATA_PATH = Path(LIFT_PATH / "input").resolve()
CONFIG_PATH = Path(LIFT_PATH / "config").resolve()

# Project Paths
PROJECT_PATH = Path(LIFT_PATH / "project").resolve()
PUT_PATH = (PROJECT_PATH / PUT_NAME).resolve()
TESTS_PATH = (PROJECT_PATH / "tests").resolve()
REPORTS_PATH = (PROJECT_PATH / "reports").resolve()


def log():
    LOGGER.info(
        "Setup environment:\n"
        f"    OPENAI_API_KEY: {API_KEY[:6]}… (hidden)\n"
        f"    MODEL:          Generator -> {GEN_MODEL}, Debugger -> {DEBUG_MODEL}, Evaluator -> {EVAL_MODEL}\n"
        f"    LIFT_PUT:       {PUT_NAME}\n"
        f"    LIFT_MAX_ITER:  {MAX_ITER}"
    )
