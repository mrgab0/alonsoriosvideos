@echo off
cd /d "%~dp0.."

set PYTHON="C:\Program Files\Python314\python.exe"

if "%1"=="" (
    echo Uso: run_pipeline.bat <palabra-clave> [idioma]
    echo Ejemplo: run_pipeline.bat casa es
    echo Ejemplo: run_pipeline.bat storm en
    pause
    exit /b 1
)

set KEYWORD=%1
set LANG=%2
if "%LANG%"=="" set LANG=en

echo ============================================
echo  HYPERFRAMES + WHISPER
echo ============================================
echo Buscando palabra: %KEYWORD%
echo Idioma: %LANG%
echo.

%PYTHON% scripts/whisper_to_motions.py ^
  --video sample/input.mp4 ^
  --keyword %KEYWORD% ^
  --model base ^
  --language %LANG% ^
  --effect highlight ^
  --duration 1.5 ^
  --render

echo.
echo ============================================
echo  LISTO. Revisa output/resultado.mp4
echo ============================================
pause
