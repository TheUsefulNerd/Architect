# Poetry Setup Guide (Windows)

Poetry is a modern dependency management tool for Python. It's like npm for Node.js, but better!

## Why Poetry?

- **Simple dependency management**: No more `requirements.txt` confusion
- **Virtual environment handling**: Automatically creates and manages venvs
- **Lock files**: Ensures everyone has the same versions (`poetry.lock`)
- **Easy to use**: Simple commands for everything

## Installation

### Method 1: PowerShell (Recommended)

Open PowerShell and run:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Method 2: Using pip (Alternative)

```bash
pip install poetry
```

## Add Poetry to PATH

After installation, you need to add Poetry to your PATH:

### Temporary (Current Session Only):
```powershell
$env:Path += ";$env:APPDATA\Python\Scripts"
```

### Permanent:
1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", find "Path"
5. Click "Edit"
6. Click "New"
7. Add: `C:\Users\YourUsername\AppData\Roaming\Python\Scripts`
8. Click "OK" on all windows
9. **Restart your terminal/IDE**

## Verify Installation

```bash
poetry --version
```

You should see something like: `Poetry (version 1.7.1)`

## Basic Poetry Commands

### 1. Install Dependencies

Navigate to the backend folder and run:

```bash
cd backend
poetry install
```

This will:
- Read `pyproject.toml`
- Create a virtual environment (usually in `C:\Users\YourUsername\AppData\Local\pypoetry\Cache\virtualenvs\`)
- Install all dependencies
- Create a `poetry.lock` file (this locks versions)

### 2. Activate Virtual Environment

```bash
poetry shell
```

Your terminal prompt will change to show you're in the virtual environment:
```
(architect-backend-py3.11) PS C:\path\to\architect\backend>
```

### 3. Run Commands Inside Virtual Environment

**Option A: Activate shell first**
```bash
poetry shell
python app/main.py
uvicorn app.main:app --reload
```

**Option B: Run directly with poetry**
```bash
poetry run python app/main.py
poetry run uvicorn app.main:app --reload
```

### 4. Add New Packages

```bash
poetry add package-name
```

Example:
```bash
poetry add requests
```

For development dependencies (like testing tools):
```bash
poetry add --group dev pytest
```

### 5. Update Dependencies

```bash
poetry update
```

### 6. Show Installed Packages

```bash
poetry show
```

### 7. Exit Virtual Environment

```bash
exit
```

Or just close the terminal.

## Understanding pyproject.toml

The `pyproject.toml` file is like `package.json` for Node.js:

```toml
[tool.poetry]
name = "architect-backend"
version = "0.1.0"
description = "..."

[tool.poetry.dependencies]
python = "^3.11"           # Python version requirement
fastapi = "^0.109.0"       # FastAPI dependency
# ^ means: allow minor version updates (0.109.x → 0.110.0 ✓, 0.109.x → 1.0.0 ✗)

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.4"          # Only needed for development
```

## Common Issues & Solutions

### "poetry: command not found"

**Solution**: Poetry isn't in your PATH. Follow the "Add Poetry to PATH" steps above and restart your terminal.

### "No module named 'poetry'"

**Solution**: If you installed via pip, try:
```bash
python -m poetry --version
```

### Virtual environment in wrong location?

You can configure where Poetry creates venvs:

```bash
poetry config virtualenvs.in-project true
```

This creates the venv in a `.venv` folder inside your project.

### Dependencies not installing?

**Solution**: Make sure you're in the `backend` folder where `pyproject.toml` is located.

### Python version mismatch?

Check your Python version:
```bash
python --version
```

If it's less than 3.11, you need to update Python first.

## Quick Reference

| Command | What it does |
|---------|-------------|
| `poetry install` | Install all dependencies |
| `poetry shell` | Activate virtual environment |
| `poetry add pkg` | Add a package |
| `poetry remove pkg` | Remove a package |
| `poetry update` | Update all packages |
| `poetry run cmd` | Run command in venv |
| `poetry show` | List installed packages |
| `poetry env info` | Show venv information |

## Workflow for Architect Project

1. **First time setup:**
   ```bash
   cd C:\path\to\architect\backend
   poetry install
   ```

2. **Daily development:**
   ```bash
   cd C:\path\to\architect\backend
   poetry shell
   # Now you can run commands:
   uvicorn app.main:app --reload
   pytest
   python -m app.services.test_script
   ```

3. **Adding a new package:**
   ```bash
   poetry add some-package
   ```
   This automatically updates `pyproject.toml` and `poetry.lock`

## Comparing to Other Tools

| Feature | pip + requirements.txt | Poetry |
|---------|----------------------|--------|
| Virtual env | Manual (`venv`) | Automatic |
| Lock file | No (version drift!) | Yes (`poetry.lock`) |
| Dev dependencies | Separate file needed | Built-in |
| Build system | setuptools | Built-in |
| Ease of use | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Next Steps

1. ✅ Install Poetry
2. ✅ Navigate to `backend` folder
3. ✅ Run `poetry install`
4. ✅ Create your `.env` file
5. ✅ Run `poetry shell` to activate environment
6. ✅ Test with `poetry run uvicorn app.main:app`

You're now ready to develop with Poetry! 🎉

---

**Questions?**
- Poetry docs: https://python-poetry.org/docs/
- If you get stuck, just ask me!
