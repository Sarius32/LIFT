import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

data_path = Path("<<DATA_OUTPUT_PATH>>").resolve()
plots_path = Path("./plots").resolve()

# collect trial data into lift_df
lift_df = pd.DataFrame()
for trial_csv in data_path.glob("trial_*.csv"):
    trial_id = int(re.search(r"trial_(\d+)\.csv", trial_csv.name).group(1))
    trial_df = pd.read_csv(trial_csv, index_col="iteration")

    # nan => fix feedback in this iteration
    fix = trial_df["final"].isna().astype(int)

    # if 0 iteration not in series => fix iteration
    if 0 not in fix.index:
        fix.at[0] = 1
        fix.sort_index(inplace=True)

    # get the cumulative sum (over the iterations) of fixes
    fix_cum = fix.cumsum()

    # rate = cumulative sum over number of iterations (i.e. x times fixing in y iterations => x/y)
    fix_cum_rate = fix_cum / (fix.index.astype(int) + 1)

    df = pd.DataFrame({"fix": fix, "fix_cum": fix_cum, "fix_cum_rate": fix_cum_rate}).assign(trial_id=trial_id) \
        .set_index("trial_id", append=True).reorder_levels(["trial_id", "iteration"])
    lift_df = pd.concat([lift_df, df]) if lift_df is not None else df

del trial_df, fix, fix_cum, fix_cum_rate, df

# get the mean values per iteration over all trials
iter_df = lift_df.groupby("iteration").mean()

plt.figure(figsize=(9, 6))
sns.set_theme()

sns.lineplot(data=iter_df.reset_index(), x="iteration", y="fix", marker="o",
             label=r"$\bar{r}_k$ - mean per-Iteration Fix Rate")
sns.lineplot(data=iter_df.reset_index(), x="iteration", y="fix_cum_rate", linestyle="--",
             label=r"$\bar{R}_k$ - mean cumulative Fix Rate")

plt.yticks([.2, .3, .4, .5, .6, .7, .8, .9, 1])

plt.xlabel("Iteration $k$")
plt.ylabel(r"Fix Rates")
plt.legend()

plt.tight_layout()
plt.savefig(plots_path / "feedback_dist.svg")
