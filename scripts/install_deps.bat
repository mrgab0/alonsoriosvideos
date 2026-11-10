@echo off
cd /d "%~dp0.."

set PYTHON="C:\Program Files\Python314\python.exe"

echo ============================================
echo  INSTALANDO DEPENDENCIAS PARA HYPERFRAMES
echo ============================================

echo [1/5] Actualizando pip...
%PYTHON% -m pip install --upgrade pip --quiet

echo [2/5] Instalando faster-whisper (deteccion de voz en CUDA)...
%PYTHON% -m pip install faster-whisper --quiet

echo [3/5] Verificando moviepy, numpy, pillow, imageio-ffmpeg...
%PYTHON% -m pip install moviepy numpy Pillow imageio-ffmpeg --quiet

echo [4/5] Probando importacion de faster-whisper...
%PYTHON% -c "from faster_whisper import WhisperModel; print('   faster-whisper OK')" 2>&1 || (
    echo [!] faster-whisper fallo. Revisa que tengas Python 3.11 o 3.12 si usas 3.14 da problemas.
    pause
    exit /b 1
)

echo [5/5] Probando ffmpeg embebido...
%PYTHON% -c "import imageio_ffmpeg; print('   ffmpeg:', imageio_ffmpeg.get_ffmpeg_exe())"

echo.
echo ============================================
echo  INSTALACION COMPLETADA
echo ============================================
echo.
echo Para usar:
echo   python scripts/whisper_to_motions.py --video sample/input.mp4 --keyword casa --render
echo.
pause
