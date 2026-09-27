@echo off
title Indian Stock Fundamental Terminal (Public Live Deployment)
echo ========================================================
echo   ⚡ BHARAT EQUITIES FUNDAMENTAL TERMINAL
echo   Starting server & public internet tunnel...
echo ========================================================
echo.
start "FastAPI Server" cmd /k "python main.py"
timeout /t 3 /nobreak >nul
start "Public Internet Tunnel" cmd /k "powershell -Command \"while($true){ npx --yes localtunnel --port 8000 --subdomain indian-fundamental-terminal; Start-Sleep -Seconds 3 }\""
echo.
echo ========================================================
echo Local Server: http://localhost:8000
echo Fixed Public URL: https://indian-fundamental-terminal.loca.lt
echo Check the tunnel window for your password (public IP)
echo ========================================================
echo.
pause

