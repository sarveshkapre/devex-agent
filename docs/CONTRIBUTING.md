# CONTRIBUTING

Thanks for contributing!

## Basics
- Fork and create a feature branch.
- Run `make check` before opening a PR.
- Keep PRs small and focused.

## Code style
- Python 3.11
- Ruff for lint/format
- Mypy for type checking

## GitHub Actions (Self-hosted Runner)
This repository's CI workflow runs on `runs-on: self-hosted` for all jobs.

### Runner platform requirements
- Supported OS: Linux or macOS (`bash` required).
- Required tools on runner host: `git`, `bash`, `curl`, `tar`, `make`.
- Network access required to:
  - `github.com` (checkout + runner communication + gitleaks download)
  - `pypi.org` and `files.pythonhosted.org` (Python dependencies)
  - `api.osv.dev` (used by `pip-audit`)
- Docker is not required for this workflow.

### Register a runner for this repository
1. Open repository Settings → Actions → Runners.
2. Click `New self-hosted runner`.
3. Choose Linux or macOS.
4. On the runner machine, run the exact download/configure commands shown by GitHub for this repo.
5. Start the runner:
   - foreground: `./run.sh`
   - service (recommended): `sudo ./svc.sh install && sudo ./svc.sh start`
6. Return to Settings → Actions → Runners and confirm status is `Idle`.

### Important scheduling note
- Jobs use `runs-on: self-hosted` without additional labels.
- Keep at least one compatible Linux/macOS runner online for this repository.

### Local end-to-end CI validation
Run these from the repository root on the runner host:

```bash
# Build job (runner-like environment)
tmp_venv="$(mktemp -d /tmp/devex-selfhost-ci-venv.XXXXXX)"
python3 -m venv "$tmp_venv"
source "$tmp_venv/bin/activate"
python -m pip install -U pip
pip install -e '.[dev]'
PATH="$tmp_venv/bin:$PATH" make check VENV=.missing
pip install pip-audit
pip-audit

# Secrets job (same logic as workflow)
RUNNER_TEMP="$(mktemp -d /tmp/devex-selfhost-runner-temp.XXXXXX)"
version="8.24.2"
os="$(uname -s)"; arch="$(uname -m)"
case "${os}/${arch}" in
  Linux/x86_64) asset="gitleaks_${version}_linux_x64.tar.gz" ;;
  Linux/aarch64|Linux/arm64) asset="gitleaks_${version}_linux_arm64.tar.gz" ;;
  Darwin/x86_64) asset="gitleaks_${version}_darwin_x64.tar.gz" ;;
  Darwin/arm64) asset="gitleaks_${version}_darwin_arm64.tar.gz" ;;
  *) echo "Unsupported runner platform: ${os}/${arch}"; exit 1 ;;
esac
mkdir -p "$RUNNER_TEMP/gitleaks-bin"
curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/v${version}/${asset}" -o "$RUNNER_TEMP/gitleaks.tgz"
tar -xzf "$RUNNER_TEMP/gitleaks.tgz" -C "$RUNNER_TEMP/gitleaks-bin"
"$RUNNER_TEMP/gitleaks-bin/gitleaks" git --redact --verbose .
```
