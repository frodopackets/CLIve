---
inclusion: always
---

# WSL Development Environment Guidelines

## Critical Environment Context
- **Operating System**: Windows with WSL Ubuntu
- **Current Working Directory**: Always `/home/robww/CLIve` (the project root)
- **Python Environment**: Must use virtual environment at `./venv/bin/activate`
- **Shell Commands**: All Python/development commands must run in WSL Ubuntu

## Command Execution Rules

### Python Commands
- **ALWAYS** use: `wsl bash -c "cd CLIve && source venv/bin/activate && [command]"`
- **NEVER** use: `python` or `pip` directly from PowerShell
- **NEVER** use: `wsl python3` without activating virtual environment

### Directory Context
- **Current Directory**: `/home/robww/CLIve` is the project root
- **Backend Code**: Located at `./backend/` relative to project root
- **Virtual Environment**: Located at `./venv/` relative to project root

### Import Path Issues
- Python imports in backend code use relative imports from backend directory
- When running tests or main.py, ensure PYTHONPATH includes the project root
- Use `PYTHONPATH=. python -m pytest` or `PYTHONPATH=. python backend/main.py`

### Correct Command Patterns

#### Running Tests
```bash
wsl bash -c "cd CLIve && source venv/bin/activate && PYTHONPATH=. python -m pytest backend/tests/test_main.py -v"
```

#### Running Backend Server
```bash
wsl bash -c "cd CLIve && source venv/bin/activate && PYTHONPATH=. python backend/main.py"
```

#### Installing Dependencies
```bash
wsl bash -c "cd CLIve && source venv/bin/activate && pip install -r backend/requirements.txt"
```

## Common Mistakes to Avoid

1. **Don't run Python commands from PowerShell directly**
2. **Don't forget to activate virtual environment**
3. **Don't forget to set PYTHONPATH when running backend code**
4. **Don't assume current directory - always cd to CLIve first**
5. **Don't use system Python - always use virtual environment**

## File Structure Context
```
/home/robww/CLIve/          # Project root
├── backend/                # Backend Python code
│   ├── main.py            # FastAPI application
│   ├── config.py          # Configuration
│   ├── routers/           # API routes
│   ├── middleware/        # Middleware
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── tests/             # Test files
├── venv/                  # Python virtual environment
└── ...
```

## Environment Variables
- Virtual environment must be activated for all Python operations
- PYTHONPATH should be set to project root (.) when running backend code
- All development happens in WSL Ubuntu, not Windows PowerShell