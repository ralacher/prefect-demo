# Demo workflow layout

Each workflow lives in its own numbered directory and can have its own local `uv` environment.

## Create or refresh the per-directory environments

From the repo root:

```powershell
Get-ChildItem .\scripts -Directory | ForEach-Object {
    Push-Location $_.FullName
    uv venv .venv
    uv pip install -r requirements.txt
    Pop-Location
}
```

## Run the local demo sequence

```powershell
uv run python scripts\run_demo.py
```

This is optional. It is only useful as a quick local smoke test that runs the
five workflow scripts sequentially without the Prefect server, deployments, or
worker.

The fifth workflow fails on purpose so the local demo shows a real error path.

## Deploy with Prefect + Docker worker

The repo now includes `prefect.yaml` at the repo root with one deployment per
numbered workflow folder. It expects these environment variables so the config
is not tied to one machine:

- `PREFECT_WORK_POOL_NAME` for the Docker work pool name
- `PREFECT_DOCKER_NETWORK` for the container network name
- `PREFECT_HOST_PROJECT_PATH` for the host path mounted into the container
- `PREFECT_CONTAINER_PROJECT_PATH` for the in-container mount target
- `PREFECT_CONTAINER_API_URL` for the API URL the run container can reach
    from inside the container; prefer a stable hostname like
    `host.containers.internal` over a bridge IP

`prefect.yaml` can reference environment variables with `{{ $VAR_NAME }}`, but
Prefect does not automatically load a `.env` file for you. Use `.env.example`
as a template and load those variables into your shell before running
`prefect deploy` or starting a worker.

Example values:

```powershell
$env:PREFECT_WORK_POOL_NAME='docker-demo-pool'
$env:PREFECT_DOCKER_NETWORK='podman'
$env:PREFECT_HOST_PROJECT_PATH='/mnt/c/path/to/your/repo'
$env:PREFECT_CONTAINER_PROJECT_PATH='/opt/prefect/project'
$env:PREFECT_CONTAINER_API_URL='http://host.containers.internal:4200/api'
```

If you keep the values in a local `.env` file, load them first in PowerShell:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^(?!#)([^=]+)=(.*)$') {
        [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

Deploy from the repo root:

```powershell
uv run prefect deploy --prefect-file prefect.yaml --all
```