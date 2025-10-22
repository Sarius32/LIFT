# 🏗 LIFT - LLM-based Iterative Feedback-driven Test Suite Generation

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

Add `-v "YOUR_LOGS_DIR:/workspace/logs"` to have the logs written outside the container.


Note: You need to link the two volumes to the `/workspace/input` (read-only) and `/workspace/.archive` (LIFT output).
The contents of the `/input` directory will not be changed. The `/input` directory needs to adhere to this layout:
...

The `/.archive` directory will contain all LIFT output artifacts. These are the FSS (First Sufficient Suite), LPS (Last Passing Suite), all intermediary suites and reports as well as a pickle export of the final states of each agent after completing its task.
The `/.archive` directory wil have this layout (automatically created, needs to be empty on start-up):
...

