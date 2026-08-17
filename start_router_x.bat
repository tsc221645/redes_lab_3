@echo off
setlocal
cd /d "%~dp0"

echo Iniciando Router X...
python -m src.main --log-level DEBUG router --config configs\router_x.json

endlocal
