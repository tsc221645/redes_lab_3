@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo        INICIANDO SERVIDOR ATM
echo ========================================
echo.

python -m src.main atm-server --config configs\examples\server1.json

echo.
echo Servidor ATM detenido.

pause
endlocal