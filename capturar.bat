@echo off
REM ============================================================
REM  Tempestivo - captura das publicacoes
REM
REM  Roda NESTE computador (IP brasileiro) e grava no banco da
REM  nuvem. O DJEN recusa consulta vinda de servidor no exterior,
REM  entao a captura fica aqui e o painel continua na web.
REM
REM  A senha do banco NAO fica neste arquivo. Ela fica em
REM  config.local.bat, que nunca vai para o GitHub.
REM  Primeira vez? Rode configurar.bat.
REM ============================================================

cd /d "%~dp0"

if exist "config.local.bat" call "config.local.bat"

if "%DATABASE_URL%"=="" (
  echo.
  echo  ERRO: DATABASE_URL nao definida.
  echo  Rode configurar.bat uma vez para cadastrar a conexao.
  echo.
  pause
  exit /b 2
)

where python >nul 2>&1
if errorlevel 1 (
  echo.
  echo  ERRO: Python nao encontrado no PATH.
  echo.
  pause
  exit /b 2
)

echo.
echo  Tempestivo - buscando publicacoes...
echo.

python capturar.py --dias 30 --oab 61423 --uf GO
set RESULTADO=%errorlevel%

echo.
if %RESULTADO% geq 2 (
  echo  A captura FALHOU. Leia a mensagem acima.
) else (
  echo  Concluido. Os prazos novos ja aparecem no painel.
)
echo.

REM Mantem a janela aberta no duplo clique.
REM Pelo Agendador de Tarefas, passe qualquer argumento para pular.
if "%1"=="" pause

exit /b %RESULTADO%
