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
- `PREFECT_RUNTIME_IMAGE` for the runtime image tag used by deployments
- `PREFECT_DOCKER_NETWORK` for the container network name
- `PREFECT_CONTAINER_API_URL` for the API URL the run container can reach
    from inside the container; prefer a stable hostname like
    `host.containers.internal` over a bridge IP
- `PREFECT_SOURCE_REPOSITORY` for the Git repo Prefect should clone at runtime
- `PREFECT_SOURCE_BRANCH` for the branch to run from (for example, `main`)

`prefect.yaml` can reference environment variables with `{{ $VAR_NAME }}`, but
Prefect does not automatically load a `.env` file for you. Use `.env.example`
as a template and load those variables into your shell before running
`prefect deploy` or starting a worker.

Example values:

```powershell
$env:PREFECT_WORK_POOL_NAME='docker-demo-pool'
$env:PREFECT_RUNTIME_IMAGE='ghcr.io/ralacher/prefect-demo-runtime:latest'
$env:PREFECT_DOCKER_NETWORK='podman'
$env:PREFECT_CONTAINER_API_URL='http://host.containers.internal:4200/api'
$env:PREFECT_SOURCE_REPOSITORY='https://github.com/ralacher/prefect-demo.git'
$env:PREFECT_SOURCE_BRANCH='main'
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

## Runtime image CI/CD

The workflow at `.github/workflows/runtime-image.yml` does the following on
pushes to `main` (or manual dispatch):

1. Runs a CodeQL scan (GitHub Advanced Security).
2. Builds `Dockerfile.runtime` from `prefecthq/prefect:3-python3.12` and installs requirements.
3. Runs script smoke tests in the built container (`01-04` must pass, `05` must fail).
4. Publishes tags to GHCR (`latest` on default branch plus a short SHA tag).

Use the published tag by setting `PREFECT_RUNTIME_IMAGE` before running
`prefect deploy`.