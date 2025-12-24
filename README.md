# 🏗 LIFT - LLM-based Iterative Feedback-driven Test Suite Generation

## 💭 Model Selection

LIFT uses `litellm` to facilitate the flexible connection to different LLMs and LLM providers used for the different
agents.<br>
The following models are available for selection (as of Dec 24th, 2025):

| OpenAI Models                                                                                                                                                                                                                                                                                         | Anthropic Models                                                                                                                                                                     |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| gpt-3.5-turbo <br> gpt-4, gpt-4-turbo <br> gpt-4.1, gpt-4.1-mini, gpt-4.1-nano <br> gpt-5, gpt-5-pro, gpt-5-mini, gpt-5-nano, gpt-5-codex <br> gpt-5.1, gpt-5.1-codex, gpt-5.1-codex-max, gpt-5.1-codex-mini <br> gpt-5.2, gpt-5.2-pro <br> o1, o1-pro, o1-mini <br> o3, o3-pro, o3-mini <br> o4-mini | claude-sonnet-4-5 <br> claude-3-opus-latest, claude-3-5-sonnet-latest, claude-3-7-sonnet-latest <br> claude-opus-4-1, claude-opus-4-5 <br> claude-3-5-haiku-latest, claude-haiku-4-5 |

## 🐳 Docker Usage

In order to use LIFT containerized, either
<ol type="a">
  <li>download the latest docker image release here,</li>
  <li>get it from Docker Hub here or</li>
  <li>build it yourself.</li>
</ol>

In case, you want to build it yourself, use this command:
```bash
docker build -t lift-image .
```

To run LIFT on a PUT (Program Under Test) of your choosing, execute the following command (volumes are required!):
```bash
docker run \
    --name YOUR_CONTAINER_NAME \
    -v "YOUR_INPUT_DIR:/workspace/input" \
    -v "YOUR_ARCHIVE_DIR:/workspace/.archive" \
    lift-image
```
Use `--rm` to remove the container as soon as LIFT concludes execution.
Use `-d` to start the container detached.

Add `-v "YOUR_LOGS_DIR:/workspace/.logs"` to have the logs written outside the container.

Note: You need to link the two volumes to the `/workspace/input` (read-only) and `/workspace/.archive` (LIFT output).
The contents of the `/input` directory will not be changed. Examples for the `/input` files need can be found under [`📂 /input`](./input) The `/input` directory needs to adhere to this layout:<br>
```
input/
├── PUT_SOURCES               (source files of the PUT)
├── .env                      (environment variables)
├── generator.md              (TSG system prompt)
├── debugger.md               (TSD system prompt)
├── evaluator.md              (TSE system prompt)
├── evaluation_template.md    (TSE output template)
├── program-requirements.yml  (program requirements)
└── pytest_html_report.yml    (config file for pytest-html-report plugin)
```

The `/.archive` directory will contain all LIFT output artifacts. These are the FSS (First Sufficient Suite), LPS (Last Passing Suite), all intermediary suites and reports as well as a pickle export of the final states of each agent after completing its task.
The `/.archive` directory will have this layout (automatically created, needs to be empty on start-up):<br>

```
.archive/
├── archive_xx  (archive of the trial xx)
│   ├── logs/           (contains log files)
│   ├── conversations/  (contains the agents state exported after final message)
│   │
│   ├── _FSS_/  (data of the FSS - if available)
│   │   ├── tests/
│   │   ├── FSS_yy  (yy - iteration number)
│   │   ├── evaluation.md
│   │   ├── execution-report.xml
│   │   └── coverage-report.xml
│   │
│   ├── _LPS_/  (data of the LPS - if available)
│   │   ├── tests/
│   │   ├── LPS_yy  (yy - iteration number)
│   │   ├── evaluation.md
│   │   ├── execution-report.xml
│   │   └── coverage-report.xml
│   │
│   ├── tests_yy.zip  (yy - iteration number)
│   ├── ...
│   ├── reports_yy.zip  (yy - iteration number)
│   └── ...
│
└── ...
```

---

## 🔬 Analysis of LIFT output

In order to get the aggregated data of a number of LIFT trials (i.e. individual runs of LIFT on the same input data), first execute the [`📄 data_aggregation.py`](./analysis/data_aggregation.py).
It will generate a `trial_xx.csv` containing the test and coverage data over all iterations for a trial as well as a `fss_lps_all_trials.csv` containing the FSS and LPS data for all trials in your `<<DATA_OUTPUT_PATH>>`.


### Test Counts $t$

Plots generated by [`📄 counts_agg.py`](./analysis/plotting/counts_agg.py)<br>
Latex Table generated by [`📄 counts.py`](./analysis/table_data/counts.py)


### Test Types

Latex Table generated by [`📄 types_.py`](./analysis/table_data/types_.py)


### Line Coverage $l$ and Branch Coverage $b$

Plots generated by [`📄 line_cov_agg.py`](./analysis/plotting/line_cov_agg.py) and [`📄 branch_cov_agg.py`](./analysis/plotting/branch_cov_agg.py)<br>
Latex Tables generated by [`📄 coverages.py`](./analysis/table_data/coverages.py)


### Mean Fix Rates - $\bar{r}$ and $\bar{R}$

Plots generated by [`📄 feedback_distribution.py`](./analysis/plotting/feedback_distribution.py)

| Mean per-Iteration Fix Rate at Iteration $k$                                                                                                                  | Mean cumulative Fix Rate at Iteration $k$                                                                                                                                                |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| <p align="center"><img src="https://math.vercel.app/?from=\bar{r}_k = \frac{1}{m} \sum_{j=1}^{m} r_{k}^{(j)} = \frac{1}{m} \sum_{j=1}^{m} x_{k}^{(j)}" /></p> | <p align="center"><img src="https://math.vercel.app/?from=\bar{R}_k = \frac{1}{m} \sum_{j=1}^{m} R_{k}^{(j)} = \frac{1}{m} \sum_{j=1}^{m} \frac{1}{k} \sum_{i=1}^{k} x_{i}^{(j)}" /></p> |
| <p align="center"><img src="https://math.vercel.app/?from=r_{k}^{(j)} = x_{k}^{(j)}" /></p>                                                                   | <p align="center"><img src="https://math.vercel.app/?from=R_{k}^{(j)} = \frac{1}{k} \sum_{i=1}^{k} x_{i}^{(j)}" /></p>                                                                   |
| where: <br> $x_{k}^{(j)} \in \{0,1\}$ : binary indicator for a Fix feedback (TSD) at Iteration $k$ in Trial $j$ <br> $m$ : total number of Trials             | where: <br> $x_{k}^{(j)} \in \{0,1\}$ : binary indicator for a Fix feedback (TSD) at Iteration $k$ in Trial $j$ <br> $m$ : total number of Trials                                        |

Note that $r_k = x_k$ since the Fix Rate for a trial at Iteration $k$ is just the binary information whether a bug fixing is applied (TSD) or test suite evaluation is done (TSE).
The cumulative Fix Rate represents the ratio of past Iterations (incl. $k$) devoted to bug fixing.<br>
A $R_k > 0.5$ represents more iterations spent on bug fixing than test suite improvements.
$R_k = 0.5$ means that the equal counts of Iterations were spent on bug fixing as on improvements.
