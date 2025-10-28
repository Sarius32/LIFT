import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

data_path = Path("<<DATA_OUTPUT_PATH>>").resolve()
plots_path = Path("<<PLOTS_PATH>>").resolve()

# collect trial data into lift_df
lift_df = pd.DataFrame()
for trial_csv in data_path.glob("trial_*.csv"):
    trial_id = int(re.search(r"trial_(\d+)\.csv", trial_csv.name).group(1))
    trial_df = pd.read_csv(trial_csv, index_col="iteration")

    # get total number of tests (cleared total for iteration with errors => pytest total reporting incorrect here)
    trial_df.loc[trial_df["errors"] > 0, "line_cov"] = None
    coverage = trial_df["line_cov"]

    df = pd.DataFrame({"line_cov": coverage}).assign(trial_id=trial_id) \
        .set_index("trial_id", append=True).reorder_levels(["trial_id", "iteration"])
    lift_df = pd.concat([lift_df, df])

del trial_df, coverage, df

# get the mean & quantiles values per iteration over all trials
plot_df = pd.DataFrame(index=range(25))
plot_df.index.name = "iteration"
plot_df["mean"] = lift_df.groupby("iteration").mean()
plot_df["median"] = lift_df.groupby("iteration").median()
plot_df["quant_02"] = lift_df.groupby("iteration").quantile(.2)
plot_df["quant_08"] = lift_df.groupby("iteration").quantile(.8)
plot_df = plot_df.reset_index()

mean = plot_df["mean"].copy()
mean.loc[0] = 0
slope, intercept = np.polyfit(plot_df["iteration"], mean, 1)

plt.figure(figsize=(9, 6))
sns.set_theme()

sns.lineplot(data=plot_df, x="iteration", y="mean", marker="o", label=r"$\bar{l}_k$ - mean Line coverage")
sns.lineplot(data=plot_df, x="iteration", y="median", linestyle="--", label=r"$\tilde{l}_k$ - median Line coverage")
sns.lineplot(data=plot_df, x="iteration", y="quant_02", color="gray")
sns.lineplot(data=plot_df, x="iteration", y="quant_08", color="gray")

plt.fill_between(plot_df["iteration"], plot_df["quant_02"], plot_df["quant_08"],
                 color="gray", alpha=0.2, linewidth=0,
                 label=r"$l_{k,(0.2:0.8)}$ - Interquantile Line coverage range (0.2-0.8)")

plt.xlabel(r"Iteration $k$")
plt.ylabel(r"Line coverage")
plt.legend(loc="lower right")

plt.tight_layout()
plt.savefig(plots_path / "line_coverage_agg.svg")
print(f"✅ Plot for aggregated Line coverage generated: {(plots_path / "line_coverage_agg.svg")}")
