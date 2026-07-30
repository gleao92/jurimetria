# Publicar com Supabase (banco) + hospedagem do app

## Entenda os dois papéis primeiro

Publicar o Tempestivo exige DUAS coisas, e o Supabase resolve só uma:

| O quê | Quem faz | Supabase? |
|-------|----------|-----------|
| Guardar os dados (Postgres) | Supabase | **Sim** |
| Rodar o `streamlit run app.py` | um servidor de app | **Não** |

O Supabase é o banco. Ele NÃO roda o Python. Você ainda precisa de um lugar
que execute o app — Railway, Render, Fly.io ou uma VPS. A boa notícia: com o
Supabase cuidando dos dados, esse lugar pode ter disco efêmero sem problema,
porque nada importante fica no disco dele.

Isto resolve de vez o risco do disco sumir: os dados vivem no Postgres do
Supabase, que é gerenciado e com backup, não num arquivo `.db` que um redeploy
apaga.

---

## Passo 1 — Criar o banco no Supabase

1. Crie um projeto em supabase.com (o plano gratuito serve para um advogado).
2. Vá em **Project Settings → Database → Connection string**.
3. Copie a string do modo **"Session pooler"** (não a "Direct connection").

### O detalhe que trava todo mundo: a porta

O Supabase te dá dois endereços. Use o **pooler**, porta **6543**, não a
conexão direta na 5432:

```
# CERTO — Session pooler, porta 6543:
postgresql://postgres.SEU_REF:SUA_SENHA@aws-0-REGIAO.pooler.supabase.com:6543/postgres

# a direta (5432) costuma recusar conexão de plataformas de app e falha
# com "connection refused" ou timeout — é a causa nº 1 de dor de cabeça.
```

Troque `SUA_SENHA` pela senha do banco (a que você definiu ao criar o projeto,
NÃO a senha da sua conta Supabase).

---

## Passo 2 — Hospedar o app (exemplo: Railway)

Railway é o mais simples para quem não quer administrar servidor.

1. Suba o código para um repositório no GitHub.
   **Confira antes:** o `.gitignore` bloqueia `controladoria.db`, `.env` e
   `.pfx`. Subir a base de clientes de um advogado para o GitHub é um
   incidente de sigilo — verifique com `git status` antes do primeiro push.
2. No Railway: **New Project → Deploy from GitHub repo**.
3. Em **Variables**, adicione uma única variável:
   ```
   DATABASE_URL = postgresql://postgres.SEU_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:6543/postgres
   ```
4. Em **Settings → Start Command**, coloque:
   ```
   streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
   ```
   (O `$PORT` é obrigatório — o Railway escolhe a porta, não é a 8501.)
5. Deploy. Na primeira execução, o `db.py` cria todas as tabelas no Supabase
   sozinho (o `init()` roda o schema). Não precisa criar tabela na mão.

Render e Fly.io seguem a mesma ideia: uma variável `DATABASE_URL` e o comando
de start com a porta que a plataforma fornecer.

---

## Passo 3 — Proteger o acesso (importante)

Assim que estiver no ar, qualquer pessoa com o link vê a tela de login. O
login já existe (Argon2id, tentativas registradas), mas:

- Crie a senha do advogado no primeiro acesso e escolha uma senha forte.
- O Supabase, por padrão, aceita conexão de qualquer IP. Para um único
  advogado, considere restringir em **Database → Network Restrictions** ao IP
  da plataforma de hospedagem, se ela oferecer IP fixo.

---

## Sobre sigilo — leia antes de pôr dados reais

Este banco guarda **nome de cliente, número de processo e teor de intimação**,
cobertos por sigilo profissional (art. 34 EOAB). Ao usar Supabase:

- O dado sai do computador do advogado e passa a residir num provedor de nuvem
  (o Supabase roda em AWS). Isso é aceitável e comum, mas é uma decisão que o
  **advogado** precisa conhecer e concordar — não é detalhe técnico só seu.
- Ative backups no Supabase (**Database → Backups**). O plano pago tem backup
  diário automático; no gratuito, exporte periodicamente.
- Nunca coloque a `DATABASE_URL` no código nem no GitHub. Só na variável de
  ambiente da plataforma.

---

## Alternativa: só quer testar rápido, sem nada disso?

Para uma demonstração de poucos dias, com dados FICTÍCIOS (nunca reais):
Railway ou Render aceitam o app direto com SQLite, sem Supabase. O disco é
efêmero — os dados somem no próximo deploy — mas para mostrar a interface ao
advogado antes de decidir, serve. Para uso real, volte ao Supabase.
