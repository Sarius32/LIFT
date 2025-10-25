import re
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory as TmpDir
from zipfile import ZipFile

import pandas as pd

ITER_COUNT = 25
LIFT_OUTPUT = Path("<<LIFT_OUTPUT_PATH>>")

analysis_output = Path("<<DATA_OUTPUT_PATH>>")
analysis_output.mkdir(exist_ok=True)


def get_execution_dict(exec_xml):
    mapping = {"errors": "errors",
               "failures": "tests_failed", "skipped": "tests_skipped", "tests": "tests_total",
               "time": "exec_time"}

    tree = ET.parse(exec_xml)
    root = tree.getroot()
    cleaned = {k: v for k, v in root.find("testsuite").attrib.items() if k in mapping.keys()}

    return {mapping[k]: v for k, v in cleaned.items()}


def get_coverage_dict(cov_xml):
    mapping = {"lines-covered": "line_covered", "lines-valid": "line_valid", "line-rate": "line_cov",
               "branches-covered": "branch_covered", "branches-valid": "branch_valid", "branch-rate": "branch_cov"}

    tree = ET.parse(cov_xml)
    root = tree.getroot()
    cleaned = {k: v for k, v in root.attrib.items() if k in mapping.keys()}
    return {mapping[k]: v for k, v in cleaned.items()}


overall_stats = dict()
for trial in [e for e in LIFT_OUTPUT.glob("archive_*") if e.is_dir()]:
    trial_id = int(re.search(r"archive_(\d+)", trial.name).group(1))

    fss, lps = (trial / "_FSS_"), (trial / "_LPS_")

    reports_zips = [*trial.glob("reports_*.zip")]
    tests_zips = [*trial.glob("tests_*.zip")]

    if len(reports_zips) != len(tests_zips):
        print(f"⚠️ Trial {trial_id:>02d}: Not the same number of test and report iterations found!")
        continue

    if len(reports_zips) != ITER_COUNT:
        print(f"⚠️ Trial {trial_id:>02d}: Less then {ITER_COUNT} iterations executed!")
        continue

    iteration_data = dict()
    for reports_zip in reports_zips:
        iteration = int(re.search(r"reports_(\d+)\.zip", reports_zip.name).group(1))

        with TmpDir() as tmpdir:
            tmp_path = Path(tmpdir)
            with ZipFile(reports_zip, "r") as zip_ref:
                zip_ref.extractall(tmp_path)

            exec_path = tmp_path / "execution-report.xml"
            cov_path = tmp_path / "coverage-report.xml"
            fixes, evaluation = (tmp_path / "fixes.md"), (tmp_path / "evaluation.md")

            if not fixes.exists() and not evaluation.exists():
                print(f"⚠️ Trial {trial_id:>02d}, Iteration {iteration:>02d}: "
                      f"No agent feedback (neither fixes.md nor evaluation.md) found!")
                continue

            if not exec_path.exists():
                print(f"⚠️ Trial {trial_id:>02d}, Iteration {iteration:>02d}: "
                      f"No execution report found!")
                continue

            if not cov_path.exists():
                print(f"⚠️ Trial {trial_id:>02d}, Iteration {iteration:>02d}: "
                      f"No coverage report found!")
                continue

            exec_data = get_execution_dict(exec_path)
            cov_data = get_coverage_dict(cov_path)

            final = ("<FINAL>" in evaluation.read_text("UTF-8")) if evaluation.exists() else None

            iteration_data[iteration] = {**exec_data, **cov_data, "final": final}

    numeric_cols = ['errors', 'tests_failed', 'tests_skipped', 'tests_total', 'exec_time',
                    'line_valid', 'line_covered', 'line_cov', 'branch_valid', 'branch_covered', 'branch_cov']
    df = pd.DataFrame.from_dict(iteration_data, orient="index")
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
    df.index.name = "iteration"

    out_csv = analysis_output / f"trial_{trial_id:>02d}.csv"
    df.to_csv(out_csv)
    print(f"✅ Trial {trial_id:>02d}: Data collected and stored in {out_csv}")

    if fss.exists():
        iteration = int(re.search(r"FSS_(\d+)", list(fss.glob("FSS_*"))[0].name).group(1))
        fss_data = df.loc[iteration].copy()
        fss_data["iteration"] = iteration
    else:
        fss_data = pd.Series({col: None for col in df.columns})

    if lps.exists():
        iteration = int(re.search(r"LPS_(\d+)", list(lps.glob("LPS_*"))[0].name).group(1))
        lps_data = df.loc[iteration].copy()
        lps_data["iteration"] = iteration
    else:
        lps_data = pd.Series({col: None for col in df.columns})

    fss_data = fss_data.drop("final").add_prefix("fss_")
    lps_data = lps_data.drop("final").add_prefix("lps_")

    overall_stats[trial_id] = fss_data.combine_first(lps_data)

overall = pd.DataFrame.from_dict(overall_stats, orient="index")
overall.index.name = "trial"

out_csv = analysis_output / "fss_lps_all_trials.csv"
overall.to_csv(out_csv)
print(f"\n✅ Data Collection done for all trials! Overall statistics stored in {out_csv}")
