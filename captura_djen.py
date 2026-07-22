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
        r = requests.get(BASE, params=params, timeout=TIMEOUT)
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
