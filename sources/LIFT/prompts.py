from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

LOGGER = getLogger(__name__)


@dataclass
class GeneratorPrompts:
    name: str
    system: str
    init: str
    error: str
    refine: str


@dataclass
class DebuggerPrompts:
    name: str
    system: str
    instr: str


EvaluatorPrompts = DebuggerPrompts


class Prompts:
    def __init__(self, inputs_dir: Path, put_name: str):
        LOGGER.info(f"Loading Prompts from {inputs_dir}")

        name = "GENERATOR"
        self.generator = GeneratorPrompts(
            name, self._get_sys_prompt(inputs_dir, name),
            f"Generate an initial test suite for the local project `{put_name}` based on the given requirements!",
            f"Error(s) during the collection or fail(s) occurred during execution of the test suite "
            f"for the local project `{put_name}`! Please correct the test suite!",
            f"Refine the existing test suite for the local project `{put_name}` based on the latest evaluation!"
        )

        name = "DEBUGGER"
        self.debugger = DebuggerPrompts(
            name, self._get_sys_prompt(inputs_dir, name),
            f"Error(s) during the collection or fail(s) occurred during execution of the test suite "
            f"for the local project `{put_name}`! Please analyse them!"
        )

        name = "EVALUATOR"
        self.evaluator = EvaluatorPrompts(
            name, self._get_sys_prompt(inputs_dir, name),
            f"Evaluate the given test suite for the local project `{put_name}` based on the latest execution reports!"
        )

    @staticmethod
    def _get_sys_prompt(inputs_dir: Path, name: str):
        return (inputs_dir / (name.lower() + ".md")).read_text().strip()
