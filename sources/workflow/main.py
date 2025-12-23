import env
import logging_
from logging import getLogger

env.log()

LOGGER = getLogger(__name__)

from agents import Generator, GeneratorState, Evaluator, Debugger
from archiving import archive_agent, archive_suite, archive_tests, archive_reports
from archiving import SuiteType as SType
from prompts import GEN_SYS_PROMPT, GEN_INIT_PROMPT, GEN_REFINE_PROMPT, GEN_ERROR_PROMPT, GeneratorPrompts, \
    DebuggerPrompts, DEB_PROMPT, DEB_SYS_PROMPT, EvaluatorPrompts, EVAL_PROMPT, EVAL_SYS_PROMPT
from project_utils import ToolCallResult
from utils import setup_new_project, execute_tests


def main():
    first_final = True

    setup_new_project()

    gen_state = GeneratorState.INIT
    iteration = 0
    for iteration in range(env.MAX_ITER):
        LOGGER.info(f"--- ITERATION #{iteration:02d} ---")

        # generate/refine suite
        LOGGER.info(" + GENERATION + ")
        generator = Generator(env.GEN_MODEL,
                              GeneratorPrompts(GEN_SYS_PROMPT, GEN_INIT_PROMPT, GEN_ERROR_PROMPT, GEN_REFINE_PROMPT),
                              iteration)
        generator.run(gen_state)
        archive_agent(env.ARCHIVE_CON, generator, iteration)

        # archive last iterations output + feedback
        archive_reports(env.LIFT_ARCHIVE, env.REPORTS_PATH, iteration - 1) if iteration > 0 else None

        # execute test suite
        LOGGER.info(" + EXECUTION + ")
        passing = execute_tests()

        if not passing:
            # provide fixes (DEBUGGER)
            LOGGER.info(" + DEBUGGER + ")
            debugger = Debugger(env.DEBUG_MODEL, DebuggerPrompts(DEB_SYS_PROMPT, DEB_PROMPT), iteration)
            debugger.debug()
            gen_state = GeneratorState.ERROR
            archive_agent(env.ARCHIVE_CON, debugger, iteration)

        else:
            # run EVALUATOR
            LOGGER.info(f" + EVALUATION + ")
            evaluator = Evaluator(env.EVAL_MODEL, EvaluatorPrompts(EVAL_SYS_PROMPT, EVAL_PROMPT), iteration)
            evaluation = evaluator.evaluate()
            gen_state = GeneratorState.REFINE
            archive_agent(env.ARCHIVE_CON, evaluator, iteration)

            # archive FSS (First Sufficient Suite)
            if evaluation == ToolCallResult.END_FINAL_SUITE and first_final:
                archive_suite(env.LIFT_ARCHIVE, env.TESTS_PATH, env.REPORTS_PATH, SType.FSS, iteration)
                first_final = False

            # archive LPS (Last Passing Suite)
            archive_suite(env.LIFT_ARCHIVE, env.TESTS_PATH, env.REPORTS_PATH, SType.LPS, iteration)

        # archive tests
        archive_tests(env.LIFT_ARCHIVE, env.TESTS_PATH, iteration)

    # archive last iteration
    archive_reports(env.LIFT_ARCHIVE, env.REPORTS_PATH, iteration)


if __name__ == "__main__":
    main()
