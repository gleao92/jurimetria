"""
Tarefas — o que a equipe precisa fazer e não nasce de publicação nem de prazo.

POR QUE ISTO É SEPARADO DE PRAZO E DE COMPROMISSO
Prazo nasce do tribunal e tem data fatal jurídica. Compromisso é um horário
marcado (audiência, reunião). Tarefa é o resto do trabalho do escritório —
"ligar pro cliente", "juntar documento", "revisar contrato" — que não tem
consequência processual se atrasar um dia, mas que também não pode viver só
na cabeça de alguém. Misturar isso com prazo faria a fila de prazos (que
precisa ser levada a sério com o peso máximo) competir por atenção com coisa
de prioridade menor.
"""

import hashlib
from datetime import date, datetime

import db
from cache_wrap import leitura, limpar

PRIORIDADES = {"alta": {"rotulo": "Alta", "peso": 0},
               "normal": {"rotulo": "Normal", "peso": 1},
               "baixa": {"rotulo": "Baixa", "peso": 2}}


def init():
    with db.conectar() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS tarefas (
            id TEXT PRIMARY KEY, titulo TEXT, descricao TEXT,
            responsavel TEXT, cliente TEXT, processo TEXT,
            prazo TEXT, prioridade TEXT DEFAULT 'normal',
            status TEXT DEFAULT 'aberta',
            criado_por TEXT, criado_em TEXT, concluido_em TEXT)""")


def _novo_id(*partes) -> str:
    base = "|".join(str(p) for p in partes) + datetime.now().isoformat()
    return "t" + hashlib.sha1(base.encode()).hexdigest()[:14]


def criar(titulo: str, descricao: str = "", responsavel: str = "",
          cliente: str = "", processo: str = "", prazo: date = None,
          prioridade: str = "normal", autor: str = "") -> str:
    tid = _novo_id(titulo, responsavel, prazo)
    with db.conectar() as con:
        con.execute("""INSERT INTO tarefas
            (id,titulo,descricao,responsavel,cliente,processo,prazo,
             prioridade,status,criado_por,criado_em)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (tid, titulo.strip(), descricao.strip(), responsavel.strip(),
             cliente.strip(), processo.strip(), str(prazo) if prazo else None,
             prioridade if prioridade in PRIORIDADES else "normal",
             "aberta", autor, datetime.now().isoformat(timespec="seconds")))
    db.registrar("tarefa_criada", tid, f"{titulo} · resp. {responsavel or '—'}")
    limpar()
    return tid


def atualizar(tid: str, campos: dict, autor: str) -> None:
    permitidos = {"titulo", "descricao", "responsavel", "cliente", "processo",
                  "prazo", "prioridade", "status"}
    campos = {k: v for k, v in campos.items() if k in permitidos}
    if not campos:
        return
    with db.conectar() as con:
        con.execute(f"UPDATE tarefas SET "
                    f"{','.join(f'{k}=?' for k in campos)} WHERE id=?",
                    (*campos.values(), tid))
    db.registrar("tarefa_editada", tid, f"por {autor}: {list(campos)}")
    limpar()


def concluir(tid: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("UPDATE tarefas SET status='concluida', concluido_em=? WHERE id=?",
                    (datetime.now().isoformat(timespec="seconds"), tid))
    db.registrar("tarefa_concluida", tid, f"por {autor}")
    limpar()


def reabrir(tid: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("UPDATE tarefas SET status='aberta', concluido_em=NULL WHERE id=?",
                    (tid,))
    db.registrar("tarefa_reaberta", tid, f"por {autor}")
    limpar()


def excluir(tid: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("DELETE FROM tarefas WHERE id=?", (tid,))
    db.registrar("tarefa_excluida", tid, f"por {autor}")
    limpar()


@leitura()
def listar(status: str = None, responsavel: str = None) -> list[dict]:
    sql = "SELECT * FROM tarefas"
    cond, args = [], []
    if status:
        cond.append("status = ?"); args.append(status)
    if responsavel:
        cond.append("responsavel = ?"); args.append(responsavel)
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    con = db.conectar()
    linhas = [dict(r) for r in con.execute(sql, tuple(args)).fetchall()]
    con.close()
    linhas.sort(key=lambda t: (
        t["status"] != "aberta",
        PRIORIDADES.get(t.get("prioridade"), {}).get("peso", 1),
        t.get("prazo") or "9999-99-99"))
    return linhas


def contagem_abertas(responsavel: str = None) -> int:
    return len(listar(status="aberta", responsavel=responsavel))
