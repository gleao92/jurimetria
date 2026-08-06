# Deploy na Oracle Cloud (VM no Brasil)

Com o servidor no Brasil, o DJEN volta a aceitar a consulta e a captura roda
dentro do sistema — sem script no PC do escritório, sem proxy.

---

## Passo 0 — Confirme a região da VM

No painel da Oracle: **Compute → Instances → sua instância**. Olhe o campo
*Region* / *Availability Domain*. Você precisa de:

```
sa-saopaulo-1     (São Paulo)
sa-vinhedo-1      (Vinhedo)
```

**Se a sua VM estiver em região dos EUA ou Europa, ela não resolve o 403.**
Nesse caso, crie uma instância nova: o free tier permite escolher a região na
criação, e você pode ter mais de uma instância dentro da cota.

> A região *home* da conta é definida no cadastro e não muda. Se a sua conta
> foi criada com home region estrangeira, você ainda pode criar instâncias
> em São Paulo se ela estiver na lista de regiões inscritas (Subscribed
> Regions, em Governance → Regions).

---

## Passo 1 — Instalar Docker na VM

Conecte por SSH e rode:

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Saia e entre de novo no SSH (para o grupo valer):

```bash
exit
# reconecte
docker --version
```

---

## Passo 2 — A ARMADILHA DA ORACLE: dois firewalls

É aqui que a maioria perde horas. A Oracle tem **duas** camadas de bloqueio, e
abrir só uma não adianta — o site simplesmente não abre, sem mensagem de erro.

### 2a. Firewall da nuvem (console da Oracle)

**Networking → Virtual Cloud Networks → sua VCN → Security Lists → Default**
→ **Add Ingress Rules**:

| Source CIDR | Protocolo | Porta destino |
|-------------|-----------|---------------|
| 0.0.0.0/0   | TCP       | 80            |
| 0.0.0.0/0   | TCP       | 443           |

### 2b. Firewall do sistema operacional (dentro da VM)

As imagens Ubuntu da Oracle vêm com regras de `iptables` que bloqueiam tudo
menos SSH. Isso **não** aparece no console — só dentro da máquina:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# tornar permanente (senão some no reboot)
sudo netfilter-persistent save
```

Se `netfilter-persistent` não existir:

```bash
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

**Confira que valeu:**

```bash
sudo iptables -L INPUT -n --line-numbers | grep -E "80|443"
```

---

## Passo 3 — Levar o código para a VM

```bash
git clone https://github.com/gleao92/jurimetria.git tempestivo
cd tempestivo
```

Se o repositório for privado, o `git clone` vai pedir usuário e senha —
use um *personal access token* do GitHub no lugar da senha, ou torne o
repositório público apenas durante o clone (e volte a privado depois).

---

## Passo 4 — Configurar

```bash
cp .env.exemplo .env
nano .env
```

Preencha:

```
DOMINIO=tempestivo.seudominio.com.br
DATABASE_URL=
```

**Sobre o banco:** deixe `DATABASE_URL` vazio para usar SQLite no volume
persistente do Docker — simples e suficiente para um advogado. Se preferir
continuar no Postgres do Railway, cole a string dele aqui.

**Sobre o domínio:** o Caddy só emite certificado HTTPS para um domínio, não
para um IP puro. Três saídas:

1. **Domínio próprio** (~R$ 40/ano num `.com.br`) — aponte um registro `A`
   para o IP público da VM.
2. **DuckDNS** (grátis) — cria `seunome.duckdns.org` apontando para o IP.
3. **Sem HTTPS por enquanto**, só para testar: comente o serviço `caddy` no
   `docker-compose.yml` e exponha a porta 8501 direto. **Não use assim com
   dados reais de cliente** — o tráfego iria sem criptografia.

---

## Passo 5 — Subir

```bash
docker compose up -d --build
docker compose logs -f app
```

A construção roda os testes do motor de prazos antes de publicar a imagem: se
o cálculo estiver quebrado, o deploy falha em vez de subir errado.

Abra `https://seudominio` — deve aparecer a tela de criar o acesso do advogado.

---

## Passo 6 — A captura diária (agora dentro do servidor)

Este é o ganho principal da migração. Rode na VM:

```bash
docker compose exec app python capturar.py --dias 15
```

Se retornar publicações, o bloqueio geográfico acabou.

Para rodar todo dia útil às 6h, adicione ao cron:

```bash
crontab -e
```

```
0 6 * * 1-5 cd /home/ubuntu/tempestivo && docker compose exec -T app python capturar.py --dias 15 >> /home/ubuntu/captura.log 2>&1
```

A partir daí você pode **desativar a tarefa agendada do Windows** — ela deixa
de ser necessária.

---

## Passo 7 — Backup

O banco vive num volume Docker. Backup diário:

```bash
crontab -e
```

```
30 2 * * * docker run --rm -v tempestivo_dados:/d -v /home/ubuntu/backup:/b alpine tar czf /b/tempestivo-$(date +\%F).tar.gz /d
```

E apague os antigos de tempos em tempos:

```
0 3 * * 0 find /home/ubuntu/backup -name "tempestivo-*.tar.gz" -mtime +30 -delete
```

Backup que nunca foi restaurado não é backup. Teste uma restauração antes de
confiar.

---

## Se o site não abrir

Na ordem, o que checar:

1. `docker compose ps` — os containers estão *Up*?
2. `docker compose logs app` — erro de Python?
3. `curl -I http://localhost:8501` **dentro da VM** — responde? Se sim, o
   problema é firewall, não o app.
4. Firewall: refez os **dois** passos (2a console + 2b iptables)?
5. DNS: `nslookup seudominio` aponta para o IP da VM?

O caso 3 é o mais comum: aplicação funcionando e firewall fechado.

---

## O que fazer com o Railway

Depois que a Oracle estiver estável por alguns dias, desligue o serviço no
Railway para não consumir cota à toa. Não apague antes de confirmar que a
Oracle está de pé — ter os dois no ar por uma semana é barato e evita ficar
sem nada.

---

## VM com 1 GB de RAM (VM.Standard.E2.1.Micro)

Se a sua instância é a `E2.1.Micro` (1 OCPU / 1 GB), ela **funciona**, mas
exige dois cuidados. Sem eles, o `docker compose up --build` costuma ser morto
no meio da instalação por falta de memória — e a mensagem é genérica
("Killed"), sem dizer que faltou RAM.

### 1. Criar swap ANTES de construir (obrigatório)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# confirme
free -h
```

Você deve ver 2 GB em *Swap*. Isso dá folga para a construção da imagem.

### 2. Não rode Postgres na mesma VM

Com 1 GB, Postgres local disputa memória com o app. Duas saídas boas:

- **SQLite no volume** (deixe `DATABASE_URL` vazio no `.env`) — leve, e para
  um advogado é suficiente;
- **Postgres do Railway** — mantenha a `DATABASE_URL` que já funciona lá; o
  banco fica hospedado e a VM só roda o app.

Não descomente o serviço `postgres` do `docker-compose.yml` nesta máquina.

### 3. Se a construção falhar mesmo com swap

Construa sem cache e um passo por vez:

```bash
docker compose build --no-cache app
docker compose up -d
```

E, se ainda assim morrer, remova temporariamente a linha de testes do
`Dockerfile` (`RUN python test_prazos.py && python test_app.py`) — ela é uma
salvaguarda boa, mas é o passo mais pesado da construção. Rode os testes
manualmente depois:

```bash
docker compose exec app python test_prazos.py
```

---

## Alternativa melhor: instância ARM (Ampere A1)

O free tier da Oracle também oferece, **sem custo permanente**:

```
VM.Standard.A1.Flex — até 4 OCPU e 24 GB de RAM
```

É muito mais folgado que a Micro e roda o sistema inteiro com sobra, incluindo
Postgres local se você quiser.

### Como criar, passo a passo

1. **Computação → Instâncias → Criar instância**
2. **Nome**: `tempestivo` (ou o que preferir)
3. Em **Imagem e forma**, clique em **Editar**:
   - **Alterar imagem** → *Canonical Ubuntu* → **24.04** (a lista mostra a
     variante ARM automaticamente depois que você escolher a forma Ampere)
   - **Alterar forma** → aba **Ampere** → `VM.Standard.A1.Flex`
   - Defina **OCPUs** e **memória** (veja a estratégia abaixo)
4. **Rede**: use a VCN que já existe (a mesma da instância atual) e mantenha
   **Atribuir endereço IPv4 público: Sim**
5. **Chaves SSH**: escolha *Gerar par de chaves* e **baixe a chave privada**
   — ela não aparece de novo. Ou cole a pública que você já usa na outra VM,
   assim você acessa as duas com a mesma chave.
6. **Criar**

### A estratégia contra o "Out of host capacity"

A capacidade de Ampere em São Paulo vive esgotada. Você provavelmente vai
receber:

```
Out of host capacity.
```

Isso não é erro seu nem limite da sua conta — é falta de máquina livre na
região naquele momento. O que funciona:

- **Peça menos.** Um pedido de **1 OCPU / 6 GB** é atendido com muito mais
  frequência que 4 OCPU / 24 GB. E 6 GB já é seis vezes o que você tem hoje —
  mais que suficiente para este sistema. Você pode aumentar depois, quando
  houver capacidade, sem recriar a instância.
- **Tente em horários diferentes.** Madrugada e fim de semana costumam ter
  mais folga.
- **Insista.** A capacidade é liberada conforme outras contas apagam
  instâncias; tentar algumas vezes ao longo do dia costuma dar certo.

### Enquanto isso

**Não apague a Micro.** Ela funciona com swap, e é melhor ter o sistema no ar
numa máquina apertada do que esperar uma instância que talvez demore dias para
liberar. Se a A1 sair depois, você migra com calma — é só refazer o clone e o
`docker compose up` na máquina nova.

As imagens usadas (`python:3.12-slim` e `caddy:2-alpine`) têm versão ARM, então
o mesmo `docker-compose.yml` serve nas duas arquiteturas, sem alteração.
