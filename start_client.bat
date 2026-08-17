@echo off
setlocal
cd /d "%~dp0"

set "DESTINO=%~1"
if "%DESTINO%"=="" set "DESTINO=server1"

set "MENSAJE=%~2"
if "%MENSAJE%"=="" set "MENSAJE=Hola desde el cliente"

echo Enviando mensaje a %DESTINO%...
python -m src.main client --config configs\client1.json --to "%DESTINO%" --message "%MENSAJE%"

pause
endlocal
