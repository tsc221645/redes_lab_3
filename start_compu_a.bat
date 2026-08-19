@echo off
setlocal
cd /d "%~dp0"

echo Iniciando Router A...
start "Router A" /D "%~dp0" cmd /k python -m src.main --log-level DEBUG router --config configs\examples\router_A.json

echo El router A se esta iniciando.
echo Cuando los routers hayan convergido, ejecuta el cliente desde esta ventana.
echo.
pause

echo Enviando mensaje desde client1 hacia server1...
python -m src.main client --config configs\client1.json --to server1 --message "Hola desde la computadora A"

pause
endlocal
