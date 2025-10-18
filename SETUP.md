# Developer Setup Guide

**For Developers:** Quick setup to run the API locally. Assumes infrastructure is already configured by your admin/DBA team.

**For Admins:** See [DEPLOYMENT.md](DEPLOYMENT.md) for infrastructure setup.

---

## Prerequisites

Verify you have access to the following (contact your admin if not):

- ✅ **Snowflake credentials** with read access to LTC data tables
- ✅ **Python 3.9-3.11** installed
- ✅ **Git** for version control
- ✅ Network access to Snowflake account

---

## Quick Start (5 minutes)

```bash
# 1. Clone & navigate
git clone <repo-url> && cd ltc-insurance-api

# 2. Install dependencies
pip install poetry && poetry install

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Start API
poetry run uvicorn app.main:app --reload --port 8080

# 5. Test
curl http://localhost:8080/health
```

**Done!** API running at http://localhost:8080/api/v1/docs

---

## Detailed Setup

### 1. Environment Setup

#### Install Poetry (if not installed)

**Auto-detect and install:**
```bash
command -v poetry >/dev/null 2>&1 || {
  curl -sSL https://install.python-poetry.org | python3 -
  export PATH="$HOME/.local/bin:$PATH"
}
```

**Windows PowerShell:**
```powershell
if (!(Get-Command poetry -ErrorAction SilentlyContinue)) {
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    $env:Path += ";$env:APPDATA\Python\Scripts"
}
```

#### Verify Python Version

```bash
python --version  # Must be 3.9, 3.10, or 3.11
```

If version is incorrect:
```bash
poetry env use python3.9  # or python3.10, python3.11
```

---

### 2. Install Dependencies

```bash
# Install all dependencies (creates virtualenv automatically)
poetry install

# Verify installation
poetry run python -c "import fastapi, snowflake.snowpark; print('✓ All dependencies installed')"
```

**Expected output:** `✓ All dependencies installed`

---

### 3. Configure Environment Variables

#### Copy template
```bash
cp .env.example .env
```

#### Get credentials from your admin

Your admin should provide:
- Snowflake account identifier
- Database and schema names
- Your username and assigned role
- Warehouse name

#### Edit `.env`

```bash
# macOS/Linux
nano .env

# Windows
notepad .env
```

**Required values:**
```bash
# === Snowflake (provided by admin) ===
SNOWFLAKE_ACCOUNT=<ask-admin>
SNOWFLAKE_USER=<your-username>
SNOWFLAKE_PASSWORD=<your-password>
SNOWFLAKE_WAREHOUSE=<ask-admin>
SNOWFLAKE_DATABASE=<ask-admin>
SNOWFLAKE_SCHEMA=<ask-admin>
SNOWFLAKE_ROLE=<assigned-role>

# === JWT (generate yourself) ===
JWT_SECRET_KEY=<generate-below>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=1

# === API Config ===
ENVIRONMENT=development
LOG_LEVEL=INFO
```

#### Generate JWT Secret

**One-liner (any OS with Python):**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Alternative (OpenSSL):**
```bash
openssl rand -hex 32
```

Copy output to `JWT_SECRET_KEY` in `.env`

---

### 4. Validate Configuration

Run validation script before starting:

```bash
poetry run python -c "
from app.core.config import settings
from snowflake.snowpark import Session

print('Validating configuration...\n')

# Check required fields
assert settings.SNOWFLAKE_ACCOUNT, '❌ SNOWFLAKE_ACCOUNT not set'
assert settings.SNOWFLAKE_USER, '❌ SNOWFLAKE_USER not set'
assert settings.SNOWFLAKE_PASSWORD, '❌ SNOWFLAKE_PASSWORD not set'
assert settings.JWT_SECRET_KEY != 'your_secret_key_here', '❌ Generate JWT_SECRET_KEY'

print('✓ All environment variables configured')

# Test Snowflake connection
try:
    session = Session.builder.configs({
        'account': settings.SNOWFLAKE_ACCOUNT,
        'user': settings.SNOWFLAKE_USER,
        'password': settings.SNOWFLAKE_PASSWORD,
        'role': settings.SNOWFLAKE_ROLE,
        'warehouse': settings.SNOWFLAKE_WAREHOUSE,
        'database': settings.SNOWFLAKE_DATABASE,
        'schema': settings.SNOWFLAKE_SCHEMA
    }).create()
    
    result = session.sql('SELECT CURRENT_USER(), CURRENT_ROLE()').collect()
    print(f'✓ Connected to Snowflake as {result[0][0]} with role {result[0][1]}')
    
    # Verify table access
    tables = session.sql(\"SHOW TABLES LIKE 'POLICY%'\").collect()
    if tables:
        print(f'✓ Can access {len(tables)} POLICY table(s)')
    else:
        print('⚠ No POLICY tables found - contact admin to verify permissions')
    
    session.close()
    print('\n✅ Configuration valid - ready to start API')
    
except Exception as e:
    print(f'\n❌ Connection failed: {str(e)}')
    print('   Contact your admin to verify credentials and permissions')
    exit(1)
"
```

**Expected output:**
```
✓ All environment variables configured
✓ Connected to Snowflake as YOUR_USER with role LTC_APP_ROLE
✓ Can access 1 POLICY table(s)

✅ Configuration valid - ready to start API
```

---

### 5. Start the API

#### Development mode (with auto-reload)

```bash
poetry run uvicorn app.main:app --reload --port 8080
```

#### Production mode (optimized)

```bash
poetry run uvicorn app.main:app --port 8080 --workers 4
```

#### Background mode

**macOS/Linux:**
```bash
nohup poetry run uvicorn app.main:app --port 8080 > api.log 2>&1 &
echo $! > api.pid  # Save PID for later
```

**Windows PowerShell:**
```powershell
Start-Job -ScriptBlock {
    Set-Location $using:PWD
    poetry run uvicorn app.main:app --port 8080
}
```

---

### 6. Verify API is Running

#### Health checks

```bash
# Basic health
curl http://localhost:8080/health

# With database check
curl http://localhost:8080/ready
```

**Expected response:**
```json
{"status":"ready","snowflake":"connected","timestamp":"2024-10-14T18:30:45"}
```

#### Interactive documentation

Open in browser:
```
http://localhost:8080/api/v1/docs
```

---

## Development Workflow

### Daily workflow

```bash
# Start API
poetry run uvicorn app.main:app --reload --port 8080

# Make code changes (auto-reloads)
# Test in browser: http://localhost:8080/api/v1/docs

# Stop API: Ctrl+C
```

### Working with dependencies

```bash
# Add new package
poetry add package-name

# Add dev dependency
poetry add --group dev pytest

# Update all packages
poetry update

# Show installed packages
poetry show --tree
```

### Code quality

```bash
# Type checking (if mypy configured)
poetry run mypy app/

# Linting (if ruff/flake8 configured)
poetry run ruff check app/

# Format code (if black configured)
poetry run black app/
```

---

## Testing the API

### 1. Get Authentication Token

**Via Swagger UI:**
1. Go to http://localhost:8080/api/v1/docs
2. Find `POST /api/v1/auth/login`
3. Click "Try it out"
4. Enter admin credentials (ask admin for test credentials)
5. Copy `access_token` from response

**Via curl:**
```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"LTCInsurance2024!"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"
```

### 2. Make Authenticated Requests

```bash
# Get policies
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/v1/policies?limit=5"

# Get specific policy
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/v1/policies/100004"

# Filter by state
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8080/api/v1/policies?insured_state=CA&limit=10"
```

### 3. Python Client Example

```python
import requests

# Login
response = requests.post(
    "http://localhost:8080/api/v1/auth/login",
    json={"username": "admin", "password": "LTCInsurance2024!"}
)
token = response.json()["access_token"]

# Query API
headers = {"Authorization": f"Bearer {token}"}
policies = requests.get(
    "http://localhost:8080/api/v1/policies",
    headers=headers,
    params={"limit": 10, "insured_state": "CA"}
).json()

print(f"Found {len(policies)} policies")
```

---

## Troubleshooting

### Auto-diagnostic script

```bash
poetry run python -c "
import sys
from app.core.config import settings

issues = []

# Check Python version
v = sys.version_info
if not (3, 9) <= (v.major, v.minor) < (3, 12):
    issues.append(f'Python {v.major}.{v.minor} not supported (need 3.9-3.11)')

# Check env vars
if settings.SNOWFLAKE_ACCOUNT == 'your_account_identifier':
    issues.append('SNOWFLAKE_ACCOUNT not configured in .env')
if settings.JWT_SECRET_KEY == 'your_secret_key_here':
    issues.append('JWT_SECRET_KEY not generated')

if issues:
    print('❌ Issues found:\n' + '\n'.join(f'  - {i}' for i in issues))
else:
    print('✅ All checks passed')
"
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'app'` | Run from project root directory |
| `404 Not Found: post your_account_identifier.snowflakecomputing.com` | Update `SNOWFLAKE_ACCOUNT` in `.env` |
| `Incorrect username or password` | Verify credentials with admin |
| `Object 'POLICY_MONTHLY_SNAPSHOT_FACT' does not exist` | Contact admin - tables not set up |
| `Port 8080 already in use` | Kill process: `lsof -ti:8080 \| xargs kill -9` (Mac/Linux)<br>`netstat -ano \| findstr :8080` then `Stop-Process -Id <PID>` (Windows) |
| `poetry: command not found` | Install Poetry and add to PATH (see step 1) |

### Get help

```bash
# Check logs
poetry run uvicorn app.main:app --log-level debug

# Verify Snowflake tables exist
poetry run python -c "
from app.core.snowflake import SnowparkSessionManager
manager = SnowparkSessionManager()
session = manager.get_sync_session()
tables = session.sql('SHOW TABLES').collect()
print('\n'.join([row['name'] for row in tables]))
"

# Test specific endpoint
curl -v http://localhost:8080/health
```

---

## Advanced Configuration

### Custom port

```bash
poetry run uvicorn app.main:app --reload --port 8081
```

### Multiple workers (production)

```bash
poetry run uvicorn app.main:app --workers 4 --port 8080
```

### Custom log level

```bash
# In .env
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

# Or via CLI
poetry run uvicorn app.main:app --log-level debug
```

### Using Docker (optional)

```bash
# Build image
docker build -t ltc-api .

# Run container
docker run -p 8080:8080 --env-file .env ltc-api
```

---

## IDE Setup

### VS Code

Install recommended extensions:
```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
```

`.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true
  }
}
```

### PyCharm

1. Open project
2. Settings → Project → Python Interpreter
3. Select "Poetry Environment"
4. PyCharm auto-detects `pyproject.toml`

---

## Performance Tips

### 1. Connection pooling
The app uses singleton session management - connection is reused automatically.

### 2. Query optimization
Use `?fields=` parameter to select only needed columns:
```bash
curl "http://localhost:8080/api/v1/policies?fields=policy_id,carrier_name&limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Pagination
Always use `limit` and `offset` for large datasets:
```bash
# First page
curl "http://localhost:8080/api/v1/policies?limit=100&offset=0"

# Second page
curl "http://localhost:8080/api/v1/policies?limit=100&offset=100"
```

---

## Next Steps

- ✅ API running locally
- 📖 Explore [README.md](README.md) for architecture and API docs
- 🚀 For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)
- 🔍 Use interactive docs: http://localhost:8080/api/v1/docs

---

## Cheat Sheet

```bash
# Setup (one-time)
git clone <repo> && cd ltc-insurance-api
pip install poetry && poetry install
cp .env.example .env && nano .env

# Daily development
poetry run uvicorn app.main:app --reload --port 8080

# Testing
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/docs  # Open in browser

# Maintenance
poetry update              # Update dependencies
poetry add <package>       # Add new package
poetry show --tree         # View dependencies

# Troubleshooting
poetry install --no-cache  # Reinstall
lsof -ti:8080 | xargs kill # Kill port 8080 (Mac/Linux)
```

---

**Need admin access?** Contact your DBA team with the infrastructure requirements in [DEPLOYMENT.md](DEPLOYMENT.md).
