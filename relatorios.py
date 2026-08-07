"""
Relatórios — números do escritório, não só a fila do dia.

DIFERENÇA PARA A TELA "HOJE"
"Hoje" responde "o que eu preciso fazer agora". Aqui a pergunta é outra:
"como o escritório está indo" — quantos processos por área, quanto prazo é
cumprido dentro do previsto, quanto falta receber, quantas tarefas cada um
carrega. É o material pra reunião de sócios, não pra rotina diária — por
isso fica em tela própria, e não meio à fila de revisão.

TUDO AQUI É DERIVADO
Nenhuma tabela nova: só leitura das tabelas que os outros módulos já mantêm
(prazos, processos, honorários/parcelas, tarefas). Um relatório que guardasse
seu próprio número corre o risco de divergir do dado de origem — o pior tipo
de relatório é o que mente.
"""

from collections import Counter
from datetime import date

import db
import financeiro
import tarefas as tarefas_mod
from cache_wrap import leitura


def processos_por_area() -> dict:
    con = db.conectar()
    linhas = con.execute("SELECT area FROM processos").fetchall()
    con.close()
    c = Counter((r["area"] if hasattr(r, "keys") else r[0]) or "a_confirmar"
               for r in linhas)
    return dict(c)


def prazos_por_status() -> dict:
    con = db.conectar()
    linhas = con.execute("SELECT status FROM prazos").fetchall()
    con.close()
    c = Counter((r["status"] if hasattr(r, "keys") else r[0]) for r in linhas)
    return dict(c)


def cumprimento_no_prazo() -> dict:
    """Dos prazos cumpridos, quantos foram marcados até a data fatal (ou
    antes) x depois dela. É a métrica que mais importa numa controladoria:
    não "quantos prazos existem", mas "quantos passaram batido"."""
    con = db.conectar()
    linhas = con.execute(
        "SELECT data_fatal, cumprido_em FROM prazos WHERE status='cumprido' "
        "AND data_fatal IS NOT NULL AND cumprido_em IS NOT NULL").fetchall()
    con.close()
    no_prazo = atrasado = 0
    for r in linhas:
        fatal = (r["data_fatal"] if hasattr(r, "keys") else r[0])
        cumprido = (r["cumprido_em"] if hasattr(r, "keys") else r[1])
        try:
            df = date.fromisoformat(str(fatal)[:10])
            dc = date.fromisoformat(str(cumprido)[:10])
        except ValueError:
            continue
        if dc <= df:
            no_prazo += 1
        else:
            atrasado += 1
    total = no_prazo + atrasado
    return {"no_prazo": no_prazo, "atrasado": atrasado, "total": total,
            "taxa": (no_prazo / total * 100) if total else None}


def carga_por_responsavel() -> dict:
    """Tarefas abertas por responsável — quem está sobrecarregado."""
    abertas = tarefas_mod.listar(status="aberta")
    c = Counter((t.get("responsavel") or "sem responsável") for t in abertas)
    return dict(c)


def financeiro_resumo(hoje: date = None) -> dict:
    return financeiro.resumo(hoje)


@leitura(ttl=30)
def painel_geral(hoje: date = None) -> dict:
    """Um dicionário com tudo — o que a vista de relatórios consome de uma
    vez, para não espalhar consultas pela tela."""
    return {
        "processos_por_area": processos_por_area(),
        "prazos_por_status": prazos_por_status(),
        "cumprimento": cumprimento_no_prazo(),
        "carga_por_responsavel": carga_por_responsavel(),
        "financeiro": financeiro_resumo(hoje),
    }
