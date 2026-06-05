# Troubleshooting Guide

## Server & Infrastructure Issues

### Server won't start on Windows
```powershell
# Check if port 4200 is already in use
netstat -ano | findstr :4200

# If in use, kill the process:
taskkill /PID <PID> /F

# Or use a different port and update PREFECT_API_URL in .env:
uv run prefect server start --host 0.0.0.0 --port 4201
```

### Worker fails to connect to server
```powershell
# Verify server is running and accessible
curl http://127.0.0.1:4200/api/health
# Expected: 200 OK response

# Check PREFECT_API_URL is set correctly
Write-Host $env:PREFECT_API_URL

# Worker needs visibility to server API; if running locally, ensure firewall allows port 4200
```

### Docker/Podman connection fails
```powershell
# Verify Docker/Podman is running
podman ps  # or: docker ps

# For Windows Podman, ensure DOCKER_HOST is set to the correct pipe
$env:DOCKER_HOST='npipe:////./pipe/docker_engine'

# Test connection:
podman info
```

## Deployment & Flow Run Issues

### Deployment command fails: "API not available"
```
Error: Failed to connect to Prefect server at http://127.0.0.1:4200/api
```

**Cause:** Prefect server not running or unreachable.

**Fix:**
1. Verify server is running in Terminal 1: `uv run prefect server start`
2. Verify PREFECT_API_URL points to correct address: `Write-Host $env:PREFECT_API_URL`
3. If server is on different machine, update PREFECT_API_URL to its IP/hostname

### Flow run fails with "image not found"
```
Error: pulling image ghcr.io/ralacher/prefect-demo-runtime:sha-e68550b
```

**Cause:** Docker image doesn't exist, isn't published, or isn't accessible.

**Fix:**
```powershell
# Verify image exists at GHCR
Write-Host $env:PREFECT_RUNTIME_IMAGE

# Try pulling image manually
podman pull $env:PREFECT_RUNTIME_IMAGE

# If pull fails, check:
# 1. Image tag is correct (visit https://github.com/ralacher/prefect-demo/pkgs/container/prefect-demo-runtime)
# 2. Image is public, or you have GHCR credentials configured
# 3. Network can reach ghcr.io
```

### "git_clone" pull step fails in container

Error logs show clone failure during flow execution.

**Cause:** Container can't reach GitHub or repo is private/incorrect.

**Fix:**
```powershell
# Verify repository URL is correct and public
Write-Host $env:PREFECT_SOURCE_REPOSITORY

# Verify branch exists
git ls-remote $env:PREFECT_SOURCE_REPOSITORY $env:PREFECT_SOURCE_BRANCH

# Test clone manually in container
podman run --rm $env:PREFECT_RUNTIME_IMAGE git clone -b $env:PREFECT_SOURCE_BRANCH $env:PREFECT_SOURCE_REPOSITORY /tmp/test-clone
```

### Flow import fails: "No module named 'scripts.NN.main'"

**Cause:** Flow script or module structure is incorrect, or dependencies are missing from image.

**Fix:**
1. Verify script has correct structure: `scripts/NN-name/main.py` with `@flow def flow_func():`
2. Check `requirements.txt` has all dependencies
3. Rebuild image and redeploy:
   ```powershell
   # Push changes to main, wait for GitHub Actions
   # Then:
   Get-Content .env | ForEach-Object { ... }  # Load env vars
   uv run prefect deploy --all --no-prompt
   ```

### Work pool creation fails: "Already exists"
```
Error: Work pool 'docker-demo-pool' already exists
```

**Fix:** Only run `uv run prefect work-pool create ...` once. After that, skip to starting worker.

### Environment variables not applied to container

Flow runs but sees wrong values in logs (e.g., missing dependencies).

**Cause:** Environment variables passed to Prefect aren't propagated to container, or wrong image used.

**Fix:**
```powershell
# Verify deployment definition includes correct image and variables:
uv run prefect deployment inspect 'flow-01/deploy-01'
# Should show: image: ghcr.io/ralacher/prefect-demo-runtime:sha-abc1234

# If wrong, redeploy after updating .env:
Get-Content .env | ForEach-Object { ... }  # Load fresh env vars
uv run prefect deploy --all --no-prompt
```

## GitHub Actions CI/CD Issues

### Workflow fails at CodeQL step
```
CodeQL analysis returned findings with severity HIGH or CRITICAL
```

**Fix:**
- Visit Actions > latest run > CodeQL tab
- Review flagged vulnerabilities
- Fix issues in source code
- Push and re-trigger workflow

### Image build fails: "Invalid requirement"
```
ERROR: Invalid requirement: 'prefect>=3.0.0prefect>=3.0.0prefect>=3.0.0'
```

**Cause:** `Dockerfile.runtime` requirements concatenation isn't preserving newlines.

**Fix:**
- Check `Dockerfile.runtime` RUN command uses proper newline handling
- Current (fixed) version uses: `find ... | while read f; do cat "$f"; echo; done | ...`
- Rebuild and redeploy

### Smoke test fails: "script XX failed"
```
FAILED: scripts/02-prepare-data/main.py
```

**Cause:** Script can't be imported or dependency is missing.

**Fix:**
1. Verify `scripts/02-prepare-data/main.py` has valid Python syntax
2. Verify `requirements.txt` lists all imports
3. Test locally: `python scripts/02-prepare-data/main.py`
4. Fix and push to main

### publish-image job fails
```
Error: denied: permission denied
```

**Cause:** GitHub token doesn't have permission to push to GHCR.

**Fix:**
- Usually automatic for repo owned by user
- Check GHCR visibility: https://github.com/ralacher/prefect-demo/settings/packages
- Ensure package visibility is at least "Internal"

## Debugging

### See detailed flow run logs
```powershell
# In Prefect UI:
# 1. Click Deployments > select deployment > Run
# 2. Watch logs in real-time

# Or via CLI:
uv run prefect deployment run 'flow-01/deploy-01'
# Logs stream to terminal
```

### Inspect deployment definition
```powershell
# See full deployment YAML as registered:
uv run prefect deployment inspect 'flow-01/deploy-01'

# See all deployments:
uv run prefect deployment ls
```

### Debug container manually
```powershell
# Spawn container and debug interactively:
podman run -it --rm \
  -e PREFECT_API_URL=$env:PREFECT_API_URL \
  -e PREFECT_SOURCE_REPOSITORY=$env:PREFECT_SOURCE_REPOSITORY \
  -e PREFECT_SOURCE_BRANCH=$env:PREFECT_SOURCE_BRANCH \
  $env:PREFECT_RUNTIME_IMAGE /bin/bash

# Inside container, manually run git_clone:
git clone -b main https://github.com/ralacher/prefect-demo.git /tmp/code
cd /tmp/code
python -c "from scripts.01_my_flow.main import flow_func; flow_func()"
```

### Check environment variables are loaded
```powershell
# List all loaded Prefect env vars:
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
    if ($val) {
        Write-Host "✓ $_=$val"
    } else {
        Write-Host "✗ $_ NOT SET"
    }
}
```

### Verify YAML syntax
```powershell
# Check prefect.yaml:
uv run python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('prefect.yaml').read_text()); print('✓ prefect.yaml OK')"

# Check GitHub Actions workflow:
uv run python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/runtime-image.yml').read_text()); print('✓ runtime-image.yml OK')"
```

## Getting Help

1. **Check Prefect logs:** `~/.prefect/prefect.log` (on Windows: `$env:APPDATA\Prefect`)
2. **Flow run logs:** Prefect UI or `uv run prefect flow-run logs <run-id>`
3. **GitHub Actions logs:** https://github.com/ralacher/prefect-demo/actions
4. **Docker/Podman logs:** `podman logs <container-id>`
5. **Prefect documentation:** https://docs.prefect.io/
