from pathlib import Path
import subprocess

from prefect import flow, task


WORKFLOW_DIRECTORIES = [
    Path(__file__).parent / "01-my-flow",
    Path(__file__).parent / "02-prepare-data",
    Path(__file__).parent / "03-transform-data",
    Path(__file__).parent / "04-publish-summary",
    Path(__file__).parent / "05-fail-demo",
]


@task(name="run-workflow-script")
def run_workflow_script(workflow_directory: Path) -> None:
    subprocess.run(["uv", "run", "python", "main.py"], cwd=workflow_directory, check=True)


@flow(name="demo-sequence")
def demo_sequence() -> None:
    for workflow_directory in WORKFLOW_DIRECTORIES:
        run_workflow_script(workflow_directory)


if __name__ == "__main__":
    demo_sequence()