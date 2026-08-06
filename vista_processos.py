"""
Tela "Processos" do Tempestivo.

Extraída do app.py, que passara de 700 linhas e concentrava todas as telas —
qualquer ajuste numa aba exigia navegar o arquivo inteiro e arriscava mexer
noutra. Cada vista agora recebe o contexto de que precisa e nada mais.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db, pipeline, captura, configuracao, carteira, estilo, agenda, calendario, painel
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

    con = db.conectar()
    procs = [dict(r) for r in con.execute("SELECT * FROM processos")]
    con.close()

    if procs:
        faltam = [p for p in procs if (p.get("area") or "") == "a_confirmar"]

        if faltam and PODE_CONFIRMAR:
            st.warning(f"**{len(faltam)} processos sem área definida.** Sem ela "
                       "o sistema usa a contagem mais curta — protege, mas "
                       "adianta as datas. Defina abaixo e os prazos se "
                       "recalculam.")
            c1, c2, c3 = st.columns([1.2, 1.2, 2])
            if c1.button(f"Marcar os {len(faltam)} como cível", width="stretch"):
                con = db.conectar()
                for p in faltam:
                    con.execute("UPDATE processos SET area='civel' WHERE numero=?",
                                (p["numero"],))
                con.commit(); con.close()
                db.registrar("area_em_lote", USER["nome"], f"{len(faltam)} -> civel")
                pipeline.recalcular_pendentes()
                st.rerun()
            if c2.button("Marcar todos como criminal", width="stretch"):
                con = db.conectar()
                for p in faltam:
                    con.execute("UPDATE processos SET area='criminal' WHERE numero=?",
                                (p["numero"],))
                con.commit(); con.close()
                db.registrar("area_em_lote", USER["nome"], f"{len(faltam)} -> criminal")
                pipeline.recalcular_pendentes()
                st.rerun()
            c3.caption("Ou edite um a um na tabela abaixo.")

        so_pendentes = st.toggle("Mostrar só os que precisam de atenção",
                                 value=bool(faltam)) if faltam else False
        lista = faltam if so_pendentes else procs

        base = pd.DataFrame([{
            "Processo": p["numero"],
            "Cliente": p.get("cliente") or "",
            "Área": {"civel": "cível", "criminal": "criminal"}.get(
                p.get("area"), "a confirmar"),
            "Órgão": p.get("tribunal") or "",
        } for p in lista])

        editado = st.data_editor(
            base, width="stretch", hide_index=True, key="edproc",
            disabled=["Processo", "Órgão"] if PODE_CONFIRMAR
                     else ["Processo", "Cliente", "Área", "Órgão"],
            column_config={
                "Área": st.column_config.SelectboxColumn(
                    "Área", options=["a confirmar", "cível", "criminal"],
                    required=True,
                    help="Cível conta em dias úteis; criminal, em dias corridos."),
                "Cliente": st.column_config.TextColumn(
                    "Cliente", help="Preencha ou use 'Completar dados pelo tribunal'."),
            })

        if PODE_CONFIRMAR and st.button("Salvar alterações", type="primary"):
            volta = {"a confirmar": "a_confirmar", "cível": "civel",
                     "criminal": "criminal"}
            antes = {p["numero"]: p for p in lista}
            con = db.conectar()
            n = 0
            for _, linha in editado.iterrows():
                num = linha["Processo"]
                nova_area = volta.get(linha["Área"], "a_confirmar")
                novo_cli = (linha["Cliente"] or "").strip()
                velho = antes.get(num, {})
                if (nova_area != (velho.get("area") or "a_confirmar")
                        or novo_cli != (velho.get("cliente") or "")):
                    con.execute("UPDATE processos SET area=?, cliente=? WHERE numero=?",
                                (nova_area, novo_cli, num))
                    n += 1
            con.commit(); con.close()
            if n:
                db.registrar("processos_editados", USER["nome"], f"{n} alterados")
                r = pipeline.recalcular_pendentes()
                st.success(f"{n} processos atualizados · "
                           f"{r['atualizados']} prazos recalculados.")
            else:
                st.info("Nada mudou.")
            st.rerun()
    else:
        st.markdown(estilo.vazio("Carteira vazia.",
                                 "Importe a lista de processos abaixo."),
                    unsafe_allow_html=True)

    if PODE_CONFIRMAR:
        with st.expander("Importar processos", expanded=not procs):
            st.caption("Cole a lista — reconheço os números no meio de qualquer "
                       "texto. Uma vez só; depois é automático.")
            txt = st.text_area("Lista", height=120, key="imp",
                               label_visibility="collapsed",
                               placeholder="1002345-67.2026.8.09.0051")
            nums = carteira.extrair_numeros(txt) if txt else []
            c1, c2 = st.columns([2, 1])
            if txt:
                c1.caption(f"**{len(nums)}** processos reconhecidos")
            a_pad = c2.selectbox("Área", ["a_confirmar", "civel", "criminal"],
                                 format_func=lambda x: {
                                     "a_confirmar": "Definir depois",
                                     "civel": "Cíveis", "criminal": "Criminais"}[x])
            if st.button("Importar", type="primary", disabled=not nums):
                r = carteira.importar(nums, a_pad)
                db.registrar("carteira_importada", USER["nome"], str(r))
                st.rerun()
            if procs:
                st.divider()
                if st.button("Completar dados pelo tribunal"):
                    with st.spinner("Consultando..."):
                        r = carteira.enriquecer_via_mni([p["numero"] for p in procs])
                    st.success(f"{r['ok']} completados · {r['erros']} com erro")


# ══════════════════ Ajustes ══════════════════
