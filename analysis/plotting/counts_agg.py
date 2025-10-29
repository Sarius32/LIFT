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
    trial_df.loc[trial_df["errors"] > 0, "tests_total"] = None
    tests = trial_df["tests_total"]

    df = pd.DataFrame({"tests_total": tests}).assign(trial_id=trial_id) \
        .set_index("trial_id", append=True).reorder_levels(["trial_id", "iteration"])
    lift_df = pd.concat([lift_df, df])

del trial_df, tests, df


### plot individual trials ###
def individual_plot():
    plt.figure(figsize=(9, 6))
    sns.set_theme()

    palette = sns.color_palette("husl", n_colors=len(lift_df.index.get_level_values("trial_id").unique()))
    sns.lineplot(data=lift_df.reset_index(), x="iteration", y="tests_total", hue="trial_id", legend=False,
                 alpha=0.7, marker="o", palette=palette)
    plt.xlabel(r"Iteration $k$")
    plt.ylabel(r"Test count $t$")

    plt.tight_layout()
    plt.savefig(plots_path / "test_counts_ind.svg")
    print(f"✅ Plot for individual Test counts generated: {(plots_path / "test_counts_ind.svg")}")


### plot aggregated mean, median & quantile ###
def agg_test_count_plot():
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

    sns.lineplot(data=plot_df, x="iteration", y="mean", marker="o", label=r"$\bar{t}_k$ - mean Test count")
    sns.lineplot(x=[1, 24], y=[slope+intercept, 24*slope+intercept], linestyle=(0, (1, 3)), color="red", label="Trend of the mean Test count")
    sns.lineplot(data=plot_df, x="iteration", y="median", linestyle="--", label=r"$\tilde{t}_k$ - median Test count")
    sns.lineplot(data=plot_df, x="iteration", y="quant_02", color="gray")
    sns.lineplot(data=plot_df, x="iteration", y="quant_08", color="gray")

    plt.fill_between(plot_df["iteration"], plot_df["quant_02"], plot_df["quant_08"],
                     color="gray", alpha=0.2, linewidth=0,
                     label=r"$t_{k,(0.2:0.8)}$ - Interquantile Test count range (0.2-0.8)")

    plt.xlabel(r"Iteration $k$")
    plt.ylabel(r"Test count $t$")
    plt.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(plots_path / "test_counts_agg.svg")
    print(f"✅ Plot for aggregated Test counts generated: {(plots_path / "test_counts_agg.svg")}")


### plot growth of mean/median over iterations ###
def test_count_growth_plots():
    df = pd.DataFrame()
    df["mean"] = lift_df.groupby("iteration").mean()
    df["median"] = lift_df.groupby("iteration").median()
    df.loc[0, "mean"] = 0
    df.loc[0, "median"] = 0
    df["mean_diff"] = df["mean"].diff()
    df["median_diff"] = df["median"].diff()
    df["mean_perc"] = df["mean_diff"] / df["mean"]
    df["median_perc"] = df["median_diff"] / df["mean"]
    df = df.reset_index()

    plt.figure(figsize=(9, 6))
    sns.set_theme()

    sns.lineplot(data=df, x="iteration", y="mean_diff", marker="o", label="Mean")
    sns.lineplot(data=df, x="iteration", y="median_diff", linestyle="--", label="Median")

    plt.xlabel(r"Iteration $k$")
    plt.ylabel(r"Test count growth")
    plt.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(plots_path / "test_count_growth.svg")
    print(f"✅ Plot for Test count growth generated: {(plots_path / "test_count_growth.svg")}")

    plt.figure(figsize=(9, 6))
    sns.set_theme()

    sns.lineplot(data=df, x="iteration", y="mean_perc", marker="o", label="Mean")
    sns.lineplot(data=df, x="iteration", y="median_perc", linestyle="--", label="Median")

    plt.xlabel(r"Iteration $k$")
    plt.ylabel(r"Test count growth")
    plt.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(plots_path / "test_count_growth_perc.svg")
    print(f"✅ Plot for percentual Test count growth generated: {(plots_path / "test_count_growth_perc.svg")}")


individual_plot()
agg_test_count_plot()
test_count_growth_plots()
