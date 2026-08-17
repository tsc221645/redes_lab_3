@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo          INICIANDO ATM
echo ========================================
echo.

python -m src.main atm-client --config configs\client1.json --bank bank1

echo.
echo ATM detenido.

pause
endlocal