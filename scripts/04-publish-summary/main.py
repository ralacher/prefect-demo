from prefect import flow, task


@task
def build_summary() -> str:
    return "summary published to downstream system"


@flow(name="04-publish-summary")
def publish_summary() -> str:
    summary = build_summary()
    print(f"04-publish-summary: {summary}")
    return summary


if __name__ == "__main__":
    publish_summary()