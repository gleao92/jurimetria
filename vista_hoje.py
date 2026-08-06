"""
Tela "Hoje" do Tempestivo.

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

    if revisar:
        st.markdown(
            f'<div class="secao">Fila de revisão · {len(revisar)}'
            f'<span style="text-transform:none;letter-spacing:0;font-weight:400;'
            f'margin-left:.6rem;opacity:.75">'
            f'classificação sugerida — confirme antes de confiar na data</span>'
            f'</div>', unsafe_allow_html=True)
        if not PODE_CONFIRMAR:
            st.caption("A confirmação é do advogado.")

        # Grade de duas colunas: cabe o dobro de prazos sem rolar a tela.
        # O painel de revisão, quando aberto, ocupa a largura inteira embaixo —
        # ele tem campos demais para caber em meia tela.
        aberto = st.session_state.get("abrir")
        for i in range(0, len(revisar), 2):
            colunas = st.columns(2, gap="medium")
            for col, p in zip(colunas, revisar[i:i + 2]):
                num, un, _cor, _selo, dias = urgencia(p)
                with col:
                    st.markdown(estilo.cartao(
                        p, num, un, estilo.tom_por_dias(dias),
                        processo=p["processo"],
                        orgao=p.get("tribunal") or p.get("sistema") or "",
                        fatal=fmt_longo(p["data_fatal"]),
                        interno=fmt(p.get("prazo_interno"))),
                        unsafe_allow_html=True)
                    if st.button("Revisar", key=f"r{p['id']}", width="stretch",
                                 disabled=not PODE_CONFIRMAR):
                        st.session_state["abrir"] = p["id"]
                        st.rerun()

            # painel do prazo aberto nesta faixa, em largura cheia
            for p in revisar[i:i + 2]:
                if aberto == p["id"]:
                    painel.revisar(st, db, p, USER["nome"], prefixo="hoje",
                                   pode_confirmar=PODE_CONFIRMAR)
            st.markdown('<hr class="divisa">', unsafe_allow_html=True)

    urgentes = sorted([p for p in confirmados if urgencia(p)[4] is not None
                       and urgencia(p)[4] <= 5], key=lambda p: d(p["data_fatal"]))
    if urgentes:
        st.markdown(f'<div class="secao">Confirmados, vencendo · {len(urgentes)}</div>',
                    unsafe_allow_html=True)
        for i in range(0, len(urgentes), 2):
            colunas = st.columns(2, gap="medium")
            for col, p in zip(colunas, urgentes[i:i + 2]):
                num, un, _cor, _selo, dias = urgencia(p)
                with col:
                    st.markdown(estilo.cartao(
                        p, num, un, estilo.tom_por_dias(dias),
                        processo=p["processo"],
                        orgao=p.get("tribunal") or p.get("sistema") or "",
                        fatal=fmt_longo(p["data_fatal"]),
                        interno=fmt(p.get("prazo_interno"))),
                        unsafe_allow_html=True)
                    if st.button("Marcar cumprido", key=f"k{p['id']}",
                                 width="stretch"):
                        db.marcar_cumprido(p["id"], USER["nome"]); st.rerun()
            st.markdown('<hr class="divisa">', unsafe_allow_html=True)

    # Compromissos da semana: audiência e reunião não vêm de publicação, mas
    # ocupam o mesmo dia de trabalho. Quem só vê prazos aqui marca uma reunião
    # em cima de uma audiência.
    prox = compromissos.proximos(7)
    if prox:
        st.markdown(f'<div class="secao">Próximos compromissos · {len(prox)}</div>',
                    unsafe_allow_html=True)
        for c in prox:
            cfg = compromissos.TIPOS.get(c["tipo"], {})
            try:
                dia = date.fromisoformat(str(c["data"])[:10])
            except ValueError:
                continue
            falta = (dia - HOJE).days
            quando = ("hoje" if falta == 0 else "amanhã" if falta == 1
                      else f"em {falta} dias")
            k1, k2 = st.columns([6, 1.4])
            with k1:
                st.markdown(estilo.linha(
                    cfg.get("cor", "#1E4D6B"),
                    f'{dia.day:02d}', dia.strftime("%b").lower(),
                    f'{cfg.get("rotulo", "Compromisso")}: {c["titulo"]}',
                    c.get("cliente") or "—",
                    " · ".join(filter(None, [
                        quando, c.get("hora") or "", c.get("local") or "",
                        c.get("processo") or ""]))),
                    unsafe_allow_html=True)
            with k2:
                st.write("")
                if st.button("Abrir", key=f"oc{c['id']}", width="stretch"):
                    st.session_state["sel_compromisso"] = c["id"]
                    st.rerun()
            st.markdown('<hr class="divisa">', unsafe_allow_html=True)

    if not revisar and not urgentes and not prox:
        st.markdown(estilo.vazio(
            "Nada exige ação hoje.",
            "Prazos revisados, com folga, e nenhum compromisso nos próximos dias."),
            unsafe_allow_html=True)


# ══════════════════ Prazos ══════════════════
