# Proxy brasileiro para o Tempestivo

O ComunicaAPI do PJe (`comunicaapi.pje.jus.br`) bloqueia IPs fora do Brasil.
O Railway nao tem regiao no Brasil (so US, Europa e Asia). Este proxy roda numa
VPS em Sao Paulo e o jurimetria (no Railway) o usa como saida para as capturas.

O `captura_djen.py` usa `requests.get(...)`, que le `HTTP_PROXY`/`HTTPS_PROXY`
automaticamente. Logo, **nao precisa mexer no codigo**.

## 1) Subir a VPS (Sao Paulo)
- DigitalOcean droplet "Sao Paulo", ou AWS EC2 sa-east-1, ou outro provedor BR.
- Instale o Docker + Docker Compose.

## 2) Gerar senha (na VPS)
```bash
docker run --rm httpd:2.4 htpasswd -nb tempestivo SUASENHA > passwords
# use a senha que quiser no lugar de SUASENHA
```

## 3) Subir o proxy
```bash
docker compose up -d
```

## 4) No Railway (servico jurimetria) -> Variables
```
HTTP_PROXY=http://tempestivo:SUASENHA@IP_DA_VPS:3128
HTTPS_PROXY=http://tempestivo:SUASENHA@IP_DA_VPS:3128
NO_PROXY=.supabase.co,localhost,127.0.0.1
```

Pronto. As chamadas ao PJe/DJEN saem com IP brasileiro; Supabase e acesso interno
continuam diretos (NO_PROXY).
