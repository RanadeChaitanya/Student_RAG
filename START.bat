@echo off
title Studob - JEE Adaptive Tutor
echo ============================================
echo   Studob v0.2 - JEE Adaptive Tutor
echo ============================================
echo.
echo  Starting server at http://127.0.0.1:8000
echo.
echo  First time? Run: pip install -e ".[dev]"
echo  Then: python scripts/seed_full.py
echo.
pause >nul

echo Starting server...
python main.py
pause
