@echo off
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\update_fokus_results.ps1"
pause
