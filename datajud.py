"""
Integracao com a API Publica do DataJud (CNJ) para o Tempestivo.

Camada ADITIVA: nao altera nada do fluxo DJEN existente.

Regra de ouro
-------------
DataJud NAO conta prazo. E base estatistica, alimentada em lote pelos
tribunais, com atraso variavel, e sem semantica de data de publicacao ou
disponibilizacao. Movimento do DataJud vira cartao informativo na timeline.
Prazo continua nascendo exclusivamente da publicacao do DJEN.

Ambiente
--------
DATAJUD_API_KEY  chave publica do DPJ/CNJ. Publicada na wiki e alteravel a
                 qualquer momento -> manter em env var, nunca no codigo.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

BASE_URL = "https://api-publica.datajud.cnj.jus.br"
TIMEOUT = 30
PAUSA_ENTRE_CHAMADAS = 0.6  # cortesia com a API; evita 429 em lote


class DataJudError(Exception):
    pass


class TribunalSemCobertura(DataJudError):
    """Segmento existe mas o CNJ nao expoe alias para ele."""


# --------------------------------------------------------------------------
# Numeracao unica -> alias do tribunal
# NNNNNNN-DD.AAAA.J.TR.OOOO  (7 seq + 2 dv + 4 ano + 1 J + 2 TR + 4 origem)
# --------------------------------------------------------------------------

_UF_POR_TR = {
    "01": "ac", "02": "al", "03": "ap", "04": "am", "05": "ba", "06": "ce",
    "07": "df", "08": "es", "09": "go", "10": "ma", "11": "mt", "12": "ms",
    "13": "mg", "14": "pa", "15": "pb", "16": "pr", "17": "pe", "18": "pi",
    "19": "rj", "20": "rn", "21": "rs", "22": "ro", "23": "rr", "24": "sc",
    "25": "se", "26": "sp", "27": "to",
}


@dataclass(frozen=True)
class Processo:
    numero: str          # 20 digitos, sem formatacao
    ano: str
    segmento: str        # J
    tribunal: str        # TR
    origem: str          # OOOO

    @property
    def formatado(self) -> str:
        n = self.numero
        return f"{n[0:7]}-{n[7:9]}.{n[9:13]}.{n[13]}.{n[14:16]}.{n[16:20]}"


def parse_numero(numero: str) -> Processo:
    digitos = re.sub(r"\D", "", numero or "")
    if len(digitos) != 20:
        raise DataJudError(f"Numero CNJ deve ter 20 digitos, recebido {len(digitos)}.")
    return Processo(
        numero=digitos,
        ano=digitos[9:13],
        segmento=digitos[13],
        tribunal=digitos[14:16],
        origem=digitos[16:20],
    )


def resolver_alias(numero: str) -> str:
    """
    Devolve o alias do endpoint (ex.: 'api_publica_tjgo').

    Cobertura verificada: estadual (J=8), federal (J=4), trabalhista (J=5) e
    superiores. Eleitoral e militar variam de formato entre versoes da wiki --
    conferir em datajud-wiki.cnj.jus.br/api-publica/endpoints antes de habilitar.
    """
    p = parse_numero(numero)
    j, tr = p.segmento, p.tribunal

    if j == "1":
        raise TribunalSemCobertura("STF nao possui alias na API Publica.")
    if j == "3":
        return "api_publica_stj"

    if j == "4":  # Justica Federal
        n = int(tr)
        if 1 <= n <= 6:
            return f"api_publica_trf{n}"
        raise TribunalSemCobertura(f"TRF {tr} desconhecido.")

    if j == "5":  # Justica do Trabalho
        if tr == "00":
            return "api_publica_tst"
        n = int(tr)
        if 1 <= n <= 24:
            return f"api_publica_trt{n}"
        raise TribunalSemCobertura(f"TRT {tr} desconhecido.")

    if j == "8":  # Justica Estadual
        uf = _UF_POR_TR.get(tr)
        if not uf:
            raise TribunalSemCobertura(f"TR estadual {tr} desconhecido.")
        return f"api_publica_tj{uf}"

    raise TribunalSemCobertura(
        f"Segmento J={j} sem alias mapeado. Conferir a wiki do DataJud."
    )


# --------------------------------------------------------------------------
# Cliente
# --------------------------------------------------------------------------

@dataclass
class Movimento:
    codigo: int
    nome: str
    data_hora: datetime
    complementos: list = field(default_factory=list)

    def chave(self, numero_processo: str) -> str:
        """Identidade estavel para deduplicacao entre sincronizacoes."""
        return f"{numero_processo}:{self.codigo}:{self.data_hora.isoformat()}"


@dataclass
class Capa:
    numero: str
    tribunal: str
    grau: str
    classe: str
    assuntos: list
    orgao_julgador: str
    data_ajuizamento: datetime | None
    ultima_atualizacao: datetime | None
    movimentos: list


class DataJudClient:
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key or os.environ.get("DATAJUD_API_KEY")
        if not self.api_key:
            raise DataJudError("DATAJUD_API_KEY ausente no ambiente.")
        self.session = session or requests.Session()

    def _post(self, alias: str, corpo: dict) -> dict:
        url = f"{BASE_URL}/{alias}/_search"
        cabecalho = {
            "Authorization": f"APIKey {self.api_key}",
            "Content-Type": "application/json",
        }
        for tentativa in range(3):
            resp = self.session.post(url, json=corpo, headers=cabecalho, timeout=TIMEOUT)
            if resp.status_code == 401:
                raise DataJudError(
                    "401 no DataJud. A chave publica do CNJ mudou -- "
                    "atualizar DATAJUD_API_KEY a partir da wiki."
                )
            if resp.status_code in (429, 502, 503, 504):
                time.sleep(2 ** tentativa)
                continue
            if not resp.ok:
                raise DataJudError(f"DataJud {resp.status_code}: {resp.text[:300]}")
            return resp.json()
        raise DataJudError("DataJud indisponivel apos 3 tentativas.")

    def consultar(self, numero: str) -> Capa | None:
        """Consulta um processo pelo numero CNJ. None se nao encontrado."""
        p = parse_numero(numero)
        alias = resolver_alias(numero)
        dados = self._post(alias, {"query": {"match": {"numeroProcesso": p.numero}}, "size": 1})

        hits = dados.get("hits", {}).get("hits", [])
        if not hits:
            return None
        return _montar_capa(hits[0].get("_source", {}), p.numero)


def _data(valor) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None


def _montar_capa(src: dict, numero: str) -> Capa:
    movimentos = []
    for m in src.get("movimentos") or []:
        quando = _data(m.get("dataHora"))
        if quando is None:
            continue
        movimentos.append(
            Movimento(
                codigo=int(m.get("codigo") or 0),
                nome=(m.get("nome") or "").strip(),
                data_hora=quando,
                complementos=m.get("complementosTabelados") or [],
            )
        )
    movimentos.sort(key=lambda x: x.data_hora, reverse=True)

    classe = src.get("classe") or {}
    orgao = src.get("orgaoJulgador") or {}

    return Capa(
        numero=numero,
        tribunal=src.get("tribunal") or "",
        grau=src.get("grau") or "",
        classe=(classe.get("nome") or "").strip(),
        assuntos=[a.get("nome") for a in (src.get("assuntos") or []) if a.get("nome")],
        orgao_julgador=(orgao.get("nome") or "").strip(),
        data_ajuizamento=_data(src.get("dataAjuizamento")),
        ultima_atualizacao=_data(src.get("dataHoraUltimaAtualizacao")),
        movimentos=movimentos,
    )


# --------------------------------------------------------------------------
# Relevancia (TPU) -- o que merece aparecer para o advogado
# --------------------------------------------------------------------------

MOVIMENTOS_RELEVANTES = {
    51: "Audiencia designada",
    123: "Concluso ao juiz",
    132: "Ato ordinatorio praticado",
    193: "Baixa definitiva",
    196: "Arquivamento",
    246: "Desarquivamento",
    848: "Peticao juntada",
    861: "Sentenca",
    966: "Distribuicao",
    11383: "Decisao",
    12265: "Despacho",
}

# Movimentos que costumam anteceder intimacao. NAO geram prazo -- geram um
# aviso de "fique de olho, deve pingar publicacao no DJEN".
MOVIMENTOS_PRE_INTIMACAO = {861, 11383, 12265, 51}


def classificar(mov: Movimento) -> str:
    if mov.codigo in MOVIMENTOS_PRE_INTIMACAO:
        return "atencao"
    if mov.codigo in MOVIMENTOS_RELEVANTES:
        return "relevante"
    return "rotina"


# --------------------------------------------------------------------------
# Sincronizacao
# --------------------------------------------------------------------------

JANELA_RECONCILIACAO_HORAS = 72


def sincronizar_processo(supabase, client: DataJudClient, processo_id, numero: str) -> dict:
    """
    Busca no DataJud e grava apenas o que e novo.

    Idempotente: rodar duas vezes seguidas nao duplica nada.
    Retorna resumo {'novos': n, 'atencao': n, 'status': str}.
    """
    try:
        capa = client.consultar(numero)
    except TribunalSemCobertura as e:
        return {"novos": 0, "atencao": 0, "status": f"sem_cobertura: {e}"}

    if capa is None:
        return {"novos": 0, "atencao": 0, "status": "nao_encontrado"}

    existentes = {
        r["chave"]
        for r in (
            supabase.table("datajud_movimentos")
            .select("chave")
            .eq("processo_id", str(processo_id))
            .execute()
            .data
            or []
        )
    }

    novos, atencao = [], 0
    for mov in capa.movimentos:
        chave = mov.chave(capa.numero)
        if chave in existentes:
            continue
        rotulo = classificar(mov)
        if rotulo == "atencao":
            atencao += 1
        novos.append(
            {
                "processo_id": str(processo_id),
                "chave": chave,
                "codigo": mov.codigo,
                "nome": mov.nome,
                "data_hora": mov.data_hora.isoformat(),
                "relevancia": rotulo,
                "complementos": mov.complementos,
            }
        )

    if novos:
        supabase.table("datajud_movimentos").insert(novos).execute()

    supabase.table("datajud_capas").upsert(
        {
            "processo_id": str(processo_id),
            "numero": capa.numero,
            "tribunal": capa.tribunal,
            "grau": capa.grau,
            "classe": capa.classe,
            "assuntos": capa.assuntos,
            "orgao_julgador": capa.orgao_julgador,
            "data_ajuizamento": capa.data_ajuizamento.isoformat() if capa.data_ajuizamento else None,
            "ultima_atualizacao": capa.ultima_atualizacao.isoformat() if capa.ultima_atualizacao else None,
            "sincronizado_em": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="processo_id",
    ).execute()

    return {"novos": len(novos), "atencao": atencao, "status": "ok"}


def sincronizar_lote(supabase, processos: list[dict], client: DataJudClient | None = None) -> dict:
    """
    processos: [{'id': ..., 'numero': ...}] -- vem do SEU cadastro atual.
    Rodar uma vez por dia, fora do horario de pico. O DataJud nao e tempo real;
    sincronizar de hora em hora so gasta quota sem trazer novidade.
    """
    client = client or DataJudClient()
    resumo = {"processos": 0, "novos": 0, "atencao": 0, "erros": []}

    for p in processos:
        try:
            r = sincronizar_processo(supabase, client, p["id"], p["numero"])
            resumo["processos"] += 1
            resumo["novos"] += r["novos"]
            resumo["atencao"] += r["atencao"]
        except DataJudError as e:
            resumo["erros"].append({"numero": p.get("numero"), "erro": str(e)})
        time.sleep(PAUSA_ENTRE_CHAMADAS)

    return resumo


# --------------------------------------------------------------------------
# Timeline unificada -- e aqui que o advogado para de abrir tribunal
# --------------------------------------------------------------------------

def timeline(supabase, processo_id) -> list[dict]:
    """
    Funde publicacoes do DJEN (fonte de prazo) com movimentos do DataJud
    (contexto), ordenado do mais recente para o mais antigo.

    ADAPTAR: trocar 'publicacoes' e os nomes de coluna pelo seu schema atual.
    """
    pubs = (
        supabase.table("publicacoes")            # <-- sua tabela do DJEN
        .select("id, data_publicacao, texto, prazo_id")
        .eq("processo_id", str(processo_id))
        .execute()
        .data
        or []
    )
    movs = (
        supabase.table("datajud_movimentos")
        .select("id, data_hora, nome, codigo, relevancia")
        .eq("processo_id", str(processo_id))
        .execute()
        .data
        or []
    )

    itens = [
        {
            "fonte": "djen",
            "quando": p["data_publicacao"],
            "titulo": "Publicacao no DJEN",
            "detalhe": (p.get("texto") or "")[:280],
            "conta_prazo": True,
            "ref": p["id"],
        }
        for p in pubs
    ] + [
        {
            "fonte": "datajud",
            "quando": m["data_hora"],
            "titulo": m["nome"],
            "detalhe": f"Movimento CNJ {m['codigo']}",
            "conta_prazo": False,
            "ref": m["id"],
        }
        for m in movs
    ]

    itens.sort(key=lambda x: x["quando"] or "", reverse=True)
    return itens


def pendencias_de_intimacao(supabase, escritorio_id, horas: int = JANELA_RECONCILIACAO_HORAS) -> list[dict]:
    """
    Movimentos 'atencao' sem publicacao correspondente no DJEN dentro da janela.

    Nao e prazo. E uma lista de conferencia: sentenca movimentada ha 3 dias sem
    publicacao pode ser atraso normal de diario, ou pode ser intimacao que
    entrou por outro canal. Quem decide e o advogado.
    """
    corte = datetime.now(timezone.utc).timestamp() - horas * 3600
    resp = (
        supabase.table("datajud_movimentos")
        .select("id, processo_id, data_hora, nome, codigo")
        .eq("relevancia", "atencao")
        .order("data_hora", desc=True)
        .limit(200)
        .execute()
    )
    candidatos = [
        m for m in (resp.data or [])
        if (_data(m["data_hora"]) or datetime.now(timezone.utc)).timestamp() >= corte
    ]

    pendentes = []
    for m in candidatos:
        tem_pub = (
            supabase.table("publicacoes")        # <-- sua tabela do DJEN
            .select("id")
            .eq("processo_id", m["processo_id"])
            .gte("data_publicacao", m["data_hora"][:10])
            .limit(1)
            .execute()
            .data
        )
        if not tem_pub:
            pendentes.append(m)
    return pendentes
