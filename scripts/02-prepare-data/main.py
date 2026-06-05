from prefect import flow, task


@task
def prepare_payload() -> str:
    return "customer payload prepared"


@flow(name="02-prepare-data")
def prepare_data() -> str:
    payload = prepare_payload()
    print(f"02-prepare-data: {payload}")
    return payload


if __name__ == "__main__":
    prepare_data()