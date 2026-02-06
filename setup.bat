@echo off
echo === LG TV Switcher Setup ===
echo.

echo Installing websocket-client...
pip install websocket-client
echo.

echo Starting TV pairing...
python "%~dp0lg_switch.py" --setup %*
