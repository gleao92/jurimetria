"""
Financeiro — honorários contratados e parcelas a receber.

ESCOPO DELIBERADAMENTE PEQUENO
Isto não é um ERP contábil: não emite nota fiscal, não concilia banco, não
calcula imposto. É o mínimo que evita a pergunta "quanto esse cliente me
deve e quando vence": um contrato de honorário por cliente/processo, dividido
em parcelas, cada uma paga ou não. Se o escritório crescer a ponto de
precisar de conciliação bancária de verdade, a ferramenta certa é um sistema
financeiro — não este.

POR QUE PARCELA É TABELA SEPARADA DE HONORÁRIO
Um contrato normalmente vira várias parcelas (entrada + N mensais, ou
percentual de êxito pago de uma vez). Guardar tudo numa linha só forçaria
"5 datas de vencimento" dentro de um campo de texto — impossível somar
"quanto vence este mês" sem parsear string. Parcela própria permite
"SELECT soma onde vencimento <= hoje e status='pendente'" direto no banco.
"""

import hashlib
from datetime import date, datetime

import db
from cache_wrap import leitura, limpar

TIPOS = {"fixo": "Valor fixo", "exito": "Êxito", "mensal": "Mensalidade"}
STATUS_PARCELA = {"pendente": "Pendente", "pago": "Pago", "atrasado": "Atrasado"}


def init():
    with db.conectar() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS honorarios (
            id TEXT PRIMARY KEY, cliente TEXT, processo TEXT, tipo TEXT,
            valor_total REAL, descricao TEXT,
            criado_por TEXT, criado_em TEXT, cancelado INTEGER DEFAULT 0)""")
        con.execute("""CREATE TABLE IF NOT EXISTS parcelas (
            id TEXT PRIMARY KEY, honorario_id TEXT, numero INTEGER,
            valor REAL, vencimento TEXT, status TEXT DEFAULT 'pendente',
            pago_em TEXT, criado_em TEXT)""")


def _novo_id(prefixo, *partes) -> str:
    base = "|".join(str(p) for p in partes) + datetime.now().isoformat()
    return prefixo + hashlib.sha1(base.encode()).hexdigest()[:14]


def criar_honorario(cliente: str, processo: str, tipo: str, valor_total: float,
                    descricao: str = "", autor: str = "",
                    parcelas: list[tuple[float, date]] = None) -> str:
    """`parcelas`: lista de (valor, vencimento). Vazia = pagamento único, sem
    data — só entra no total contratado, sem cobrança agendada."""
    hid = _novo_id("h", cliente, processo, valor_total)
    agora = datetime.now().isoformat(timespec="seconds")
    with db.conectar() as con:
        con.execute("""INSERT INTO honorarios
            (id,cliente,processo,tipo,valor_total,descricao,criado_por,
             criado_em,cancelado) VALUES (?,?,?,?,?,?,?,?,0)""",
            (hid, cliente.strip(), processo.strip(),
             tipo if tipo in TIPOS else "fixo", float(valor_total),
             descricao.strip(), autor, agora))
        for i, (valor, venc) in enumerate(parcelas or [], start=1):
            pid = _novo_id("p", hid, i)
            con.execute("""INSERT INTO parcelas
                (id,honorario_id,numero,valor,vencimento,status,criado_em)
                VALUES (?,?,?,?,?,?,?)""",
                (pid, hid, i, float(valor), str(venc), "pendente", agora))
    db.registrar("honorario_criado", hid,
                 f"{cliente} · {processo} · R$ {valor_total:.2f} · "
                 f"{len(parcelas or [])} parcela(s)")
    limpar()
    return hid


def cancelar_honorario(hid: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("UPDATE honorarios SET cancelado=1 WHERE id=?", (hid,))
    db.registrar("honorario_cancelado", hid, f"por {autor}")
    limpar()


def marcar_pago(pid: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("UPDATE parcelas SET status='pago', pago_em=? WHERE id=?",
                    (datetime.now().isoformat(timespec="seconds"), pid))
    db.registrar("parcela_paga", pid, f"por {autor}")
    limpar()


def desfazer_pagamento(pid: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("UPDATE parcelas SET status='pendente', pago_em=NULL WHERE id=?",
                    (pid,))
    db.registrar("parcela_reaberta", pid, f"por {autor}")
    limpar()


def _atualizar_atrasadas(hoje: date) -> None:
    """Parcela pendente com vencimento passado vira 'atrasado' — cálculo, não
    marcação manual: se ninguém abrir o painel por uma semana, a próxima
    consulta já recalcula certo."""
    with db.conectar() as con:
        con.execute("""UPDATE parcelas SET status='atrasado'
                       WHERE status='pendente' AND vencimento < ?""",
                    (str(hoje),))


@leitura()
def listar_honorarios(incluir_cancelados: bool = False) -> list[dict]:
    con = db.conectar()
    sql = "SELECT * FROM honorarios"
    if not incluir_cancelados:
        sql += " WHERE cancelado = 0"
    sql += " ORDER BY criado_em DESC"
    r = [dict(x) for x in con.execute(sql).fetchall()]
    con.close()
    return r


@leitura()
def listar_parcelas(honorario_id: str = None, status: str = None,
                    hoje: date = None) -> list[dict]:
    _atualizar_atrasadas(hoje or date.today())
    con = db.conectar()
    sql = """SELECT pa.*, h.cliente, h.processo, h.tipo AS tipo_honorario
             FROM parcelas pa JOIN honorarios h ON h.id = pa.honorario_id
             WHERE h.cancelado = 0"""
    args = []
    if honorario_id:
        sql += " AND pa.honorario_id = ?"; args.append(honorario_id)
    if status:
        sql += " AND pa.status = ?"; args.append(status)
    sql += " ORDER BY pa.vencimento IS NULL, pa.vencimento"
    r = [dict(x) for x in con.execute(sql, tuple(args)).fetchall()]
    con.close()
    return r


@leitura()
def resumo(hoje: date = None) -> dict:
    """Números que respondem 'como está o caixa': contratado, recebido,
    pendente e atrasado — o mínimo que um advogado olha antes de decidir se
    pode assumir um caso novo sem receber adiantado."""
    hoje = hoje or date.today()
    honorarios = listar_honorarios()
    parcelas = listar_parcelas(hoje=hoje)
    contratado = sum(h["valor_total"] for h in honorarios)
    recebido = sum(p["valor"] for p in parcelas if p["status"] == "pago")
    pendente = sum(p["valor"] for p in parcelas if p["status"] == "pendente")
    atrasado = sum(p["valor"] for p in parcelas if p["status"] == "atrasado")
    return {"contratado": contratado, "recebido": recebido,
            "pendente": pendente, "atrasado": atrasado,
            "qtd_atrasadas": len([p for p in parcelas if p["status"] == "atrasado"])}
