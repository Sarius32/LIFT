import shutil, subprocess, sys
from logging import getLogger
from pathlib import Path

from .config import LiftConfig
from .paths import Paths
from .requirements import ReqScope

LOGGER = getLogger(__name__)

from .report_utils import parse_cur_exec_report


def check_inputs(config: LiftConfig, paths: Paths) -> None:
    # project existing
    if paths.project.exists():
        LOGGER.error(f"LIFT folder already exists at {paths.project.absolute()}. No LIFT process started!")
        raise Exception("LIFT folder already exists!")

    # Prompts missing
    prompts = [paths.inputs / "generator.md", paths.inputs / "debugger.md", paths.inputs / "evaluator.md"]
    for prompt in prompts:
        if not prompt.exists():
            LOGGER.error(f"{prompt.name[:-3].title()} System Prompt not found at {prompt.absolute()}!")
            raise FileNotFoundError(f"{prompt.name[:-3].title()} System Prompt ({prompt.name}) not found!")

    # PyTest HTML Report Config is missing
    if not paths.html_template.exists():
        LOGGER.error(f"PyTest HTML Report Config (pytest_html_report.yml) not found "
                     f"at {paths.html_template.absolute()}!")
        raise FileNotFoundError("PyTest HTML Report Config (pytest_html_report.yml) missing!")

    # PUT is missing
    input_put_path = (paths.inputs / config.put_name).resolve()
    if not input_put_path.exists() or not input_put_path.is_dir():
        LOGGER.error(f"PUT {config.put_name} for LIFT not found at {paths.inputs.absolute()}!")
        raise Exception(f"PUT {config.put_name} missing!")

    # Requirements document is missing
    if not paths.req_doc.exists():
        LOGGER.error(f"Program requirements (program-requirements.yml) not found at {paths.req_doc.absolute()}!")
        raise FileNotFoundError("Program requirements (program-requirements.yml) missing!")

    # Evaluation template is missing
    if not paths.eval_template.exists():
        LOGGER.error(f"Evaluation template (evaluation_template.md) not found at {paths.eval_template.absolute()}!")
        raise FileNotFoundError("Evaluation template (evaluation_template.md) missing!")


def setup_new_project(config: LiftConfig, paths: Paths, reqs: ReqScope) -> None:
    # create project folder
    paths.project.mkdir()

    # copy PUT
    shutil.copytree((paths.inputs / config.put_name), paths.put)

    # copy eval template
    shutil.copy(paths.eval_template, (paths.project / "evaluation_template.md"))

    # load pytest html report template
    with open(paths.eval_template) as file:
        lines = file.readlines()

    # create filled pytest HTML report config with report dir and requirements
    new_lines = []
    for line in lines:
        if "<<REPORT_DIR>>" in line:
            new_lines.append(f"  report_dir: \"{paths.reports.absolute()}\"\n")
            continue
        if "<<REQUIREMENT_IDS>>" in line:
            [new_lines.append(f"  {req.id}: \"{req.title}\"\n") for req in reqs.get_requirements()]
            continue
        new_lines.append(line)
    paths.config.mkdir(exist_ok=True)
    with open(paths.config / "pytest_html_report.yml", "w") as file:
        file.writelines(new_lines)

    # create archive & project folders
    paths.archive.mkdir(exist_ok=True)
    paths.conversation_archive.mkdir(exist_ok=True)
    paths.tests.mkdir()
    paths.reports.mkdir()

    LOGGER.info("Setup finished!")


def execute_tests(put_name: str, paths: Paths) -> bool:
    """ Executes the current state of the test suite and parses the generated report. Returns True if all tests passed. """
    exec_report_file = (paths.reports / 'execution-report.xml')

    # execute pytest as a subprocess
    e = subprocess.run([sys.executable, "-m", "pytest", paths.project.absolute(),
                        f"--rootdir={paths.project.absolute()}",
                        f"--cache-clear", f"--disable-warnings",
                        f"--junit-xml={exec_report_file.absolute()}",
                        f"--cov={put_name}", f"--cov-branch",
                        f"--cov-report=xml:{(paths.reports / 'coverage-report.xml').absolute()}"])

    # parse the last execution report
    parse_cur_exec_report(exec_report_file)

    # remove pytest-html-report temp files
    rm_report_temps(paths.reports)

    return e.returncode == 0


def rm_report_temps(reports_dir: Path) -> None:
    [file.unlink() for file in reports_dir.glob("*.json")]
