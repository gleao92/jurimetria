# Deploy no Railway + Supabase — passo a passo

Testado: o app sobe na porta dinâmica do Railway e passa no healthcheck.
Os arquivos `railway.json`, `Procfile` e `runtime.txt` já estão prontos.

---

## Parte 1 — Banco no Supabase (uma vez)

1. Crie um projeto em **supabase.com**.
2. **Project Settings → Database → Connection string → Session pooler.**
3. Copie a string. **Use a porta 6543 (pooler), não a 5432** — a direta
   recusa conexão de plataformas de app.
4. Troque `[YOUR-PASSWORD]` pela senha do banco (definida ao criar o projeto).

Guarde essa string. Você vai colá-la no Railway no passo 2.4.

---

## Parte 2 — Subir para o GitHub e conectar ao Railway

### 2.1 — Antes do primeiro push: confira o que vai subir

```bash
cd <pasta-do-projeto>
git init
git add .
git status          # << PARE E LEIA
```

Na lista do `git status`, **NÃO pode aparecer**:
`controladoria.db`, `.env`, `configuracao.json`, nenhum `.pfx`.

Se aparecer algum, NÃO faça commit — o `.gitignore` não está na pasta ou tem
erro. Subir a base de clientes de um advogado para o GitHub é incidente de
sigilo. Só prossiga quando a lista estiver limpa.

### 2.2 — Commit e push

```bash
git commit -m "Tempestivo - deploy inicial"
# crie um repositório PRIVADO no GitHub (não público — é sistema jurídico)
git remote add origin https://github.com/gleao92/tempestivo.git
git branch -M main
git push -u origin main
```

**Repositório privado**, sempre. Mesmo com o banco no `.gitignore`, o código
de um sistema de prazos de um escritório não precisa ser público.

### 2.3 — Criar o projeto no Railway

1. Em **railway.com**: **New Project → Deploy from GitHub repo**.
2. Autorize o Railway a acessar seu GitHub e escolha o repositório.
3. O Railway detecta Python e começa a construir sozinho (via Nixpacks).

### 2.4 — A única variável obrigatória

No projeto, aba **Variables**, adicione:

```
DATABASE_URL = postgresql://postgres.SEU_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:6543/postgres
```

(a string do Supabase do passo 1.4)

Assim que você salva, o Railway refaz o deploy. O `db.py` detecta a
`DATABASE_URL`, entra em modo Postgres e **cria todas as tabelas no Supabase
sozinho** — não precisa criar nada na mão.

### 2.5 — Gerar o endereço público

1. Aba **Settings → Networking → Generate Domain**.
2. O Railway te dá uma URL tipo `tempestivo-production.up.railway.app`.
3. Abra. Vai aparecer a tela de criar o acesso do advogado.

Pronto — está no ar.

---

## Se der errado

**Build falha** → veja os logs na aba **Deployments**. Quase sempre é uma
dependência; o `requirements.txt` já foi testado em instalação limpa, então
confira se subiu a versão certa dele.

**"Application failed to respond"** → o app subiu mas o Railway não o alcança.
Confirme que o **Start Command** (Settings → Deploy) usa `$PORT`:
```
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```
O `railway.json` já define isso, mas se você mexeu no comando, é aqui.

**Conecta mas dá erro de banco** → a `DATABASE_URL` está com a porta errada
(use 6543) ou a senha errada (é a senha do BANCO, não a da conta Supabase).

**App lento no primeiro acesso** → normal. O plano gratuito "dorme" e leva
alguns segundos para acordar na primeira visita.

---

## Depois de no ar

- **Backup**: ative em **Supabase → Database → Backups**. O histórico de
  prazos do escritório não pode depender de um único lugar.
- **Custo**: Railway tem cota gratuita mensal; um app de um advogado costuma
  caber nela. Passando disso, é upgrade barato.
- **Sigilo**: os dados agora vivem no Supabase (nuvem AWS). O advogado precisa
  saber e concordar — não é decisão só técnica.
