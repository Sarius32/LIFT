import os
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

from dotenv import load_dotenv

LOGGER = getLogger(__name__)

SetupError = Exception


@dataclass
class LiftConfig:
    api_key: str

    generator: str
    debugger: str
    evaluator: str

    put_name: str
    max_iterations: int

    def __init__(self, env_file: Path):
        # load .env file is exists
        if not env_file.exists():
            LOGGER.error(f".env file not found at {env_file.absolute()}!")
            raise FileNotFoundError(".env file missing!")
        load_dotenv(env_file, verbose=True)

        required_vars = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "LIFT_PUT": os.getenv("LIFT_PUT"),
            "LIFT_MAX_ITER": os.getenv("LIFT_MAX_ITER"),
        }

        for var_name, value in required_vars.items():
            if value is None:
                LOGGER.error(f"{var_name} not set in .env file!")
                raise SetupError(f"{var_name} missing in .env file!")

        self.api_key = required_vars["OPENAI_API_KEY"]
        self.put_name = required_vars["LIFT_PUT"]
        self.max_iterations = int(required_vars["LIFT_MAX_ITER"])

        # get models
        all_model = os.getenv("LIFT_MODEL")
        gen_model = os.getenv("LIFT_GEN_MODEL")
        debug_model = os.getenv("LIFT_DEBUG_MODEL")
        eval_model = os.getenv("LIFT_EVAL_MODEL")

        if not all_model:
            if not gen_model or not debug_model or not eval_model:
                LOGGER.error(
                    "Either set all agent models individually (LIFT_GEN_MODEL, LIFT_DEBUG_MODEL, LIFT_EVAL_MODEL) "
                    "or define fallback model using LIFT_MODEL in .env file!")
                raise SetupError(f"Models not properly set in .env file!")

        self.generator = gen_model or all_model
        self.debugger = debug_model or all_model
        self.evaluator = eval_model or all_model

        LOGGER.info(
            "Setup environment:\n"
            f"    OPENAI_API_KEY: {self.api_key[:6]}… (hidden)\n"
            f"    MODEL:          Generator -> {self.generator}, Debugger -> {self.debugger}, Evaluator -> {self.evaluator}\n"
            f"    LIFT_PUT:       {self.put_name}\n"
            f"    LIFT_MAX_ITER:  {self.max_iterations}"
        )
