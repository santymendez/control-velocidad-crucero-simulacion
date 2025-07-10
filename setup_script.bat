@echo off
setlocal

REM Paso 1: Verificar si py -3.12 está disponible
py -3.12 -c "exit()" >nul 2>nul
if errorlevel 1 (
    echo Python 3.12 no está disponible en el sistema.
    echo Por favor instalalo desde: https://www.python.org/downloads/release/python-3120/
    pause
    exit /b
)

echo Python 3.12 encontrado correctamente.

REM Paso 2: Crear entorno virtual si no existe
if not exist ".venv" (
    echo Creando entorno virtual con py -3.12...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo Error al crear el entorno virtual.
        pause
        exit /b
    )
) else (
    echo Entorno virtual ya existe. Saltando creación.
)

REM Paso 3: Activar entorno virtual
call .venv\Scripts\activate

REM Paso 4: Instalar dependencias siempre que exista requirements.txt
if exist requirements.txt (
    echo Instalando dependencias desde requirements.txt...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo No se encontro requirements.txt, saltando instalacion de dependencias.
)

REM Paso 5: Ejecutar el script principal
echo Ejecutando main.py...
python main.py

endlocal
pause
