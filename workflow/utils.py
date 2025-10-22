import pickle

import logging_

LOGGER = logging_.get_logger(__name__)

import shutil, subprocess, sys

from agents import Agent
from env import PROJECT_PATH, DATA_PATH, LIFT_ARCHIVE, ARCHIVE_CON, PUT_NAME, PUT_PATH, TESTS_PATH, REPORTS_PATH


def create_new_project() -> None:
    # archive existing
    if PROJECT_PATH.exists():
        LOGGER.error(f"LIFT folder already exists. No need LIFT process started!")
        exit(-1)

    # create & fill project folder
    PROJECT_PATH.mkdir()
    input_put_path = (DATA_PATH / PUT_NAME).resolve()
    if not input_put_path.exists() or not input_put_path.is_dir():
        LOGGER.error(f"PUT {PUT_NAME} for LIFT not found in {DATA_PATH}!")
        exit(-1)

    # copy PUT
    shutil.copytree(input_put_path, PUT_PATH)

    # copy eval template, requirements and pytest html report config
    for file in ["evaluation_template.md", "program-requirements.yml"]:
        shutil.copy((DATA_PATH / file), (PROJECT_PATH / file))

    with open(DATA_PATH / "pytest_html_report.yml") as file:
        lines = file.readlines()
    lines = [line if "<<REPORT_DIR>>" not in line else f"  report_dir: {REPORTS_PATH}" for line in lines]
    with open(PROJECT_PATH / "pytest_html_report.yml", "w") as file:
        file.writelines(lines)

    # create archive & project folders
    LIFT_ARCHIVE.mkdir(exist_ok=True)
    ARCHIVE_CON.mkdir(exist_ok=True)
    TESTS_PATH.mkdir()
    REPORTS_PATH.mkdir()


def archive_tests(iteration: int) -> None:
    # remove __pycache__ in tests
    pycache = TESTS_PATH / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache, ignore_errors=True)

    test_zip = shutil.make_archive(LIFT_ARCHIVE / f"tests_{iteration:02d}", "zip", TESTS_PATH)
    LOGGER.info(f"ARCHIVING: tests for iteration {iteration} -> {test_zip}")


def archive_exec_eval(iteration: int, delete=True) -> None:
    # zip reports
    progress_zip = shutil.make_archive(LIFT_ARCHIVE / f"reports_{iteration:02d}", "zip", REPORTS_PATH)

    # delete reports if wanted
    if delete:
        shutil.rmtree(REPORTS_PATH, ignore_errors=True)

    LOGGER.info(f"ARCHIVING: reports for iteration {iteration} -> {progress_zip}")


def archive_first_final_suite(iteration: int) -> None:
    fss_path = (LIFT_ARCHIVE / "_FSS_").resolve()

    # copy reports
    shutil.copytree(REPORTS_PATH, fss_path)

    # copy tests
    shutil.copytree(TESTS_PATH, fss_path / "tests")
    shutil.rmtree(fss_path / "tests" / "__pycache__", ignore_errors=True)

    # create iteration marker
    open(fss_path / f"FSS_{iteration}", "x")

    LOGGER.info(f"ARCHIVING: First Sufficient Suite for iteration {iteration}")


def archive_last_passing_suite(iteration: int) -> None:
    lps_path = (LIFT_ARCHIVE / "_LPS_new").resolve()

    # copy reports
    shutil.copytree(REPORTS_PATH, lps_path)

    # copy tests
    shutil.copytree(TESTS_PATH, lps_path / "tests")
    shutil.rmtree(lps_path / "tests" / "__pycache__", ignore_errors=True)

    # create iteration marker
    open(lps_path / f"LPS_{iteration}", "x")

    # copy new LPS
    shutil.rmtree(LIFT_ARCHIVE / "_LPS_", ignore_errors=True)
    shutil.move(lps_path, LIFT_ARCHIVE / "_LPS_")

    LOGGER.info(f"ARCHIVING: Updating Last Passing Suite to iteration {iteration}")


def rm_report_temps() -> None:
    [file.unlink() for file in REPORTS_PATH.glob("*.json")]


def execute_tests() -> bool:
    """ Returns True if all tests passed """
    e = subprocess.run([sys.executable, "-m", "pytest", PROJECT_PATH.absolute(),
                        f"--rootdir={PROJECT_PATH.absolute()}",
                        f"--cache-clear", f"--disable-warnings",
                        f"--junit-xml={(REPORTS_PATH / 'execution-report.xml').absolute()}",
                        f"--cov=simplejson", f"--cov-branch",
                        f"--cov-report=xml:{(REPORTS_PATH / 'coverage-report.xml').absolute()}"])

    # remove pytest-html-report temp files
    rm_report_temps()

    return e.returncode == 0


def archive_agent(agent: Agent, iteration: int) -> None:
    with open(ARCHIVE_CON / f"{iteration:02d}_{agent.type_}.pkl", "wb") as file:
        pickle.dump(agent, file)
