import logging_

LOGGER = logging_.get_logger(__name__)

import shutil, subprocess, sys

from env import PROJECT_PATH, DATA_PATH, LIFT_ARCHIVE, ARCHIVE_CON, PUT_NAME, PUT_PATH, TESTS_PATH, REPORTS_PATH, \
    CONFIG_PATH
from report_utils import parse_cur_exec_report
from requirements import parse_requirements_doc, get_requirements_only


def setup_new_project() -> None:
    # archive existing
    if PROJECT_PATH.exists():
        LOGGER.error(f"LIFT folder already exists. No LIFT process started!")
        exit(-1)

    # PUT is missing
    input_put_path = (DATA_PATH / PUT_NAME).resolve()
    if not input_put_path.exists() or not input_put_path.is_dir():
        LOGGER.error(f"PUT {PUT_NAME} for LIFT not found in {DATA_PATH}!")
        exit(-1)

    # Evaluation template is missing
    eval_template = DATA_PATH / "evaluation_template.md"
    if not eval_template.exists():
        LOGGER.error(f"Evaluation template (evaluation_template.md) not found in {DATA_PATH}!")
        exit(-1)

    # Requirements document is missing
    req_document = DATA_PATH / "program-requirements.yml"
    if not req_document.exists():
        LOGGER.error(f"Program requirements (program-requirements.yml) not found in {DATA_PATH}!")
        exit(-1)

    # PyTest HTML Report Config is missing
    pytest_html_report = DATA_PATH / "pytest_html_report.yml"
    if not pytest_html_report.exists():
        LOGGER.error(f"PyTest HTML Report Config (pytest_html_report.yml) not found in {DATA_PATH}!")
        exit(-1)

    # create project folder
    PROJECT_PATH.mkdir()

    # copy PUT
    shutil.copytree(input_put_path, PUT_PATH)

    # copy eval template
    shutil.copy(eval_template, (PROJECT_PATH / "evaluation_template.md"))

    # parse the requirements for later tool use (requirements doc not provided to agents directly)
    parse_requirements_doc(req_document)
    reqs = get_requirements_only()

    # load pytest html report template
    with open(pytest_html_report) as file:
        lines = file.readlines()

    # create filled pytest HTML report config with report dir and requirements
    new_lines = []
    for line in lines:
        if "<<REPORT_DIR>>" in line:
            new_lines.append(f"  report_dir: \"{REPORTS_PATH}\"\n")
            continue
        if "<<REQUIREMENT_IDS>>" in line:
            [new_lines.append(f"  {req.id}: \"{req.title}\"\n") for req in reqs]
            continue
        new_lines.append(line)
    CONFIG_PATH.mkdir(exist_ok=True)
    with open(CONFIG_PATH / "pytest_html_report.yml", "w") as file:
        file.writelines(new_lines)

    # create archive & project folders
    LIFT_ARCHIVE.mkdir(exist_ok=True)
    ARCHIVE_CON.mkdir(exist_ok=True)
    TESTS_PATH.mkdir()
    REPORTS_PATH.mkdir()


def rm_report_temps() -> None:
    [file.unlink() for file in REPORTS_PATH.glob("*.json")]


def execute_tests() -> bool:
    """ Executes the current state of the test suite and parses the generated report. Returns True if all tests passed. """
    exec_report_file = (REPORTS_PATH / 'execution-report.xml')

    # execute pytest as a subprocess
    e = subprocess.run([sys.executable, "-m", "pytest", PROJECT_PATH.absolute(),
                        f"--rootdir={PROJECT_PATH.absolute()}",
                        f"--cache-clear", f"--disable-warnings",
                        f"--junit-xml={exec_report_file.absolute()}",
                        f"--cov={PUT_NAME}", f"--cov-branch",
                        f"--cov-report=xml:{(REPORTS_PATH / 'coverage-report.xml').absolute()}"])

    # parse the last execution report
    parse_cur_exec_report(exec_report_file)

    # remove pytest-html-report temp files
    rm_report_temps()

    return e.returncode == 0
