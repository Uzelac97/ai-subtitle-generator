@echo off
title AI Subtitle Generator v1.0
cls

:: Set code page to UTF-8 to support modern symbols/emojis
chcp 65001 > nul

:: Color: Deep gray background, bright cyan text
color 0B

echo ====================================================================
echo    🤖 AI SUBTITLE GENERATOR  ^|  Production Ready
echo ====================================================================
echo.
echo   [→] Target Platform: Shorts ^& TikTok Optimizer
echo   [→] Backend Engine:   Python + OpenAI Whisper (small)
echo.
echo --------------------------------------------------------------------
echo   ⚙️  PROCESSING PIPELINE RUNNING
echo --------------------------------------------------------------------
echo.
echo   ⚡ [1/3] Optimizing audio tracks via FFmpeg...
echo   🧠 [2/3] Loading Whisper AI neural network...
echo   ⏳ [3/3] Synchronizing words and calculating timestamps...
echo.
echo   [LOGS] Initializing Python core engine...
echo --------------------------------------------------------------------
echo.

:: Execution of the main script
python -W ignore main.py --audio audio.mp3 --tekst text.txt

echo.
echo --------------------------------------------------------------------
echo   ✨ PIPELINE COMPLETE
echo --------------------------------------------------------------------
echo.
echo   [✓] Success! Subtitles generated flawlessly.
echo   📂 Output file: audio.srt
echo.
echo ====================================================================
echo   Press any key to close this terminal...
echo ====================================================================

pause > nul