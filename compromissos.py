"""
Compromissos — audiências, reuniões, perícias e lembretes do advogado.

POR QUE ISTO FALTAVA
Até aqui o sistema só recebia do tribunal: publicação entra, prazo sai. Mas a
semana do advogado tem audiência, reunião com cliente e perícia, e nenhum
deles vinha de publicação. Sem isso ele mantém uma segunda agenda no celular
— e uma controladoria que precisa ser conferida contra outra agenda não
controla nada.

AUDIÊNCIA MERECE O MESMO PESO DO PRAZO
Faltar a uma audiência tem consequência processual imediata: revelia, preclusão
da prova, arquivamento. Por isso audiência aparece com o mesmo destaque de uma
data fatal, não como um lembrete qualquer.

DIFERENÇA EM RELAÇÃO AO PRAZO
Prazo nasce de publicação e passa por confirmação do advogado. Compromisso é
criado por ele — não precisa de revisão, mas precisa ser editável e
cancelável, porque audiência remarca e reunião muda de horário.
"""

import hashlib
from datetime import date, datetime, time

import db

TIPOS = {
    "audiencia": {"rotulo": "Audiência", "cor": "#7C2D12", "peso": 1},
    "pericia": {"rotulo": "Perícia", "cor": "#7C2D12", "peso": 1},
    "reuniao": {"rotulo": "Reunião", "cor": "#1E4D6B", "peso": 2},
    "diligencia": {"rotulo": "Diligência", "cor": "#1E4D6B", "peso": 2},
    "lembrete": {"rotulo": "Lembrete", "cor": "#6B6E72", "peso": 3},
}


def init():
    with db.conectar() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS compromissos (
            id TEXT PRIMARY KEY, tipo TEXT, titulo TEXT, data TEXT, hora TEXT,
            duracao_min INTEGER, processo TEXT, cliente TEXT, local TEXT,
            observacao TEXT, criado_por TEXT, criado_em TEXT,
            cancelado INTEGER DEFAULT 0)""")


def _novo_id(*partes) -> str:
    base = "|".join(str(p) for p in partes) + datetime.now().isoformat()
    return "c" + hashlib.sha1(base.encode()).hexdigest()[:14]


def criar(tipo: str, titulo: str, data_: date, hora: str = "",
          duracao_min: int = 60, processo: str = "", cliente: str = "",
          local: str = "", observacao: str = "", autor: str = "") -> str:
    cid = _novo_id(tipo, titulo, data_)
    with db.conectar() as con:
        con.execute("""INSERT INTO compromissos
            (id,tipo,titulo,data,hora,duracao_min,processo,cliente,local,
             observacao,criado_por,criado_em,cancelado)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0)""",
            (cid, tipo, titulo.strip(), str(data_), hora or "",
             int(duracao_min or 60), processo.strip(), cliente.strip(),
             local.strip(), observacao.strip(), autor,
             datetime.now().isoformat(timespec="seconds")))
    db.registrar("compromisso_criado", cid, f"{TIPOS.get(tipo,{}).get('rotulo',tipo)} · {titulo} · {data_}")
    return cid


def atualizar(cid: str, campos: dict, autor: str) -> None:
    permitidos = {"tipo", "titulo", "data", "hora", "duracao_min", "processo",
                  "cliente", "local", "observacao", "cancelado"}
    campos = {k: v for k, v in campos.items() if k in permitidos}
    if not campos:
        return
    with db.conectar() as con:
        con.execute(f"UPDATE compromissos SET "
                    f"{','.join(f'{k}=?' for k in campos)} WHERE id=?",
                    (*campos.values(), cid))
    db.registrar("compromisso_editado", cid, f"por {autor}: {list(campos)}")


def cancelar(cid: str, autor: str) -> None:
    atualizar(cid, {"cancelado": 1}, autor)
    db.registrar("compromisso_cancelado", cid, f"por {autor}")


def listar(desde: date = None, ate: date = None,
           incluir_cancelados: bool = False) -> list[dict]:
    sql = "SELECT * FROM compromissos"
    cond, args = [], []
    if not incluir_cancelados:
        cond.append("cancelado = 0")
    if desde:
        cond.append("data >= ?"); args.append(str(desde))
    if ate:
        cond.append("data <= ?"); args.append(str(ate))
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    sql += " ORDER BY data, hora"
    con = db.conectar()
    r = [dict(x) for x in con.execute(sql, tuple(args)).fetchall()]
    con.close()
    return r


def por_dia(desde: date = None, ate: date = None) -> dict:
    """{data: [compromissos]} — formato que o calendário consome."""
    saida = {}
    for c in listar(desde, ate):
        try:
            d = date.fromisoformat(str(c["data"])[:10])
        except ValueError:
            continue
        saida.setdefault(d, []).append(c)
    for v in saida.values():
        v.sort(key=lambda c: (TIPOS.get(c["tipo"], {}).get("peso", 9),
                              c.get("hora") or "99:99"))
    return saida


def rotulo(c: dict) -> str:
    """Texto curto para a etiqueta do calendário."""
    t = TIPOS.get(c.get("tipo"), {}).get("rotulo", "Compromisso")
    hora = (c.get("hora") or "").strip()
    quem = (c.get("cliente") or "").strip()
    partes = [f"{hora} " if hora else "", t.lower(), " · ",
              c.get("titulo") or quem or ""]
    return "".join(partes).strip(" ·")


def proximos(dias: int = 7) -> list[dict]:
    from datetime import timedelta
    hoje = date.today()
    return listar(hoje, hoje + timedelta(days=dias))
