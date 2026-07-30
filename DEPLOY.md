# Subindo o Tempestivo para a nuvem

## Antes de tudo: o que NÃO fazer

**Não use Streamlit Community Cloud.** Dois motivos, ambos graves aqui:

1. **O banco some.** A documentação do Streamlit diz que apps do Community
   Cloud não garantem persistência de arquivos locais e que a plataforma pode
   apagar esses dados a qualquer momento. Já aconteceu com gente que perdeu o
   `.db` inteiro depois de um redeploy — o app continua rodando, os dados
   simplesmente sumiram. Num sistema de prazos isso é catastrófico e silencioso.
2. **Sigilo.** Este banco guarda nome de cliente, número de processo e teor de
   intimação — dado coberto por sigilo profissional. Plataforma gratuita
   voltada a demos públicas não é lugar para isso.

**Não versione o banco nem o `.env`.** O `.gitignore` já bloqueia
`controladoria.db`, `.env` e `.pfx`. Confira antes do primeiro `git push` —
subir a base de clientes de um advogado para o GitHub é um incidente de sigilo.

---

## Opção A — VPS + Docker (recomendada para 1 advogado)

Mais simples, mais barata, e o SQLite continua servindo bem para um usuário.
Custo típico: uma VPS pequena (1–2 GB de RAM) já basta.

```bash
# na VPS, com Docker e Docker Compose instalados
git clone <seu-repo> tempestivo && cd tempestivo
cp .env.exemplo .env
nano .env                 # preencha DOMINIO
docker compose up -d
```

O Caddy emite e renova o certificado HTTPS sozinho — só exige que o DNS do
domínio já aponte para o IP da VPS antes de subir.

O banco fica no volume `dados`, que sobrevive a redeploys. **Backup é seu
trabalho:**

```bash
# backup diário (coloque no cron da VPS)
docker compose exec -T app cat /app/dados/controladoria.db > backup-$(date +%F).db
```

Sem backup automático, um erro de operação apaga o histórico de prazos do
escritório. Isto não é opcional.

## Opção B — PaaS + Postgres gerenciado

Se preferir Render, Railway, Fly.io ou similar, o disco geralmente é efêmero —
então **Postgres é obrigatório**, não opcional. O código já suporta: basta
definir `DATABASE_URL` e ele troca de banco sozinho, sem alterar mais nada.

```
DATABASE_URL=postgresql://usuario:senha@host:5432/tempestivo
```

Testado nos dois bancos com o mesmo fluxo (`python test_backends.py`).

Vantagem: backup e alta disponibilidade gerenciados. Desvantagem: mais peças e
custo mensal maior.

---

## A captura precisa rodar todo dia — e é isso que justifica a nuvem

O maior ganho de subir para a nuvem não é o painel: é a **captura rodar sozinha
todo dia útil**, independente de o computador do advogado estar ligado. Ela não
usa certificado (DJEN consulta por OAB), então pode viver na nuvem sem problema.

Na VPS, um cron simples resolve:

```bash
# 6h todo dia útil
0 6 * * 1-5 cd /caminho/tempestivo && docker compose exec -T app python -c "import captura_djen,pipeline;pipeline.processar_publicacoes(captura_djen.capturar_publicacoes('61423','GO', __import__('datetime').date.today()-__import__('datetime').timedelta(days=7)))"
```

Ou use o n8n para captura + alerta de WhatsApp, como já conversado.

---

## Segurança — o mínimo antes de colocar dado real

- [ ] **HTTPS obrigatório.** O login manda senha; sem TLS ela viaja aberta.
      O Caddy do compose já resolve.
- [ ] **Senha forte no primeiro usuário.** É o acesso a toda a carteira.
- [ ] **Backup automático testado.** Faça uma restauração de teste; backup que
      nunca foi restaurado não é backup.
- [ ] **`.env` e `.db` fora do Git.** Confira com `git status` antes do push.
- [ ] **Firewall:** só 80/443 abertos. Postgres nunca exposto à internet.

## Limite honesto da autenticação atual

O `auth.py` protege bem o acesso (PBKDF2 com salt, papéis, log de tentativas),
mas é autenticação de aplicação Streamlit: não tem expiração de sessão, 2FA nem
bloqueio por tentativas repetidas. Para um escritório pequeno atrás de HTTPS,
é proporcional. Se um dia virar multi-escritório, isso precisa ser revisto
antes — e aí a conversa é outra (provedor de identidade, 2FA, isolamento de
dados por cliente).

## LGPD e sigilo — o que muda ao sair da máquina dele

Rodando no notebook do advogado, os dados nunca saíram da posse dele. Na nuvem,
você passa a ser **operador** de dados sob sigilo profissional. Na prática:
disco criptografado, backup protegido, acesso restrito, e um acerto por escrito
com ele sobre o que você pode ver e o que faz com os dados. Não é burocracia —
é o que separa um fornecedor sério de um problema para os dois lados.
