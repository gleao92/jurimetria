"""
Tela "Financeiro" do Tempestivo — honorários contratados e parcelas a receber.

Só o advogado vê esta tela (checagem em app.py, igual a Ajustes) — dado
financeiro do cliente não é para o apoio administrativo, a menos que o
escritório decida diferente.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import financeiro
from comum import fmt_longo


def render(ctx):
    USER = ctx["USER"]

    r = financeiro.resumo()
    st.markdown(
        f'<div class="situacao">'
        f'<div class="tile-azul"><span class="rot"><span class="ms">payments</span>'
        f'contratado</span><b>R$ {r["contratado"]:,.0f}</b></div>'
        f'<div class="tile-esmeralda"><span class="rot"><span class="ms">'
        f'check_circle</span>recebido</span><b>R$ {r["recebido"]:,.0f}</b></div>'
        f'<div class="tile-ambar"><span class="rot"><span class="ms">schedule</span>'
        f'a receber</span><b>R$ {r["pendente"]:,.0f}</b></div>'
        f'<div class="tile-rosa"><span class="rot"><span class="ms">warning</span>'
        f'atrasado</span><b>R$ {r["atrasado"]:,.0f}</b></div></div>'
        .replace(",", "."), unsafe_allow_html=True)

    with st.expander("Novo contrato de honorário", expanded=False):
        with st.form("novo_honorario", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cliente = c1.text_input("Cliente")
            processo = c2.text_input("Processo (opcional)")
            c3, c4 = st.columns(2)
            tipo = c3.selectbox("Tipo", list(financeiro.TIPOS),
                                format_func=lambda k: financeiro.TIPOS[k])
            valor_total = c4.number_input("Valor total (R$)", min_value=0.0,
                                          step=100.0, format="%.2f")
            descricao = st.text_input("Descrição (opcional)")
            c5, c6, c7 = st.columns(3)
            n_parcelas = c5.number_input("Nº de parcelas", min_value=1,
                                         max_value=60, value=1)
            primeiro_venc = c6.date_input("1º vencimento", value=date.today())
            c7.caption("As demais parcelas vencem no mesmo dia, mês a mês.")
            if st.form_submit_button("Criar contrato", type="primary"):
                if not cliente.strip():
                    st.error("Preencha o cliente.")
                elif valor_total <= 0:
                    st.error("Informe o valor total.")
                else:
                    valor_parcela = round(valor_total / n_parcelas, 2)
                    parcelas = []
                    for i in range(int(n_parcelas)):
                        venc = _somar_meses(primeiro_venc, i)
                        # ajusta a última para fechar o total exato, mesmo com
                        # arredondamento de centavos nas anteriores
                        v = valor_parcela
                        if i == n_parcelas - 1:
                            v = round(valor_total - valor_parcela * (n_parcelas - 1), 2)
                        parcelas.append((v, venc))
                    financeiro.criar_honorario(cliente, processo, tipo,
                                               valor_total, descricao,
                                               USER["nome"], parcelas)
                    st.rerun()

    st.markdown('<div class="secao">Parcelas</div>', unsafe_allow_html=True)
    filtro = st.radio("Filtro", ["Todas", "Pendentes", "Atrasadas", "Pagas"],
                      horizontal=True, label_visibility="collapsed")
    mapa = {"Todas": None, "Pendentes": "pendente",
           "Atrasadas": "atrasado", "Pagas": "pago"}
    parcelas = financeiro.listar_parcelas(status=mapa[filtro])

    if not parcelas:
        st.caption("Nenhuma parcela nesse filtro.")
    else:
        for p in parcelas:
            c1, c2, c3, c4, c5 = st.columns([2, 1.3, 1, 1, 1])
            c1.write(f"**{p['cliente']}**" + (f" · {p['processo']}" if p['processo'] else ""))
            c2.write(f"Parcela {p['numero']} · R$ {p['valor']:,.2f}".replace(",", "."))
            c3.write(fmt_longo(p["vencimento"]) if p["vencimento"] else "—")
            selo = {"pendente": "🟡", "atrasado": "🔴", "pago": "🟢"}.get(p["status"], "")
            c4.write(f"{selo} {financeiro.STATUS_PARCELA.get(p['status'], p['status'])}")
            if p["status"] != "pago":
                if c5.button("Marcar pago", key=f"pg_{p['id']}"):
                    financeiro.marcar_pago(p["id"], USER["nome"]); st.rerun()
            else:
                if c5.button("Desfazer", key=f"dp_{p['id']}"):
                    financeiro.desfazer_pagamento(p["id"], USER["nome"]); st.rerun()
        st.divider()

    with st.expander("Contratos"):
        hs = financeiro.listar_honorarios()
        if hs:
            df = pd.DataFrame([{
                "Cliente": h["cliente"], "Processo": h["processo"] or "—",
                "Tipo": financeiro.TIPOS.get(h["tipo"], h["tipo"]),
                "Valor total": f"R$ {h['valor_total']:,.2f}".replace(",", "."),
                "Descrição": h["descricao"] or "—",
            } for h in hs])
            st.dataframe(df, width="stretch", hide_index=True)
        else:
            st.caption("Nenhum contrato cadastrado ainda.")


def _somar_meses(d: date, n: int) -> date:
    mes = d.month - 1 + n
    ano = d.year + mes // 12
    mes = mes % 12 + 1
    import calendar
    dia = min(d.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)
