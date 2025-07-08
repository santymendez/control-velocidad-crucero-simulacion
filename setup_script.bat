@echo off
setlocal

REM Paso 1: Verificar si python 3.12 está instalado
where python >nul 2>nul
if errorlevel 1 (
echo Python no está instalado. Por favor instalá Python 3.12 manualmente desde https://www.python.org/downloads/release/python-3120/
pause
exit /b
)

for /f "tokens=2 delims=[]" %%a in ('python -V 2^>^&1') do set "PY_VERSION=%%a"
echo Detectado Python %PY_VERSION%

echo.
echo Paso 2: Crear entorno virtual...
python -m venv .venv
if errorlevel 1 (
echo Error al crear el entorno virtual.
pause
exit /b
)

echo.
echo Paso 3: Activar entorno virtual...
call .venv\Scripts\activate

echo.
echo Paso 4: Instalar dependencias...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Paso 5: Ejecutar main.py...
python main.py

endlocal
pause