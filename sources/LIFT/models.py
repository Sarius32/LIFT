from enum import Enum
from logging import getLogger

LOGGER = getLogger(__name__)


class OpenAIModel(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"

    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"

    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"

    GPT_5 = "gpt-5"
    GPT_5_PRO = "gpt-5-pro"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    GPT_5_CODEX = "gpt-5-codex"

    GPT_5_1 = "gpt-5.1"
    GPT_5_1_CODEX = "gpt-5.1-codex"
    GPT_5_1_CODEX_MAX = "gpt-5.1-codex-max"
    GPT_5_1_CODEX_MINI = "gpt-5.1-codex-mini"

    GPT_5_2 = "gpt-5.2"
    GPT_5_2_PRO = "gpt-5.2-pro"

    O1 = "o1"
    O1_PRO = "o1-pro"
    O1_MINI = "o1-mini"

    O3 = "o3"
    O3_PRO = "o3-pro"
    O3_MINI = "o3-mini"

    O4_MINI = "o4-mini"


class AnthropicModel(Enum):
    SONNET_4_5 = "claude-sonnet-4-5"

    OPUS_3_LATEST = "claude-3-opus-latest"
    OPUS_3_5_LATEST = "claude-3-5-sonnet-latest"
    OPUS_3_7_LATEST = "claude-3-7-sonnet-latest"

    OPUS_4_1 = "claude-opus-4-1"
    OPUS_4_5 = "claude-opus-4-5"

    HAIKU_3_5_LATEST = "claude-3-5-haiku-latest"
    HAIKU_4_5 = "claude-haiku-4-5"


Model = OpenAIModel | AnthropicModel


def validate_model(model: str) -> Model:
    if model in {m.value for m in OpenAIModel}:
        return OpenAIModel(model)

    if model in {m.value for m in AnthropicModel}:
        return AnthropicModel(model)

    LOGGER.error(f"Invalid Model ({model}) set in .env file!")
    raise ValueError(f"Model {model} is not a valid model")


def litellm_model(model: Model) -> str:
    if isinstance(model, OpenAIModel):
        return "openai/" + model.value

    if isinstance(model, AnthropicModel):
        return "anthropic/" + model.value

    return ""
