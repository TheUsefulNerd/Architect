# Poetry Setup Guide (Windows)

Poetry is Python's modern dependency manager — like npm but for Python.

---

## Installation

**PowerShell (recommended):**
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

**Add to PATH permanently:**
1. Win + X → System → Advanced system settings → Environment Variables
2. Under User variables → Path → Edit → New
3. Add: `C:\Users\YourUsername\AppData\Roaming\Python\Scripts`
4. Restart your terminal

**Verify:**
```bash
poetry --version
```

---

## Project Setup

```bash
cd backend
poetry install       # installs all deps, creates venv, reads pyproject.toml
```

---

## Daily Commands

```bash
# Run a command inside the venv (no activation needed)
poetry run uvicorn app.main:app --reload

# Or activate the shell first
poetry shell
uvicorn app.main:app --reload

# Add a new package
poetry add package-name

# Regenerate poetry.lock (after deleting it or changing pyproject.toml)
poetry lock

# Install after lock regeneration
poetry install
```

---

## Important Notes for Architect

- **Python must be 3.11** — grpcio-tools is incompatible with 3.12+. Check with `python --version`
- **Never use `poetry pip`** — the `pip` subcommand was removed in Poetry 2.x. Use `pip install` or `poetry add` instead
- **After changing `pyproject.toml`**, always run `poetry lock` then `poetry install`
- **Commit `poetry.lock`** to git — this ensures everyone gets identical dependency versions

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `poetry: command not found` | Restart terminal, verify PATH includes `AppData\Roaming\Python\Scripts` |
| `No module named X` | Run `poetry install` — venv is out of sync |
| Wrong Python version | Install Python 3.11 and run `poetry env use python3.11` |
| `poetry.lock` deleted | Run `poetry lock` to regenerate |

---

## Quick Reference

| Command | What it does |
|---|---|
| `poetry install` | Install all dependencies |
| `poetry shell` | Activate virtual environment |
| `poetry add pkg` | Add a package |
| `poetry remove pkg` | Remove a package |
| `poetry lock` | Regenerate lock file |
| `poetry run cmd` | Run command in venv without activating |
| `poetry show` | List installed packages |