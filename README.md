# Prefect Demo: Scalable Workflow Orchestration

This repo demonstrates a production-grade workflow orchestration system using Prefect 3, Docker/Podman, and GitHub Actions CI/CD. It's designed to support 60+ scripts across multiple teams with conflicting dependencies.

## 📚 Documentation

- **[README.md](README.md)** ← **START HERE**: Quick start guide, local setup, deployment steps
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Design decisions, component overview, scaling for 60+ scripts
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)**: Debug common issues, error messages, solutions

## Quick Start (TL;DR)

```powershell
# 1. Copy environment variables template
cp .env.example .env

# 2. Load them in PowerShell (copy-paste from .env file)
# 3. Three terminals:

# Terminal 1: Start server
uv run prefect server start --host 0.0.0.0 --port 4200

# Terminal 2: Create work pool & start worker
uv run prefect work-pool create --type docker docker-demo-pool
uv run prefect worker start --pool docker-demo-pool

# Terminal 3: Deploy flows
uv run prefect deploy --all --no-prompt

# 4. Open http://127.0.0.1:4200 and trigger a deployment
```

For detailed instructions, see the [Local Development & Deployment](#local-development--deployment) section below.

---

## Demo workflow layout

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

## Local Development & Deployment

### Prerequisites

1. **Docker/Podman**: Ensure Docker or Podman is running. On Windows with Podman, set:
   ```powershell
   $env:DOCKER_HOST='npipe:////./pipe/docker_engine'
   ```

2. **Environment Variables**: The repo requires environment variables for portability. Copy `.env.example` to `.env` and update values as needed:
   ```powershell
   cp .env.example .env
   ```

### Environment Variables

Required variables (referenced in `prefect.yaml` with `{{ $VAR_NAME }}`):

| Variable | Purpose | Example |
|----------|---------|---------|
| `PREFECT_API_URL` | Prefect server URL for this machine | `http://127.0.0.1:4200/api` |
| `PREFECT_WORK_POOL_NAME` | Docker work pool name | `docker-demo-pool` |
| `PREFECT_RUNTIME_IMAGE` | Custom Docker image with script dependencies | `ghcr.io/ralacher/prefect-demo-runtime:sha-abc1234` |
| `PREFECT_DOCKER_NETWORK` | Container network name | `podman` |
| `PREFECT_CONTAINER_API_URL` | API URL reachable **from inside** container | `http://host.containers.internal:4200/api` |
| `PREFECT_SOURCE_REPOSITORY` | Git repo URL for `git_clone` pull step | `https://github.com/ralacher/prefect-demo.git` |
| `PREFECT_SOURCE_BRANCH` | Git branch to deploy from | `main` |

### Load Environment Variables in PowerShell

Before running any Prefect commands, load the `.env` file into your current session:

**Option 1: Load from traditional .env file (KEY=VALUE format):**

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($varName, $varValue)
    }
}

# Verify:
Write-Host "PREFECT_WORK_POOL_NAME=$env:PREFECT_WORK_POOL_NAME"
Write-Host "PREFECT_RUNTIME_IMAGE=$env:PREFECT_RUNTIME_IMAGE"
```

**Option 2: Copy and paste directly into PowerShell:**

You can also copy all lines from `.env` (or your customized `.env` file) and paste them directly into the PowerShell terminal. The shell will execute each `KEY=VALUE` assignment.

**Verify all variables are loaded:**

```powershell
@(
    'PREFECT_API_URL',
    'PREFECT_WORK_POOL_NAME',
    'PREFECT_RUNTIME_IMAGE',
    'PREFECT_DOCKER_NETWORK',
    'PREFECT_CONTAINER_API_URL',
    'PREFECT_SOURCE_REPOSITORY',
    'PREFECT_SOURCE_BRANCH',
    'DOCKER_HOST'
) | ForEach-Object {
    $val = [System.Environment]::GetEnvironmentVariable($_)
    Write-Host "$_=$val"
}
```

### Start Prefect Server

In one terminal, start the Prefect server (stays running; no `--detach` on Windows):

```powershell
# Load env vars (if not already done)
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($varName, $varValue)
    }
}

# Start server
uv run prefect server start --host 0.0.0.0 --port 4200
```

Server will be available at `http://127.0.0.1:4200/`.

**Note:** The server must be running for `prefect deploy` to work in another terminal.

### Create Work Pool & Start Worker

In a **second** terminal, create the work pool and start the worker:

```powershell
# Load env vars
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($varName, $varValue)
    }
}

# Create work pool (one-time setup)
uv run prefect work-pool create --type docker $env:PREFECT_WORK_POOL_NAME

# Start worker (stays running)
uv run prefect worker start --pool $env:PREFECT_WORK_POOL_NAME
```

The worker will poll the Prefect server for jobs and execute them in Docker/Podman containers.

### Deploy Flows to Prefect

In a **third** terminal, deploy the flow definitions:

```powershell
# Load env vars
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $varName = $matches[1].Trim()
        $varValue = $matches[2].Trim()
        [System.Environment]::SetEnvironmentVariable($varName, $varValue)
    }
}

# Deploy all flows defined in prefect.yaml
uv run prefect deploy --prefect-file prefect.yaml --all --no-prompt
```

**Important:** The Prefect server must be running (from Terminal 1) for this to succeed.

Expected output:
```
...
Deployment 'flow-01/deploy-01' provided 'docker-demo-pool' work pool with properties:
        image: ghcr.io/ralacher/prefect-demo-runtime:sha-abc1234
        ...
Successfully created/updated all deployments!
```

This registers all flow definitions in `prefect.yaml` with the Prefect backend. Each deployment specifies the Docker image, entrypoint, pull steps (git_clone), and environment variables.

### Run a Flow

Via the Prefect UI (`http://127.0.0.1:4200`):
1. Click **Deployments** > select any deployment > **Run**
2. Watch the run status and logs in real-time

Or via CLI:
```powershell
uv run prefect deployment run 'flow-01/deploy-01'
```

### Update & Redeploy

To update a deployment (e.g., change the runtime image, update a flow, or change environment variables):

1. **No need to stop server or worker** — they remain running
2. Update your `.env` with the new `PREFECT_RUNTIME_IMAGE` tag (after CI/CD publishes)
3. Reload env vars in your terminal
4. Run `uv run prefect deploy --all --no-prompt` again
5. Next flow run will use the updated deployment definition

## Runtime Image CI/CD Pipeline

### Workflow Overview

The GitHub Actions workflow at `.github/workflows/runtime-image.yml` automates building and publishing Docker images with consolidated script dependencies. It runs on:
- Every push to `main`
- Manual dispatch from GitHub Actions UI

### Workflow Jobs

**1. CodeQL Security Scan**
    - Scans Python code for security vulnerabilities
    - Runs on every push
    - Results visible in repository's **Security** tab

**2. Build & Test Image (test-image job)**
    - Builds `Dockerfile.runtime` from `prefecthq/prefect:3-python3.12` base
    - Copies all `scripts/*/requirements.txt` files and deduplicates them
    - Installs consolidated dependencies into image
    - Smoke tests: scripts `01-04` must succeed, script `05` must fail (intentional error)
    - Only proceeds to publish if all tests pass

**3. Publish to GHCR**
    - Publishes image to GitHub Container Registry (`ghcr.io`)
    - Tags: 
      - `latest` (on `main` branch)
      - `sha-<short-commit-hash>` (always)
    - Example: `ghcr.io/ralacher/prefect-demo-runtime:sha-e68550b`

### Using Published Images

1. **Check GHCR for available tags:**
    - Visit: https://github.com/ralacher/prefect-demo/pkgs/container/prefect-demo-runtime
    - Or run: `podman pull ghcr.io/ralacher/prefect-demo-runtime:latest --dry-run`

2. **Update PREFECT_RUNTIME_IMAGE in `.env`:**
    ```powershell
    $env:PREFECT_RUNTIME_IMAGE='ghcr.io/ralacher/prefect-demo-runtime:sha-e68550b'
    ```

3. **Redeploy with new image:**
    ```powershell
    # Reload env vars in your terminal
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $varName = $matches[1].Trim()
            $varValue = $matches[2].Trim()
            [System.Environment]::SetEnvironmentVariable($varName, $varValue)
        }
    }

    # Redeploy (server and worker stay running)
    uv run prefect deploy --all --no-prompt
    ```

4. **Next flow run uses the new image** — no restart needed

### Monitoring Workflow Status

- Visit: https://github.com/ralacher/prefect-demo/actions
- Click **runtime-image** workflow > latest run
- Check job logs under each job tab

### Troubleshooting Failed Builds

**CodeQL fails:**
- Check the security scan results in the workflow run
- Address any flagged vulnerabilities in source code

**test-image fails:**
- Check the build log for Docker errors
- Verify `Dockerfile.runtime` syntax
- Ensure script requirements.txt files are valid
- Check that smoke test scripts (01-05) can be imported from the image

**publish-image fails:**
- Ensure GitHub token has permission to push to GHCR (usually automatic)
- Verify GHCR visibility settings

### Adding New Script Dependencies

When a new script folder is added:

1. Create `scripts/NN-*/requirements.txt` with dependencies
2. Push to `main` or trigger workflow manually
3. GitHub Actions automatically includes new requirements in next image build
4. New image is published with updated requirements
5. Update `PREFECT_RUNTIME_IMAGE` in `.env` and redeploy