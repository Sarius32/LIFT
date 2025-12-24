from pathlib import Path


class Paths:
    def __init__(self, root: Path, inputs: Path, put_name: str) -> None:
        self.root = root.resolve()
        self.config = self.root.joinpath("config").resolve()

        self.inputs = inputs.resolve()
        self.req_doc = self.inputs.joinpath("program-requirements.yml").resolve()
        self.eval_template = self.inputs.joinpath("evaluation_template.md").resolve()
        self.html_template = self.inputs.joinpath("pytest_html_report.yml").resolve()

        self.archive = self.root.joinpath(".archive").resolve()
        self.conversation_archive = self.archive.joinpath("conversations").resolve()

        self.project = self.root.joinpath("project").resolve()
        self.put = self.project.joinpath(put_name).resolve()
        self.tests = self.project.joinpath("tests").resolve()
        self.reports = self.project.joinpath("reports").resolve()
