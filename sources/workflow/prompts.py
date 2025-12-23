from dataclasses import dataclass
from logging import getLogger

from env import DATA_PATH, PUT_NAME

LOGGER = getLogger(__name__)


@dataclass
class GeneratorPrompts:
    system: str
    init: str
    error: str
    refine: str


@dataclass
class DebuggerPrompts:
    system: str
    instr: str


EvaluatorPrompts = DebuggerPrompts
Prompts = GeneratorPrompts | DebuggerPrompts | EvaluatorPrompts


def get_sys_prompt(name):
    return (DATA_PATH / (name + ".md")).read_text().strip()


LOGGER.info(f"Loading Prompts from {DATA_PATH}")

GEN_NAME = "GENERATOR"
GEN_SYS_PROMPT = get_sys_prompt(GEN_NAME.lower())
GEN_INIT_PROMPT = f"Generate an initial test suite for the local project `{PUT_NAME}` based on the given requirements!"
GEN_ERROR_PROMPT = f"Error(s) during the collection or fail(s) occurred during execution of the test suite for the local project `{PUT_NAME}`! Please correct the test suite!"
GEN_REFINE_PROMPT = f"Refine the existing test suite for the local project `{PUT_NAME}` based on the latest evaluation!"

DEB_NAME = "DEBUGGER"
DEB_SYS_PROMPT = get_sys_prompt(DEB_NAME.lower())
DEB_PROMPT = f"Error(s) during the collection or fail(s) occurred during execution of the test suite for the local project `{PUT_NAME}`! Please analyse them!"

EVAL_NAME = "EVALUATOR"
EVAL_SYS_PROMPT = get_sys_prompt(EVAL_NAME.lower())
EVAL_PROMPT = f"Evaluate the given test suite for the local project `{PUT_NAME}` based on the latest execution reports!"
