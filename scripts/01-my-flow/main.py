from prefect import flow, task


@task
def compose_message() -> str:
    return "01-my-flow says hello from its own directory"


@flow(name="01-my-flow")
def my_flow() -> str:
    message = compose_message()
    print(message)
    return message


if __name__ == "__main__":
    my_flow()