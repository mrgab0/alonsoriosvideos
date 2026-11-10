@echo off
set VIDEO=%1
set PROFILE=%2

if "%VIDEO%"=="" set VIDEO=input-3.mp4
if "%PROFILE%"=="" set PROFILE=IAshorts

echo ===================================================
echo  HYPERFRAMES AUTOMATION - PERFIL: %PROFILE%
echo  Video: %VIDEO%
echo ===================================================

python scripts/render_cli.py --input %VIDEO% --profile %PROFILE%
