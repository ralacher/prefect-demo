from prefect import flow, task


@task
def trigger_failure() -> None:
    raise RuntimeError("Intentional failure for the demo")


@flow(name="05-fail-demo")
def fail_demo() -> None:
    print("05-fail-demo: starting")
    trigger_failure()


if __name__ == "__main__":
    fail_demo()