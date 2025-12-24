import pickle
import shutil
from enum import Enum
from logging import getLogger
from pathlib import Path

from .agents import Agent

LOGGER = getLogger(__name__)


class SuiteType(Enum):
    FSS = "FSS"
    LPS = "LPS"


def archive_agent(archive: Path, agent: Agent, iteration: int) -> None:
    loc = archive / f"{iteration:02d}_{agent.type_.lower()}.pkl"
    with open(loc, "wb") as file:
        pickle.dump(agent, file)
        LOGGER.info(f"{agent.type_} for iteration {iteration} archived at {loc.absolute()}")


def archive_tests(archive: Path, put_tests: Path, iteration: int) -> None:
    # remove __pycache__ in tests
    pycache = put_tests / "__pycache__"
    if pycache.exists():
        shutil.rmtree(pycache, ignore_errors=True)

    test_zip = shutil.make_archive(base_name=str(archive / f"tests_{iteration:02d}"),
                                   format="zip", root_dir=put_tests)
    LOGGER.info(f"Tests for iteration {iteration} archived at {test_zip}")


def archive_reports(archive: Path, put_reports: Path, iteration: int, delete=True) -> None:
    # zip reports
    progress_zip = shutil.make_archive(base_name=str(archive / f"reports_{iteration:02d}"),
                                       format="zip", root_dir=put_reports)
    LOGGER.info(f"Reports for iteration {iteration} archived at {progress_zip}")

    # delete reports if wanted
    if delete:
        shutil.rmtree(put_reports, ignore_errors=True)
        LOGGER.info(f"Current reports removed from {put_reports.absolute()}")


def archive_suite(archive: Path, put_tests: Path, put_reports: Path,
                  type_: SuiteType, iteration: int) -> None:
    suite_name = "_" + type_.name + "_" + ("new" if type_ == SuiteType.LPS else "")
    suite_path = (archive / suite_name).resolve()

    # copy reports
    shutil.copytree(put_reports, suite_path)

    # copy tests
    shutil.copytree(put_tests, suite_path / "tests")
    shutil.rmtree(suite_path / "tests" / "__pycache__", ignore_errors=True)

    # create iteration marker
    open(suite_path / f"{type_.name}_{iteration}", "x")

    # copy new LPS
    if type_ == SuiteType.LPS:
        shutil.rmtree(archive / "_LPS_", ignore_errors=True)
        shutil.move(suite_path, archive / "_LPS_")
        suite_path = archive / "_LPS_"

        LOGGER.info(f"Updated Last Passing Suite (LPS) for iteration {iteration} at {suite_path.absolute()}")
    else:
        LOGGER.info(f"First Sufficient Suite (FSS) for iteration {iteration} archived at {suite_path.absolute()}")
