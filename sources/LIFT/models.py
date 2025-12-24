from enum import Enum
from logging import getLogger

LOGGER = getLogger(__name__)


class OpenAIModel(Enum):
    GPT_5 = "gpt-5"
    GPT_5_CODEX = "gpt-5-codex"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    GPT_5_PRO = "gpt-5-pro"

    GPT_5_1 = "gpt-5.1"
    GPT_5_1_CODEX = "gpt-5.1-codex"
    GPT_5_1_CODEX_MAX = "gpt-5.1-codex-max"
    GPT_5_1_CODEX_MINI = "gpt-5.1-codex-mini"

    GPT_5_2 = "gpt-5.2"
    GPT_5_2_PRO = "gpt-5.2-pro"

    O1 = "o1"
    O1_PRO = "o1-pro"

    O3 = "o3"
    O3_MINI = "o3-mini"
    O3_PRO = "o3-pro"

    O4_MINI = "o4-mini"


Model = OpenAIModel


def validate_model(model: str) -> Model:
    if model in {m.value for m in OpenAIModel}:
        return OpenAIModel(model)

    LOGGER.error(f"Invalid Model ({model}) set in .env file!")
    raise ValueError(f"Model {model} is not a valid model")
