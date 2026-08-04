# Está rodando a versão certa?

O mesmo erro voltando **idêntico** depois de uma correção quase sempre
significa que o código novo não foi carregado — não que a correção falhou.

## Duas causas, nesta ordem de probabilidade

**1. Pasta antiga.** Cada download do navegador cria uma pasta nova
(`files (8)`, `files (9)`, `files (10)`...). Se o Streamlit subiu de uma pasta
e os arquivos novos foram para outra, ele continua rodando o código velho.

No PowerShell, veja de onde ele está rodando:
```powershell
Get-Location
dir mni.py
```
A data de modificação do `mni.py` tem que ser de agora.

**2. Módulo em cache.** O Python guarda os módulos já importados. Trocar um
`.py` com o app no ar nem sempre recarrega. **Pare com Ctrl+C e suba de novo:**
```powershell
python -m streamlit run app.py
```

## Como conferir sem adivinhar

A aba Configuração mostra, logo acima do campo de consulta de processo:

```
módulo mni.py carregado: 2026-07-20.c — cliente tolerante + plano B em XML cru
arquivo em uso: C:\...\mni.py
```

Se aparecer **"ANTIGO — sem versão"**, é código velho, ponto final.
Se o caminho apontar para outra pasta, é a pasta errada.

## Sugestão para parar de sofrer com isso

Mantenha UMA pasta fixa do projeto e copie os arquivos baixados para dentro
dela, em vez de rodar de dentro de `Downloads`:

```powershell
mkdir C:\tempestivo
# copie os arquivos novos para C:\tempestivo, sempre
cd C:\tempestivo
python -m streamlit run app.py
```

Com o `git` isso fica ainda melhor, mas uma pasta fixa já resolve 90%.
