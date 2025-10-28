from pathlib import Path

import pandas as pd

data_path = Path("<<DATA_OUTPUT_PATH>>").resolve()
tables_path = Path("<<TABLES_PATH>>").resolve()

# collect data
lift_df = pd.read_csv(data_path / "fss_lps_all_trials.csv")


def create_coverage_table(df, caption, label, file_name):
    # get mean and median
    mean, median = df.mean(), df.median()
    mean["trial"], median["trial"] = "mean", "median"

    # append mean and median at end
    df = df.reset_index()
    df.loc[len(df)] = mean
    df.loc[len(df)] = median
    df = df.drop(columns=["index"])

    # clean up data types for export
    df = df.astype({"line_valid": int, "line_covered": int, "branch_valid": int, "branch_covered": int})
    df["line_cov"] = df["line_cov"].map(lambda x: f"{x * 100:.2f}")
    df["branch_cov"] = df["branch_cov"].map(lambda x: f"{x * 100:.2f}")

    # export rows with values only
    data = df.to_latex(index=False, escape=False).strip().split("\n")[4:-2]

    # insert table layout
    data.insert(-2, r"\midrule")
    data.insert(-2, r"\midrule")
    data.insert(0, r"\midrule")
    data.insert(0, r"\textbf{Total Branches} & \textbf{Covered Branches} & \textbf{Branch Coverage (\%)} \\")
    data.insert(0, r"\textbf{Trial ID} & \textbf{Total Lines} & \textbf{Covered Lines} & \textbf{Line Coverage (\%)} &")
    data.insert(0, r"\toprule")
    data.append(r"\bottomrule")

    # shift table data
    data = [2 * "    " + e for e in data]

    # build table around it
    data.insert(0, r"    \begin{tabularx}{\linewidth}{lCCCCCC}")
    data.insert(0, r"    \centering")
    data.insert(0, r"\begin{table}[H]")
    data.append(r"    \end{tabularx}")
    data.append(rf"    \caption{{{caption}}}")
    data.append(rf"    \label{{{label}}}")
    data.append(r"\end{table}")

    with open(tables_path / file_name, "w") as file:
        file.write("\n".join(data))


fss_df = lift_df.dropna(subset=["fss_iteration"])[["trial", "fss_line_valid", "fss_line_covered", "fss_line_cov",
                                                   "fss_branch_valid", "fss_branch_covered", "fss_branch_cov"]].copy()
fss_df.columns = fss_df.columns.str.removeprefix("fss_")
create_coverage_table(fss_df, r"Coverages of the \acrlongpl{FSS} for all trials",
                      "app:cov_fss", "fss_cov_table.tex")

lps_df = lift_df.dropna(subset=["lps_iteration"])[["trial", "lps_line_valid", "lps_line_covered", "lps_line_cov",
                                                   "lps_branch_valid", "lps_branch_covered", "lps_branch_cov"]].copy()
lps_df.columns = lps_df.columns.str.removeprefix("lps_")
create_coverage_table(lps_df, r"Coverages of the \acrlongpl{LPS} for all trials",
                      "app:cov_lps", "lps_cov_table.tex")
