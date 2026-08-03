@echo off
REM ============================================================
REM  Tempestivo - configuracao inicial
REM  Rode uma unica vez. Gera config.local.bat com a conexao.
REM ============================================================

cd /d "%~dp0"

echo.
echo  ============================================
echo   Tempestivo - configuracao da captura
echo  ============================================
echo.
echo  Cole a DATABASE_URL do Railway.
echo  Onde achar: projeto ^> Postgres ^> Variables ^>
echo  DATABASE_PUBLIC_URL (a que tem "proxy.rlwy.net").
echo.

set /p CONEXAO="DATABASE_URL: "

if "%CONEXAO%"=="" (
  echo.
  echo  Nada informado. Nada foi gravado.
  pause
  exit /b 1
)

echo.
set /p CHAVE="DATAJUD_API_KEY (enter para pular): "

(
  echo @echo off
  echo REM Gerado por configurar.bat. NAO versionar este arquivo.
  echo set DATABASE_URL=%CONEXAO%
  if not "%CHAVE%"=="" echo set DATAJUD_API_KEY=%CHAVE%
) > config.local.bat

echo.
echo  Pronto. Gravado em config.local.bat.
echo.
echo  IMPORTANTE: confirme que o .gitignore contem a linha
echo  config.local.bat antes do proximo commit.
echo.
pause
