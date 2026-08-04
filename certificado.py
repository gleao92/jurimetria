"""
Certificado digital (ICP-Brasil / OAB) — LEIA ANTES DE IMPLEMENTAR.

═══════════════════════════════════════════════════════════════════
1) PARA A CONTROLADORIA, VOCÊ PROVAVELMENTE NÃO PRECISA DE CERTIFICADO
═══════════════════════════════════════════════════════════════════
As intimações do ADVOGADO são publicadas no DJEN, que é consultável pelo
NÚMERO DA OAB, sem autenticação. É daí que saem os prazos — todo o núcleo
deste sistema. Certificado só entra em três casos:

  a) Domicílio Judicial Eletrônico — canal das PARTES (os clientes dele),
     não das intimações do advogado. Provavelmente fora do escopo.
  b) Peticionamento / protocolo — assinar e enviar a peça. Fora do piloto.
  c) Ler o interior dos autos (documentos, não só a publicação).

Se o objetivo é "nunca mais perder prazo", (a)-(c) não são necessários.
Adicionar certificado agora multiplica a complexidade sem mover o resultado.

═══════════════════════════════════════════════════════════════════
2) DECISÃO TOMADA: O ADVOGADO USA A3 (TOKEN). CONSEQUÊNCIAS:
═══════════════════════════════════════════════════════════════════
A3 = token USB / cartão. A chave privada NUNCA sai do hardware — isso é
o projeto do dispositivo, não uma limitação de software. Portanto:

  - NÃO existe "subir o certificado para o servidor". Nunca vai existir.
  - Qualquer assinatura exige o token FISICAMENTE plugado na máquina que
    assina, com PIN. Automação desacompanhada é inviável.
  - SaaS em nuvem que protocola peça sozinho está DESCARTADO para este
    cliente. Se um dia houver peticionamento, ele roda na máquina dele.
  - O código A1 abaixo (item 4) NÃO SE APLICA aqui. Ficou só como
    referência caso apareça um cliente com A1.

>>> MAS ISSO NÃO TRAVA A CONTROLADORIA <<<
A captura de publicações é feita pelo DJEN, por número de OAB, SEM
certificado. Ou seja: a parte que gera valor (prazos) independe do A3.
A restrição do A3 só alcança protocolo/assinatura, que está fora do
escopo. Ver "Decisões de arquitetura" no README.

═══════════════════════════════════════════════════════════════════
3) NÃO GUARDE O CERTIFICADO DO ADVOGADO NO SEU SERVIDOR
═══════════════════════════════════════════════════════════════════
O certificado é PESSOAL e INTRANSFERÍVEL — atos praticados com ele são
imputados a ele. Você segurar o .pfx + senha significa poder assinar
petição em nome dele. Isso é:
  - risco para ele (responsabilidade por ato que não praticou),
  - risco para você (se vazar, o problema é seu),
  - e conflita com as regras de uso do próprio certificado.

O jeito certo: o certificado FICA COM O ADVOGADO. Ou o sistema roda na
máquina dele (Streamlit local, que é como está hoje — e é um argumento
a favor de manter local), ou a assinatura acontece do lado dele e o
servidor só recebe o resultado. Se um dia for para nuvem, essa decisão
precisa ser revista com cuidado.

═══════════════════════════════════════════════════════════════════
4) CÓDIGO (A1) — NÃO TESTADO
═══════════════════════════════════════════════════════════════════
Autenticação mútua TLS com .pfx. Requer:  pip install requests-pkcs12
A senha vem de variável de ambiente, nunca do código.
"""

import os

CERT_PATH = os.environ.get("CERT_PFX_PATH")      # ex.: C:/certificados/adv.pfx
CERT_SENHA = os.environ.get("CERT_PFX_SENHA")    # NUNCA escreva a senha aqui


def disponivel() -> bool:
    return bool(CERT_PATH and CERT_SENHA and os.path.exists(CERT_PATH))


def get_sessao():
    """Devolve uma sessão HTTP autenticada por certificado A1 (mTLS).

    NÃO TESTADO — o endpoint e o formato de autenticação precisam ser
    confirmados na documentação do serviço que você for consumir.
    """
    if not disponivel():
        raise RuntimeError(
            "Certificado A1 não configurado. Defina as variáveis de ambiente "
            "CERT_PFX_PATH e CERT_PFX_SENHA. Se o advogado usa A3 (token), "
            "esta abordagem não se aplica — veja o item 2 no topo do arquivo."
        )
    try:
        from requests_pkcs12 import Pkcs12Adapter
        import requests
    except ImportError as e:
        raise RuntimeError("pip install requests-pkcs12") from e

    s = requests.Session()
    s.mount("https://", Pkcs12Adapter(pkcs12_filename=CERT_PATH,
                                      pkcs12_password=CERT_SENHA))
    return s


def info_certificado() -> dict:
    """Lê titular e validade do .pfx — útil para avisar antes de vencer.
    Um certificado vencido sem aviso derruba a automação em silêncio."""
    if not disponivel():
        return {"configurado": False}
    from cryptography.hazmat.primitives.serialization import pkcs12
    with open(CERT_PATH, "rb") as f:
        _, cert, _ = pkcs12.load_key_and_certificates(f.read(), CERT_SENHA.encode())
    return {
        "configurado": True,
        "titular": cert.subject.rfc4514_string(),
        "valido_ate": cert.not_valid_after_utc.date().isoformat(),
    }
