from pathlib import Path

import pandas as pd

data_path = Path("<<DATA_OUTPUT_PATH>>").resolve()
tables_path = Path("<<TABLES_PATH>>").resolve()

# collect data
lift_df = pd.read_csv(data_path / "fss_lps_all_trials.csv")

df = lift_df[["trial", "fss_tests_total", "fss_tests_skipped", "fss_exec_time",
              "lps_tests_total", "lps_tests_skipped", "lps_exec_time"]].copy()

# get mean and median
mean, median = df.mean(), df.median()
mean["trial"], median["trial"] = "mean", "median"

# append mean and median at end
df = df.reset_index()
df.loc[len(df)] = mean
df.loc[len(df)] = median
df = df.drop(columns=["index"])

# clean up data types for export
for col in ["fss_tests_total", "fss_tests_skipped", "lps_tests_total", "lps_tests_skipped"]:
    df[col] = df[col].round().astype("Int64").astype(str).replace("<NA>", "-")
df["fss_exec_time"] = df["fss_exec_time"].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "-")
df["lps_exec_time"] = df["lps_exec_time"].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "-")

# export rows with values only
data = df.to_latex(index=False, escape=False).strip().split("\n")[4:-2]

# insert table layout
data.insert(-2, r"\midrule")
data.insert(-2, r"\midrule")
data.insert(0, r"\midrule")
data.insert(0, r"\textbf{Total Tests} & \textbf{Skipped Tests} & \textbf{Execution Times ($s$)} \\")
data.insert(0, r"& \textbf{Total Tests} & \textbf{Skipped Tests} & \textbf{Execution Times ($s$)} &")
data.insert(0, r"\multicolumn{3}{c}{\acrlong{FSS}} & \multicolumn{3}{c}{\acrlong{LPS}} \\")
data.insert(0, r"\multirow[c]{2}{*}{\textbf{Trial ID}} &")
data.insert(0, r"\toprule")
data.append(r"\bottomrule")

# shift table data
data = [2 * "    " + e for e in data]

# build table around it
data.insert(0, r"    \begin{tabularx}{\linewidth}{lCCCCCC}")
data.insert(0, r"    \centering")
data.insert(0, r"\begin{table}[H]")
data.append(r"    \end{tabularx}")
data.append(r"    \caption{Test suite size and execution time for the \acrlongpl{FSS} "
            r"\& \acrlongpl{LPS} for all Trials}")
data.append(r"    \label{tab:test_suite_size_time_all_trials}")
data.append(r"\end{table}")

with open(tables_path / "test_counts.tex", "w") as file:
    file.write("\n".join(data))
