"""
Tela "Prazos" do Tempestivo.

Extraída do app.py, que passara de 700 linhas e concentrava todas as telas —
qualquer ajuste numa aba exigia navegar o arquivo inteiro e arriscava mexer
noutra. Cada vista agora recebe o contexto de que precisa e nada mais.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db, pipeline, captura, configuracao, carteira, estilo, agenda, calendario, painel, compromissos
from comum import d, fmt, fmt_longo, urgencia, rotulo_area, DIAS_PT, MESES_PT
from prazos import (calcular_prazo, dias_uteis_entre, eh_dia_util,
                    nome_do_feriado, feriados_do_ano, area_para_calculo,
                    MARGEM_SEGURANCA_DIAS)
from config import PAPEIS


def render(ctx):
    """ctx traz: USER, PODE_CONFIRMAR, HOJE, FONTE_CONECTADA e as listas."""
    USER = ctx["USER"]
    PODE_CONFIRMAR = ctx["PODE_CONFIRMAR"]
    HOJE = ctx["HOJE"]
    FONTE_CONECTADA = ctx["FONTE_CONECTADA"]
    ativos = ctx.get("ativos", [])
    revisar = ctx.get("revisar", [])
    confirmados = ctx.get("confirmados", [])

    todos = db.listar_prazos()
    if not todos:
        st.markdown(estilo.vazio("Nenhum prazo registrado.",
                                 "Busque publicações na barra lateral."),
                    unsafe_allow_html=True)
    else:
        f1, f2 = st.columns([1, 2])
        stf = f1.multiselect("Situação", db.STATUS,
                             default=["pendente_revisao", "confirmado"])
        cli = sorted({p.get("cliente") or "não identificado" for p in todos})
        cf = f2.multiselect("Cliente", cli, default=cli)
        linhas = [{
            "Restam": urgencia(p)[0], "Ato": p["ato"],
            "Cliente": p.get("cliente") or "—",
            "Área": {"a_confirmar": "a confirmar", "civel": "cível",
                     "criminal": "criminal"}.get(p.get("area"), "—"),
            "Processo": p["processo"],
            "Interno": fmt(p["prazo_interno"]), "Fatal": fmt(p["data_fatal"]),
            "Situação": p["status"].replace("_", " "),
            "Confirmado por": p.get("confirmado_por") or "—",
        } for p in todos if p["status"] in stf
          and (p.get("cliente") or "não identificado") in cf]
        st.dataframe(pd.DataFrame(linhas), width="stretch", hide_index=True)
        st.markdown('<div class="secao">Levar para a agenda</div>',
                    unsafe_allow_html=True)
        r = agenda.resumo(todos)
        if r["prazos"]:
            st.caption(f"{r['prazos']} prazos confirmados viram {r['eventos']} "
                       "compromissos: um para preparar a peça (com folga) e outro "
                       "na data fatal, ambos com alarme. Importe no Google "
                       "Agenda, Outlook ou no calendário do celular.")
            c1, c2 = st.columns([1, 2])
            _comps = compromissos.listar()
            c1.download_button("Baixar agenda (.ics)",
                               agenda.gerar_ics(todos, comps=_comps).encode("utf-8"),
                               f"prazos_{HOJE}.ics", "text/calendar",
                               type="primary", width="stretch")
            c2.download_button("Baixar planilha (.csv)",
                               pd.DataFrame(linhas).to_csv(index=False).encode("utf-8"),
                               f"prazos_{HOJE}.csv", "text/csv", width="stretch")
            st.caption("Entram os prazos confirmados e todos os compromissos "
                       "(audiências, reuniões). Prazo sugerido automaticamente, "
                       "sem sua revisão, não vira compromisso no calendário.")
        else:
            st.caption("Nenhum prazo confirmado ainda. Confirme os prazos em "
                       "Hoje e eles ficam prontos para a agenda.")


# ══════════════════ Processos ══════════════════
