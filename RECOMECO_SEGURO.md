# Recomeço seguro do repositório (o banco vazou — leia antes)

## O que aconteceu
O `controladoria.db` e o `configuracao.json` foram para o GitHub, num
repositório PÚBLICO. Esses arquivos contêm dados sob sigilo. O `.gitignore`
não os bloqueou porque provavelmente o `git add .` rodou antes dele existir
na pasta — o Git não ignora o que já está rastreando.

## Passo 1 — AGORA: estancar (1 minuto)
GitHub → repositório `jurimetria` → **Settings** → desça até **Danger Zone**
→ **Change repository visibility** → **Make private**.

Isso tira o banco do acesso público imediatamente. Faça antes de tudo.

## Passo 2 — Recomeço limpo (recomendado)
Como o repo tem só 1 commit, apagar e refazer é mais seguro que tentar limpar
o histórico (os arquivos continuariam nos commits antigos).

### 2a. Apague o repositório no GitHub
Settings → Danger Zone → **Delete this repository**.

### 2b. Na sua máquina, prepare a pasta corretamente
```bash
cd <pasta-do-projeto>

# remova o histórico git atual (que contém o banco)
rmdir /s /q .git        # Windows (PowerShell/cmd)
# no lugar do controladoria.db versionado, garanta que ele NÃO será re-adicionado

# confirme que o .gitignore existe ANTES de qualquer git add
type .gitignore         # tem que listar controladoria.db, .env, configuracao.json
```

### 2c. Apague os arquivos sensíveis da pasta (eles serão recriados)
```bash
del controladoria.db          # o app recria vazio no 1º uso
del configuracao.json         # você reconfigura na tela de Ajustes
```
(Se quiser guardar os dados de teste, mova para fora da pasta antes.)

### 2d. Comece o git do zero, com o .gitignore JÁ presente
```bash
git init
git add .gitignore            # PRIMEIRO o .gitignore, sozinho
git commit -m "gitignore"
git add .                     # agora o resto — o banco já está sendo ignorado
git status                    # CONFIRA: controladoria.db NÃO pode aparecer
```

Só prossiga se o `git status` NÃO listar `controladoria.db` nem
`configuracao.json`.

### 2e. Crie o repositório novo — PRIVADO
No GitHub: **New repository** → nome → marque **Private** → Create.
Não marque "Add README" (você já tem um).

```bash
git commit -m "Tempestivo - deploy inicial"
git remote add origin https://github.com/gleao92/NOME-NOVO.git
git branch -M main
git push -u origin main
```

## Passo 3 — Se havia senha no configuracao.json
Se o `configuracao.json` que vazou tinha a senha do MNI do advogado, **troque
essa senha** no sistema do tribunal. Um dado que foi público deve ser tratado
como comprometido, mesmo que você ache que ninguém viu.

## Como evitar da próxima vez
A regra de ouro: **`.gitignore` sempre no primeiro commit, antes de qualquer
`git add .`**. O passo 2d faz exatamente isso — adiciona o `.gitignore`
sozinho primeiro, e só depois o resto.
