@echo off
setlocal
cd /d "%~dp0"

echo Iniciando Router B...
python -m src.main --log-level DEBUG router --config configs\examples\router_B.json

endlocal
