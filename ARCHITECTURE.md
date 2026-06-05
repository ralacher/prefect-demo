# Architecture Overview

This repo demonstrates a scalable, portable workflow orchestration system designed to support many teams with different dependencies.

## Components

1. **Flow Scripts** (`scripts/NN-*/main.py`)
   - Independent Python modules, each with a `@flow` function
   - Each can have its own `requirements.txt` for dependencies
   - No hardcoded paths or environment-specific code

2. **Prefect Deployments** (`prefect.yaml`)
   - Single file defining all 5 deployments
   - Uses environment variable substitution (`{{ $VAR_NAME }}`) for portability
   - Pull step clones code from GitHub instead of using local mounts
   - Work pool references custom Docker image with all dependencies preinstalled

3. **Custom Runtime Image** (`Dockerfile.runtime` + GitHub Actions CI/CD)
   - Built from `prefecthq/prefect:3-python3.12`
   - Aggregates all `scripts/*/requirements.txt` into one image
   - Deduplicated dependencies across all scripts
   - Published to GHCR with tags (`latest`, `sha-<commit>`)

4. **Prefect Server**
   - Orchestration backend running locally or remotely
   - Stores deployment definitions, flow runs, logs
   - API reachable from worker and client terminals

5. **Docker Worker Pool**
   - Pulls jobs from Prefect queue
   - Spawns ephemeral containers per run
   - Containers pull code from GitHub, execute flow, then terminate

## Data Flow for a Flow Run

1. User triggers deployment via UI or CLI
2. Prefect server queues the job
3. Docker worker polls and picks up job
4. Worker spawns container from `PREFECT_RUNTIME_IMAGE`
5. Container's pull step clones repo from GitHub main branch
6. Flow imported and executed
7. Logs streamed to Prefect UI in real-time
8. Container exits; worker ready for next job

## Portability & Multi-Team Design

- **No hardcoded paths**: All config driven by environment variables
- **No local volume mounts**: Code sourced from GitHub, not local filesystem
- **Dependency isolation per image**: Each team/profile can build custom images with their dependencies
- **Ephemeral workers**: No lingering state between runs; clean slate every time
- **CI/CD driven**: Changes to `prefect.yaml` or new dependencies trigger automated image builds

## Directory Structure

```
loudoun-prefect-demo/
├── prefect.yaml                          # Deployment definitions (5 flows + work pool config)
├── Dockerfile.runtime                    # Custom image with consolidated script requirements
├── .env.example                          # Environment variable template (portable across machines)
├── .env                                  # Local env vars (not in git, copy from .example)
├── README.md                             # Quick start & operational guide
├── ARCHITECTURE.md                       # This file
├── .github/
│   └── workflows/
│       └── runtime-image.yml             # CI/CD: CodeQL scan, image build & test, GHCR publish
├── .gitignore                            # Git ignore patterns (Python, __pycache__, .env, etc.)
├── .dockerignore                         # Docker build context filter
└── scripts/
    ├── 01-my-flow/
    │   ├── main.py                       # Flow function: flow_func()
    │   └── requirements.txt               # Dependencies: prefect>=3.0.0
    ├── 02-prepare-data/
    │   ├── main.py
    │   └── requirements.txt
    ├── 03-transform-data/
    │   ├── main.py
    │   └── requirements.txt
    ├── 04-publish-summary/
    │   ├── main.py
    │   └── requirements.txt
    └── 05-fail-demo/
        ├── main.py                       # Intentionally fails for testing error paths
        └── requirements.txt
```

## Adding a New Flow Script

To add a new script (e.g., `06-new-script`):

1. **Create the script structure:**
   ```bash
   mkdir -p scripts/06-new-script
   touch scripts/06-new-script/main.py
   echo "prefect>=3.0.0" > scripts/06-new-script/requirements.txt
   ```

2. **Add the flow function:**
   ```python
   from prefect import flow
   
   @flow
   def flow_func():
       print("New flow execution")
   ```

3. **Add deployment to `prefect.yaml`:**
   - Copy an existing deployment block
   - Update `name:`, `entrypoint:` to `scripts/06-new-script/main.py:flow_func`
   - Push to GitHub

4. **GitHub Actions will:**
   - Detect new `requirements.txt`
   - Build new image with consolidated deps (including from script 06)
   - Publish image with new tags
   - You redeploy with new image tag

## Key Design Decisions

### Why separate requirements per script?
- Different teams may have different dependencies
- Easier to track what each flow needs
- Deduplication happens at image-build time

### Why git_clone instead of local volumes?
- Works in CI/CD without host filesystem knowledge
- Developers can work on any branch, any machine
- Container always gets code from specified GitHub ref
- No path coupling between host and container

### Why environment variables in prefect.yaml?
- Same YAML works across dev, test, prod
- Developers load `.env.example`, customize, commit nothing
- Server/worker IP changes don't require file edits
- Docker network and container API URL abstracted

### Why ephemeral containers?
- No leftover state between runs
- Clean environment every execution
- Resource cleanup automatic
- Scaling: many concurrent runs without resource leaks

### Why GHCR instead of local image registry?
- Works across any machine/network
- GitHub Actions push natively
- No separate registry infrastructure to manage
- Image pulls work in CI and locally

## Scaling Considerations

**For 60+ scripts across multiple teams:**

1. **Separate images per dependency profile:**
   - `prefect-demo-runtime:data-team` (pandas, dask, polars)
   - `prefect-demo-runtime:ml-team` (tensorflow, sklearn, ray)
   - `prefect-demo-runtime:web-team` (requests, beautifulsoup, selenium)
   - Each team maintains their own Dockerfile.runtime variant

2. **Multiple work pools per team:**
   - Each team's scripts use their team's work pool
   - Work pool points to their custom image
   - Prevents dependency conflicts

3. **GitHub Environments for promotions:**
   - Dev branch → builds test images (no publish)
   - Main branch → builds & publishes prod images
   - Production deployments use different image tags

4. **Centralized Prefect server:**
   - Single server for all teams & scripts
   - Teams create their own deployments in dedicated directories
   - Audit trail of all runs across org

## Monitoring & Observability

- **Prefect UI**: http://127.0.0.1:4200 — deployment status, run logs, flow history
- **GitHub Actions**: Actions tab — CI/CD build logs, image tag history
- **GHCR**: Packages tab — all published image tags & digests
- **Flow logs**: Real-time streaming to Prefect UI during execution
