import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"

if sys.platform == "win32":
    VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

python = VENV_PYTHON if VENV_PYTHON.exists() else sys.executable

cov_args = [
    "--cov=domain",
    "--cov=use_cases",
    "--cov=infrastructure",
    "--cov=presentation",
    "--cov=app",
    "--cov-report=term",
    "--cov-report=html",
]

cmd = [str(python), "-m", "pytest", *cov_args, str(ROOT / "tests")]

result = subprocess.run(cmd, cwd=str(ROOT))

if result.returncode == 0:
    html_report = ROOT / "htmlcov" / "index.html"
    print(f"\nCoverage HTML report: file://{html_report}")

sys.exit(result.returncode)
