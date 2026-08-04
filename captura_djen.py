"""
Captura via DJEN (Diário de Justiça Eletrônico Nacional).

CONFIRMADO EM PRODUÇÃO: responde para a OAB 61423/GO — 63 publicações em 60
dias, tribunais TJGO e TRF1. Não exige certificado nem senha.

Endpoint (o mesmo que comunica.pje.jus.br usa por baixo):
    https://comunicaapi.pje.jus.br/api/v1/comunicacao

>>> ATENÇÃO AOS NOMES DE CAMPO <<<
A API não é uniforme entre tribunais e versões. Em vez de fixar um nome, cada
campo abaixo tenta várias grafias conhecidas. Se algo vier vazio, rode
`amostra()` e acrescente o nome que aparecer no retorno real.

Um campo mapeado errado aqui não dá erro — dá prazo silenciosamente errado.
Por isso existe a função amostra(): confira ANTES de ingerir.
"""

from datetime import date, timedelta

import requests

from modelos import Publicacao

BASE = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
TIMEOUT = 45

# Cabeçalhos de navegador. A API do DJEN é pública, mas serviços do Judiciário
# costumam filtrar requisição sem identificação — e o padrão do requests
# ("python-requests/2.x") é o primeiro a ser barrado.
CABECALHOS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/122.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Referer": "https://comunica.pje.jus.br/",
    "Origin": "https://comunica.pje.jus.br",
}


class DJENBloqueado(Exception):
    """A API recusou a consulta (403). Quase sempre é origem do pedido."""


def _proxies():
    """Proxy opcional para a consulta sair por um IP brasileiro.

    O DJEN recusa pedido vindo de servidor no exterior. Em vez de mover o
    sistema inteiro, dá para rotear SÓ esta requisição por uma máquina no
    Brasil. Configure a variável de ambiente:

        DJEN_PROXY=http://usuario:senha@host:porta
        DJEN_PROXY=socks5://usuario:senha@host:1080

    Para socks5 é preciso instalar:  pip install "requests[socks]"

    Sem a variável, a consulta sai direto (comportamento normal).
    """
    import os
    p = os.environ.get("DJEN_PROXY", "").strip()
    return {"http": p, "https": p} if p else None


def _pega(item: dict, *nomes, padrao=None):
    """Primeiro nome de campo que existir e não estiver vazio."""
    for n in nomes:
        v = item.get(n)
        if v not in (None, "", []):
            return v
    return padrao


def _parse_data(v):
    if not v:
        return None
    s = str(v).strip()
    try:
        if len(s) >= 8 and s[:8].isdigit() and "-" not in s[:8]:
            return date(int(s[:4]), int(s[4:6]), int(s[6:8]))   # AAAAMMDD
        return date.fromisoformat(s[:10])                        # ISO
    except Exception:
        return None


def _buscar_bruto(oab: str, uf: str, desde: date, ate: date = None,
                  paginas_max: int = 20) -> list[dict]:
    """Retorna os itens CRUS da API, paginando até acabar."""
    ate = ate or date.today()
    itens, pagina = [], 1
    while pagina <= paginas_max:
        params = {
            "numeroOab": oab, "ufOab": uf,
            "dataDisponibilizacaoInicio": desde.isoformat(),
            "dataDisponibilizacaoFim": ate.isoformat(),
            "itensPorPagina": 100, "pagina": pagina,
        }
        r = requests.get(BASE, params=params, timeout=TIMEOUT,
                         headers=CABECALHOS, proxies=_proxies())
        if r.status_code == 403:
            # 403 quase nunca é a OAB errada — é a ORIGEM do pedido sendo
            # recusada. O DJEN é público, mas serviços do Judiciário brasileiro
            # costumam barrar IP de datacenter no exterior. A mesma consulta
            # funciona a partir de uma conexão no Brasil.
            raise DJENBloqueado(
                "O DJEN recusou a consulta (403). A OAB e o período estão "
                "corretos — o que ele recusou foi a ORIGEM do pedido.\n\n"
                "Isto acontece quando o sistema roda num servidor fora do "
                "Brasil (o seu está em Oregon, EUA). O DJEN aceita a mesma "
                "consulta partindo de uma conexão brasileira.\n\n"
                "Saídas possíveis:\n"
                "• hospedar o sistema num servidor no Brasil;\n"
                "• rodar a captura no computador do escritório e deixar só o "
                "painel na nuvem (veja capturar.py);\n"
                "• rotear só esta consulta por um proxy brasileiro, definindo "
                "a variável DJEN_PROXY."
                + (" (Há um proxy configurado e ele também foi recusado — "
                   "provavelmente é IP de datacenter, que costuma estar na "
                   "mesma lista de bloqueio.)" if _proxies() else ""))
        r.raise_for_status()
        dados = r.json()
        lote = (dados if isinstance(dados, list)
                else dados.get("items") or dados.get("content")
                or dados.get("data") or [])
        if not lote:
            break
        itens += lote
        if len(lote) < 100:
            break
        pagina += 1
    return itens


def normalizar(item: dict) -> Publicacao:
    """Converte um item cru da API num objeto Publicacao já validado.

    Devolve um objeto tipado, não um dicionário: assim um campo com nome
    errado falha na construção, e não vira `None` silencioso que depois vira
    data errada. O objeto ainda aceita acesso por chave, para o restante do
    código continuar igual.
    """
    return Publicacao(
        processo=_pega(item, "numeroProcesso", "numero_processo",
                       "numeroprocessocommascara", "numeroProcessoMascara",
                       "numero", padrao=""),
        sistema=_pega(item, "siglaTribunal", "tribunal", "siglatribunal",
                      padrao="?"),
        data_disponibilizacao=_pega(item, "dataDisponibilizacao",
                                    "data_disponibilizacao",
                                    "datadisponibilizacao", "dataEnvio"),
        teor=_pega(item, "texto", "teor", "textoComunicacao",
                   "conteudo", "textoDocumento", padrao=""),
        # tipoComunicacao costuma nomear o ato direto — ajuda a classificação
        tipo=_pega(item, "tipoComunicacao", "tipoDocumento", "nomeClasse",
                   padrao=""),
        orgao=_pega(item, "nomeOrgao", "orgao", "siglaOrgao", padrao=""),
        # O DJEN entrega a data em que a comunicação SE CONSIDERA publicada (o
        # primeiro dia útil após a disponibilização, art. 224 §2º do CPC). O
        # cálculo não pode avançar esse dia de novo. Marca na origem, em vez de
        # depender de casar a sigla do tribunal com uma lista.
        tipo_data="publicacao",
    )


def capturar_publicacoes(oab: str, uf: str, desde: date,
                         ate: date = None) -> list[dict]:
    return [normalizar(i) for i in _buscar_bruto(oab, uf, desde, ate)]


def amostra(oab: str, uf: str, dias: int = 60) -> dict:
    """Diagnóstico: mostra os nomes de campo REAIS e checa o mapeamento.

    Use antes de ingerir. Um campo vazio aqui = prazo errado depois.
    """
    desde = date.today() - timedelta(days=dias)
    brutos = _buscar_bruto(oab, uf, desde)
    if not brutos:
        return {"total": 0}
    norm = [normalizar(i) for i in brutos]
    vazios = {c: sum(1 for n in norm if not n[c])
              for c in ("processo", "teor", "sistema")}
    incompletas = sum(1 for n in norm if not n.completa)
    return {
        "total": len(brutos),
        "campos_da_api": sorted(brutos[0].keys()),
        "tribunais": sorted({n["sistema"] for n in norm}),
        "orgaos": sorted({n["orgao"] for n in norm if n["orgao"]})[:25],
        "tipos": sorted({n["tipo"] for n in norm if n["tipo"]})[:25],
        "processos": sorted({n["processo"] for n in norm if n["processo"]}),
        "campos_vazios": vazios,
        "incompletas": incompletas,
        "exemplo_bruto": brutos[0],
    }


if __name__ == "__main__":
    import json, os
    a = amostra(os.environ.get("OAB_NUMERO", "61423"),
                os.environ.get("OAB_UF", "GO"))
    print(json.dumps({k: v for k, v in a.items() if k != "exemplo_bruto"},
                     indent=2, ensure_ascii=False, default=str))
