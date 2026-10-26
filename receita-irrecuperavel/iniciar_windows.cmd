@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Instale Python 3.12 ou superior em python.org e execute novamente.
        pause
        exit /b 1
    )
    py -3 -m venv .venv
    if errorlevel 1 goto falha
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto falha
if not exist config_local.py copy config_local.example.py config_local.py >nul
 echo.
 echo Servidor local: abra o navegador na porta 8001 do seu computador.
 echo Configure config_local.py para consultar Oracle. Excel e CSV funcionam sem banco.
 echo Para encerrar, pressione Ctrl+C nesta janela.
.venv\Scripts\python.exe painel\app.py
if errorlevel 1 goto falha
exit /b 0
:falha
 echo Nao foi possivel iniciar. Confira a mensagem acima.
 pause
 exit /b 1
