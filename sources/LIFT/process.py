from logging import getLogger
from pathlib import Path

from .agents import Generator, GeneratorState, Debugger, Evaluator
from .archiving import archive_agent, archive_suite, archive_tests, archive_reports
from .archiving import SuiteType as SType
from .config import LiftConfig
from .paths import Paths
from .project_utils import ToolCallResult
from .prompts import Prompts
from .requirements import parse_requirements_doc
from .tools import init_tools
from .utils import check_inputs, setup_new_project, execute_tests

LOGGER = getLogger(__name__)


class Process:
    def __init__(self, root: Path, inputs: Path, env_file: Path):
        self._config = LiftConfig(env_file)
        self._paths = Paths(root, inputs, self._config.put_name)

        check_inputs(self._config, self._paths)

        self._prompts = Prompts(self._paths.inputs, self._config.put_name)
        self._reqs = parse_requirements_doc(self._paths.inputs / "program-requirements.yml")

        init_tools(self._paths.project, self._reqs)

    def run(self):
        setup_new_project(self._config, self._paths, self._reqs)

        first_final = True
        iteration = 0

        gen_state = GeneratorState.INIT
        for iteration in range(self._config.max_iterations):
            LOGGER.info(f"--- ITERATION #{iteration:02d} ---")

            # generate/refine suite
            LOGGER.info(" + GENERATION + ")
            generator = Generator(self._config.api_key, self._config.generator, self._prompts.generator, iteration)
            generator.run(gen_state)
            archive_agent(self._paths.conversation_archive, generator, iteration)

            # archive last iterations output + feedback
            archive_reports(self._paths.archive, self._paths.reports, iteration - 1) if iteration > 0 else None

            # execute test suite
            LOGGER.info(" + EXECUTION + ")
            passing = execute_tests(self._config.put_name, self._paths)

            if not passing:
                # provide fixes (DEBUGGER)
                LOGGER.info(" + DEBUGGER + ")
                debugger = Debugger(self._config.api_key, self._config.debugger, self._prompts.debugger,
                                    self._paths.reports, iteration)
                debugger.debug()
                gen_state = GeneratorState.ERROR
                archive_agent(self._paths.conversation_archive, debugger, iteration)

            else:
                # run EVALUATOR
                LOGGER.info(f" + EVALUATION + ")
                evaluator = Evaluator(self._config.api_key, self._config.evaluator, self._prompts.evaluator,
                                      self._paths.reports, iteration)
                evaluation = evaluator.evaluate()
                gen_state = GeneratorState.REFINE
                archive_agent(self._paths.conversation_archive, evaluator, iteration)

                # archive FSS (First Sufficient Suite)
                if evaluation == ToolCallResult.END_FINAL_SUITE and first_final:
                    archive_suite(self._paths.archive, self._paths.tests, self._paths.reports, SType.FSS, iteration)
                    first_final = False

                # archive LPS (Last Passing Suite)
                archive_suite(self._paths.archive, self._paths.tests, self._paths.reports, SType.LPS, iteration)

            # archive tests
            archive_tests(self._paths.archive, self._paths.tests, iteration)

        # archive last iteration
        archive_reports(self._paths.archive, self._paths.reports, iteration)

        LOGGER.info("LIFT concluded!")
