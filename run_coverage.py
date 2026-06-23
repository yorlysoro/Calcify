# BSD 3-Clause License
#
# Copyright (c) 2026, yorlysoro
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
