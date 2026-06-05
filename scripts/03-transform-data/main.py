from prefect import flow, task


@task
def transform_payload(payload: str) -> str:
    return payload.upper()


@flow(name="03-transform-data")
def transform_data() -> str:
    transformed = transform_payload("customer payload transformed")
    print(f"03-transform-data: {transformed}")
    return transformed


if __name__ == "__main__":
    transform_data()