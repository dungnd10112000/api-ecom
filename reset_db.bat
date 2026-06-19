@echo off
title Reset PostgreSQL Password & Setup DB (TCT_CRM)
cd /d "%~dp0"
echo Dang khoi chay tap lenh tu dong reset mat khau PostgreSQL...
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe reset_db.py
) else (
    python reset_db.py
)

if %errorlevel% neq 0 (
    echo.
    echo Da xay ra loi khi chay tap lenh reset. Vui long kiem tra xem Python da duoc cai dat chua.
    pause
)
