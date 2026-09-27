@echo off
title Deploy to GitHub
echo ========================================================
echo   ? BHARAT EQUITIES FUNDAMENTAL TERMINAL
echo   Deploying to GitHub...
echo ========================================================
echo.
set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/YourUsername/your-repo.git): "
if "%REPO_URL%"=="" (
    echo.
    echo No URL provided. Please create a repository on github.com/new and run this script again.
    pause
    exit /b
)
echo.
echo [1/3] Setting remote repository origin...
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
echo.
echo [2/3] Setting primary branch to main...
git branch -M main
echo.
echo [3/3] Pushing all code and history to GitHub...
git push -u origin main
echo.
echo ========================================================
echo   Success! Code deployed to GitHub.
echo ========================================================
pause
