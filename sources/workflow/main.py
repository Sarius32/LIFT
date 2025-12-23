import env
import logging_

env.log()

LOGGER = logging_.get_logger(__name__)

from agents import Generator, Evaluator, Debugger
from archiving import archive_agent, archive_suite, archive_tests, archive_reports
from archiving import SuiteType as SType
from prompts import GEN_INIT_PROMPT, GEN_REFINE_PROMPT, GEN_ERROR_PROMPT
from project_utils import ToolCallResult
from utils import setup_new_project, execute_tests


def main():
    first_final = True

    setup_new_project()

    gen_prompt = GEN_INIT_PROMPT
    iteration = 0
    for iteration in range(env.MAX_ITER):
        LOGGER.info(f"--- ITERATION #{iteration:02d} ---")

        # generate/refine suite
        LOGGER.info(" + GENERATION + ")
        generator = Generator(iteration)
        generator.query(gen_prompt)
        archive_agent(env.ARCHIVE_CON, generator, iteration)

        # archive last iterations output + feedback
        archive_reports(env.LIFT_ARCHIVE, env.REPORTS_PATH, iteration - 1) if iteration > 0 else None

        # execute test suite
        LOGGER.info(" + EXECUTION + ")
        passing = execute_tests()

        if not passing:
            # provide fixes (DEBUGGER)
            LOGGER.info(" + DEBUGGER + ")
            debugger = Debugger(iteration)
            debugger.query()
            gen_prompt = GEN_ERROR_PROMPT
            archive_agent(env.ARCHIVE_CON, debugger, iteration)

        else:
            # run EVALUATOR
            LOGGER.info(f" + EVALUATION + ")
            evaluator = Evaluator(iteration)
            evaluation = evaluator.query()
            gen_prompt = GEN_REFINE_PROMPT
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
