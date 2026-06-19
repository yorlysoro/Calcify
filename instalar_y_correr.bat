REM BSD 3-Clause License
REM
REM Copyright (c) 2026, yorlysoro
REM
REM Redistribution and use in source and binary forms, with or without
REM modification, are permitted provided that the following conditions are met:
REM
REM 1. Redistributions of source code must retain the above copyright notice, this
REM    list of conditions and the following disclaimer.
REM
REM 2. Redistributions in binary form must reproduce the above copyright notice,
REM    this list of conditions and the following disclaimer in the documentation
REM    and/or other materials provided with the distribution.
REM
REM 3. Neither the name of the copyright holder nor the names of its
REM    contributors may be used to endorse or promote products derived from
REM    this software without specific prior written permission.
REM
REM THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
REM AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
REM IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
REM DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
REM FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
REM DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
REM SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
REM CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
REM OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
REM OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

@echo off
chcp 65001 >nul

REM === Admin Elevation Block ===
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c %~dpnx0' -Verb RunAs"
    exit /b
)

REM === Python Auto-Installer Block ===
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing components...
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile %TEMP%\pyinst.exe"
    if %errorlevel% neq 0 ( echo [ERROR] Failed to download Python. & pause & exit /b %errorlevel% )
    %TEMP%\pyinst.exe /quiet InstallAllUsers=1 PrependPath=1
    if %errorlevel% neq 0 ( echo [ERROR] Failed to install Python. & pause & exit /b %errorlevel% )
    powershell -Command "$machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine'); $userPath = [Environment]::GetEnvironmentVariable('Path', 'User'); $newPath = $machinePath + ';' + $userPath; [Environment]::SetEnvironmentVariable('Path', $newPath, 'Process')"
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        if exist "%ProgramFiles%\Python311\python.exe" (
            set "PATH=%ProgramFiles%\Python311;%PATH%"
        )
    )
)

REM === Virtual Environment Bootstrapper ===
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv
    if %errorlevel% neq 0 ( echo [ERROR] Failed to create virtual environment. & pause & exit /b %errorlevel% )
)

call venv\Scripts\activate.bat

python -m pip install --upgrade pip
if %errorlevel% neq 0 ( echo [ERROR] Failed to update pip. & pause & exit /b %errorlevel% )

pip install -r requirements.txt
if %errorlevel% neq 0 ( echo [ERROR] Failed to install dependencies. & pause & exit /b %errorlevel% )

REM === Bootstrapping ===
python setup_security.py
if %errorlevel% neq 0 ( echo [ERROR] Failed to run setup_security.py. & pause & exit /b %errorlevel% )

REM === App Launching ===
start http://localhost:5000
python app.py
if %errorlevel% neq 0 ( echo [ERROR] Failed to run app.py. & pause & exit /b %errorlevel% )
