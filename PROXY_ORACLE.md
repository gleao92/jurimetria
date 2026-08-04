# Captura na nuvem com IP brasileiro (Oracle Cloud — São Paulo)

## O problema que isto resolve

O DJEN (consulta de publicações por OAB) recusa requisições vindas de IP fora
do Brasil — retorna `403 Forbidden`. O Railway roda em servidores
norte-americanos/europeus, então a captura que roda lá não consegue consultar o
tribunal.

A solução: um proxy HTTP autenticado numa VM em São Paulo. O app no Railway
faz a requisição passando pelo proxy; o proxy (com IP brasileiro) consulta o
DJEN e devolve a resposta. Para o app é transparente — a biblioteca `requests`
do Python honra as variáveis `HTTP_PROXY`/`HTTPS_PROXY` automaticamente.

## Por que Oracle Cloud

- **Always Free de verdade** — a VM `VM.Standard.E2.1.Micro` é sempre
  gratuita, sem limite de 12 meses (diferente da AWS).
- **Região em São Paulo** (`sa-saopaulo-1`) → IP brasileiro.
- 1 GB de RAM e 1 vCPU sobra para um Squid.

> Se você já tem uma VM em outro provedor com IP brasileiro (AWS sa-east-1,
> DigitalOcean SP, etc.), o mesmo passo a passo serve — só muda o painel.

---

## Passo a passo

### 1. Criar a VM na Oracle Cloud

1. Em **cloud.oracle.com**, confirme a região no topo: **Brazil East (Sao Paulo)**.
2. **Compute → Instances → Create Instance**:
   - **Name:** `tempestivo-proxy`
   - **Image:** Oracle Linux 9 (default)
   - **Shape:** `VM.Standard.E2.1.Micro` (Always Free)
   - **SSH keys:** marque **"Save private key"** e **"Save public key"** —
     baixa dois arquivos. **Guarde a chave privada** (`.key`); sem ela você
     não entra na VM.
   - Crie.
3. Anote o **IP público** que aparece na lista de instâncias após ela ficar
   verde ("Executando").

### 2. Abrir a porta 3128 na VCN

1. Na página da instância → aba **Rede** → clique no **VCN/Subnet**.
2. Vá até o **Security List** que ela usa → **Adicionar Regras de Ingresso**:
   - Origem: `0.0.0.0/0`
   - Protocolo: TCP, Porta destino: `3128`
   - Salvar.

### 3. Conectar à VM e instalar o Docker

No seu terminal (na pasta onde baixou a chave privada):

```bash
chmod 600 ssh-key-*.key
ssh -i ssh-key-*.key opc@IP_DA_VPS
```

Dentro da VM (prompt vira `[opc@tempestivo-proxy ~]$`):

```bash
sudo dnf install -y dnf-utils
sudo dnf config-manager --enable ol9_addons
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker opc
exit        # saia e entre de novo pro grupo pegar
```

Reconecte com o mesmo `ssh` de antes.

### 4. Baixar os arquivos do proxy e subir o Squid

```bash
git clone https://github.com/gleao92/jurimetria.git
cd jurimetria/proxy

# criar a senha de acesso ao proxy (troque SUASENHA por uma senha forte)
docker run --rm httpd:2.4 htpasswd -nb tempestivo SUASENHA > passwords
chmod 644 passwords

# subir o Squid
docker run -d --name tempestivo-proxy --restart unless-stopped \
  -p 3128:3128 \
  -v $PWD/squid.conf:/etc/squid/squid.conf:ro \
  -v $PWD/passwords:/etc/squid/passwords:ro \
  ubuntu/squid:latest

docker logs -f tempestivo-proxy     # ctrl+c pra sair
```

### 5. Liberar a porta no firewall interno da VM (iptables)

A Oracle tem **dois** firewalls: o Security List da VCN (passo 2) e o
`iptables` dentro da VM. Sem este passo, a porta fica bloqueada mesmo com o
Security List aberto:

```bash
sudo iptables -I INPUT 6 -p tcp --dport 3128 -j ACCEPT
sudo sh -c 'iptables-save > /etc/iptables/rules.v4'
```

### 6. Testar da sua máquina

```bash
curl -x http://tempestivo:SUASENHA@IP_DA_VPS:3128 \
  https://comunicaapi.pje.jus.br/api/v1/comunicacao?numeroOab=61423
```

Se vier JSON (mesmo com erro de parâmetro) em vez de `403`, funcionou.

### 7. Configurar o Railway

No serviço do Tempestivo no Railway → aba **Variables**, adicione (troque
`IP_DA_VPS` e `SUASENHA`):

```
HTTP_PROXY=http://tempestivo:SUASENHA@IP_DA_VPS:3128
HTTPS_PROXY=http://tempestivo:SUASENHA@IP_DA_VPS:3128
NO_PROXY=.supabase.co,localhost,127.0.0.1
```

O `NO_PROXY` é importante: o Supabase e o localhost **não** podem passar pelo
proxy (só o tráfego para os tribunais). Redeploy e teste a captura — o `403`
some.

---

## Manutenção

- **Ver se está no ar:** `docker ps` mostra o container; `docker logs
  tempestivo-proxy` mostra o tráfego passando.
- **Reiniciar:** `docker restart tempestivo-proxy`.
- **Trocar a senha:** gere um novo `passwords` e `docker restart`.
- **IP mudou:** se a VM reiniciar e o IP público mudar, atualize
  `HTTP_PROXY`/`HTTPS_PROXY` no Railway. Para IP fixo, aloque um
  **Elastic IP** na Oracle (também gratuito no Always Free).

## Custo

Zero. A `VM.Standard.E2.1.Micro` está no Always Free da Oracle. O tráfego
do proxy é mínimo (só consultas ao DJEN, em texto).
