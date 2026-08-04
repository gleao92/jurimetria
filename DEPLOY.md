# Deploy do Tempestivo — guia único

> Este arquivo consolida os três guias de deploy anteriores
> (DEPLOY_RAILWAY.md e DEPLOY_SUPABASE.md foram removidos; o conteúdo
> está aqui).

## Antes de tudo: o que NÃO fazer

**Não use Streamlit Community Cloud.** Dois motivos, ambos graves:

1. **O banco some.** A plataforma não garante persistência de arquivos locais e
   pode apagar os dados a qualquer momento. Já aconteceu de perder o `.db`
   inteiro depois de um redeploy — o app continua rodando, os dados sumiram.
   Num sistema de prazos isso é catastrófico e silencioso.
2. **Sigilo.** O banco guarda nome de cliente, número de processo e teor de
   intimação — dado sob sigilo profissional. Plataforma gratuita voltada a
   demos públicas não é lugar para isso.

**Não versione o banco nem o `.env`.** O `.gitignore` já bloqueia
`controladoria.db`, `.env`, `configuracao.json` e `.pfx`. Confira com
`git status` antes do primeiro push — subir a base de clientes de um
advogado para o GitHub é um incidente de sigilo.

---

## A arquitetura em produção

Três peças, cada uma no lugar certo:

| Peça | Onde roda | Por quê |
|------|-----------|---------|
| Painel (Streamlit) | Railway | acessível de qualquer lugar |
| Banco (Postgres) | Supabase | gerenciado, com backup |
| Captura (DJEN) | **PC do escritório** (IP brasileiro) | o DJEN recusa IP fora do Brasil |

O DJEN recusa consulta de IP fora do Brasil (erro `403`). O Railway roda em
servidores fora do Brasil, então a captura **não pode** rodar lá. O único IP
brasileiro confiável que você tem hoje é a conexão do escritório — então a
captura roda no PC do escritório e grava direto no banco na nuvem. O painel na
web lê esse mesmo banco e mostra tudo na hora.

Não é remendo: separar captura de exibição é arquitetura comum. O que a
captura precisa é de um IP brasileiro; o painel precisa estar acessível de
qualquer lugar. São exigências diferentes.

**A captura local é o caminho de produção.** Ver **CAPTURA_LOCAL.md** para
instalação e agendamento automático.

> No futuro, se você passar a ter um servidor **no Brasil** (VPS em São
> Paulo, etc.), a captura pode voltar para dentro do app na nuvem e o script
> local deixa de ser necessário. Até lá, o PC do escritório é a fonte de IP
> brasileiro.

---

## Passo a passo: Railway (painel) + Supabase (banco)

### 1. Banco no Supabase (uma vez)

1. Crie um projeto em **supabase.com** (plano gratuito serve).
2. **Project Settings → Database → Connection string → Session pooler.**
3. Copie a string. **Use a porta 6543 (pooler), não a 5432** — a conexão
   direta recusa conexão de plataformas de app (`connection refused` ou
   timeout; é a causa nº 1 de dor de cabeça).
4. Troque `[YOUR-PASSWORD]` pela senha do **banco** (definida ao criar o
   projeto, não a senha da conta Supabase).

Guarde a string. Você vai colá-la no Railway no passo 3 e no `capturar.bat`.

### 2. Código no GitHub (privado)

```bash
cd <pasta-do-projeto>
git init
git add .gitignore            # PRIMEIRO o .gitignore, sozinho
git commit -m "gitignore"
git add .
git status                    # << PARE E LEIA
```

Na lista do `git status`, **NÃO pode aparecer**:
`controladoria.db`, `.env`, `configuracao.json`, nenhum `.pfx`.
Se aparecer, não faça commit — o `.gitignore` não está na pasta ou tem erro.

```bash
git commit -m "Tempestivo - deploy inicial"
# crie um repositório PRIVADO no GitHub (sistema jurídico, não público)
git remote add origin https://github.com/gleao92/jurimetria.git
git branch -M main
git push -u origin main
```

**Repositório privado**, sempre. Mesmo com o banco no `.gitignore`, o código
de um sistema de prazos de um escritório não precisa ser público.

### 3. App no Railway

1. Em **railway.com**: **New Project → Deploy from GitHub repo**.
2. Autorize o Railway a acessar seu GitHub e escolha o repositório.
3. O Railway detecta Python e constrói sozinho (via Nixpacks).
4. Aba **Variables**, adicione a única variável obrigatória:

```
DATABASE_URL = postgresql://postgres.SEU_REF:SENHA@aws-0-REGIAO.pooler.supabase.com:6543/postgres
```

   Assim que você salva, o Railway refaz o deploy. O `db.py` detecta a
   `DATABASE_URL`, entra em modo Postgres e **cria todas as tabelas no
   Supabase sozinho** — não precisa criar nada na mão.

5. Aba **Settings → Networking → Generate Domain**. O Railway te dá uma URL
   tipo `tempestivo-production.up.railway.app`. Abra — vai aparecer a tela
   de criar o acesso do advogado. Está no ar.

### 4. Captura no PC do escritório (IP brasileiro)

A captura **não roda no Railway** (IP fora do Brasil → `403`). Ela roda no
PC do escritório, agenda no Agendador de Tarefas do Windows e grava direto
no banco na nuvem. Passo a passo completo em **CAPTURA_LOCAL.md**.

---

## Alternativa: VPS + Docker + SQLite

Mais simples e barata para um único advogado. O SQLite continua servindo bem
para um usuário. Custo típico: uma VPS pequena (1–2 GB de RAM).

```bash
# na VPS, com Docker e Docker Compose instalados
git clone <seu-repo> tempestivo && cd tempestivo
cp .env.exemplo .env
nano .env                 # preencha DOMINIO
docker compose up -d
```

O Caddy emite e renova o certificado HTTPS sozinho — exige que o DNS do
domínio já aponte para o IP da VPS antes de subir. O banco fica no volume
`dados`, que sobrevive a redeploys.

**Backup é seu trabalho:**
```bash
# backup diário (coloque no cron da VPS)
docker compose exec -T app cat /app/dados/controladoria.db > backup-$(date +%F).db
```

Sem backup automático, um erro de operação apaga o histórico de prazos do
escritório. Isto não é opcional.

> **Atenção:** se a VPS for fora do Brasil, a captura continua precisando do
> PC do escritório (IP brasileiro). A VPS só hospeda o painel e o banco.

---

## Se der errado

**Build falha** → veja os logs na aba **Deployments**. Quase sempre é
dependência; o `requirements.txt` já foi testado em instalação limpa.

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

**Captura retorna 403** → está rodando de IP fora do Brasil. A captura tem
que rodar no PC do escritório (CAPTURA_LOCAL.md), não no Railway.

---

## Segurança — o mínimo antes de dado real

- [ ] **HTTPS obrigatório.** O login manda senha; sem TLS ela viaja aberta.
      O Railway já entrega HTTPS no domínio gerado.
- [ ] **Senha forte no primeiro usuário.** É o acesso a toda a carteira.
- [ ] **Backup automático testado.** Faça uma restauração de teste; backup
      que nunca foi restaurado não é backup. Ative em
      **Supabase → Database → Backups**.
- [ ] **`.env` e `.db` fora do Git.** Confira com `git status` antes do push.
- [ ] **Firewall:** só 80/443 abertos. Postgres nunca exposto à internet.

## Limite honesto da autenticação atual

O `auth.py` protege bem o acesso (Argon2id com salt, papéis, log de
tentativas), mas é autenticação de aplicação Streamlit: não tem expiração de
sessão, 2FA nem bloqueio por tentativas repetidas. Para um escritório pequeno
atrás de HTTPS, é proporcional. Se um dia virar multi-escritório, isso precisa
ser revisto antes — e aí a conversa é outra (provedor de identidade, 2FA,
isolamento de dados por cliente).

## LGPD e sigilo — o que muda ao sair da máquina do advogado

Rodando no notebook do advogado, os dados nunca saíram da posse dele. Na nuvem,
você passa a ser **operador** de dados sob sigilo profissional (art. 34 EOAB).
Na prática: disco criptografado, backup protegido, acesso restrito, e um
acerto por escrito com ele sobre o que você pode ver e o que faz com os dados.
Não é burocracia — é o que separa um fornecedor sério de um problema para os
dois lados.
