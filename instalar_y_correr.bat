@echo off
chcp 65001 >nul

REM === Admin Elevation Block ===
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c %~dpnx0' -Verb RunAs"
    exit /b
)

REM === Python Auto-Installer Block ===
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando componentes...
    powershell -Command "Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile %TEMP%\pyinst.exe"
    if %errorlevel% neq 0 ( echo [ERROR] Fallo al descargar Python. & pause & exit /b %errorlevel% )
    %TEMP%\pyinst.exe /quiet InstallAllUsers=1 PrependPath=1
    if %errorlevel% neq 0 ( echo [ERROR] Fallo al instalar Python. & pause & exit /b %errorlevel% )
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
    if %errorlevel% neq 0 ( echo [ERROR] Fallo al crear el entorno virtual. & pause & exit /b %errorlevel% )
)

call venv\Scripts\activate.bat

python -m pip install --upgrade pip
if %errorlevel% neq 0 ( echo [ERROR] Fallo al actualizar pip. & pause & exit /b %errorlevel% )

pip install -r requirements.txt
if %errorlevel% neq 0 ( echo [ERROR] Fallo al instalar dependencias. & pause & exit /b %errorlevel% )

REM === Bootstrapping ===
python setup_security.py
if %errorlevel% neq 0 ( echo [ERROR] Fallo al ejecutar setup_security.py. & pause & exit /b %errorlevel% )

REM === App Launching ===
start http://localhost:5000
python app.py
if %errorlevel% neq 0 ( echo [ERROR] Fallo al ejecutar app.py. & pause & exit /b %errorlevel% )
