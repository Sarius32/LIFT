import os
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

from dotenv import load_dotenv

from .models import validate_model, OpenAIModel, AnthropicModel, Model

LOGGER = getLogger(__name__)

SetupError = Exception


@dataclass
class LiftConfig:
    generator: Model
    debugger: Model
    evaluator: Model

    put_name: str
    max_iterations: int

    def __init__(self, env_file: Path):
        # load .env file is exists
        if not env_file.exists():
            LOGGER.error(f".env file not found at {env_file.absolute()}!")
            raise FileNotFoundError(".env file missing!")
        load_dotenv(env_file, verbose=True)

        required_vars = {
            "LIFT_PUT": os.getenv("LIFT_PUT"),
            "LIFT_MAX_ITER": os.getenv("LIFT_MAX_ITER"),
        }

        for var_name, value in required_vars.items():
            if value is None:
                LOGGER.error(f"{var_name} not set in .env file!")
                raise SetupError(f"{var_name} missing in .env file!")

        self.put_name = required_vars["LIFT_PUT"]
        self.max_iterations = int(required_vars["LIFT_MAX_ITER"])

        # get models
        all_model = os.getenv("LIFT_MODEL")
        gen_model = os.getenv("LIFT_GEN_MODEL")
        debug_model = os.getenv("LIFT_DEBUG_MODEL")
        eval_model = os.getenv("LIFT_EVAL_MODEL")

        if all_model and gen_model and debug_model and eval_model:
            LOGGER.error("Either set all agent models individually (LIFT_GEN_MODEL, LIFT_DEBUG_MODEL, "
                         "LIFT_EVAL_MODEL) or define fallback model using LIFT_MODEL in .env file - not all vars!")
            raise SetupError(f"Models not properly set in .env file!")

        if not all_model:
            if not gen_model or not debug_model or not eval_model:
                LOGGER.error("Either set all agent models individually (LIFT_GEN_MODEL, LIFT_DEBUG_MODEL, "
                             "LIFT_EVAL_MODEL) or define fallback model using LIFT_MODEL in .env file!")
                raise SetupError(f"Models not properly set in .env file!")

        self.generator = validate_model(gen_model or all_model)
        self.debugger = validate_model(debug_model or all_model)
        self.evaluator = validate_model(eval_model or all_model)

        openai_key = os.getenv("OPENAI_API_KEY", None)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", None)

        if any([isinstance(m, OpenAIModel) for m in [self.generator, self.debugger, self.evaluator]]):
            if openai_key is None:
                LOGGER.error("Tried to use OpenAI model without setting OPENAI_API_KEY in .env file!")
                raise SetupError(f"OpenAI_API_KEY not set in .env file!")

        if any([isinstance(m, AnthropicModel) for m in [self.generator, self.debugger, self.evaluator]]):
            if anthropic_key is None:
                LOGGER.error("Tried to use Anthropic model without setting ANTHROPIC_API_KEY in .env file!")
                raise SetupError(f"ANTHROPIC_API_KEY not set in .env file!")

        LOGGER.info(
            "Setup environment:\n"
            f"    OPENAI_API_KEY:    {(openai_key[:6] + '… (hidden)') if openai_key else "(not set)"}\n"
            f"    ANTHROPIC_API_KEY: {(anthropic_key[:6] + '… (hidden)') if anthropic_key else "(not set)"}\n"
            f"    MODEL:             Generator -> {self.generator}, Debugger -> {self.debugger}, Evaluator -> {self.evaluator}\n"
            f"    LIFT_PUT:          {self.put_name}\n"
            f"    LIFT_MAX_ITER:     {self.max_iterations}"
        )
