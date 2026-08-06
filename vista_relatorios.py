"""
Tela "Relatórios" do Tempestivo — números do escritório, não a fila do dia.
"""

import pandas as pd
import streamlit as st

import relatorios
import estilo


def render(ctx):
    dados = relatorios.painel_geral()

    cump = dados["cumprimento"]
    fin = dados["financeiro"]
    taxa = f"{cump['taxa']:.0f}%" if cump["taxa"] is not None else "—"
    st.markdown(
        f'<div class="situacao">'
        f'<div class="tile-esmeralda"><span class="rot"><span class="ms">'
        f'verified</span>cumpridos no prazo</span><b>{taxa}</b></div>'
        f'<div class="tile-azul"><span class="rot"><span class="ms">payments</span>'
        f'contratado</span><b>R$ {fin["contratado"]:,.0f}</b></div>'
        f'<div class="tile-ambar"><span class="rot"><span class="ms">schedule</span>'
        f'a receber</span><b>R$ {fin["pendente"]:,.0f}</b></div>'
        f'<div class="tile-rosa"><span class="rot"><span class="ms">warning</span>'
        f'financeiro atrasado</span><b>R$ {fin["atrasado"]:,.0f}</b></div></div>'
        .replace(",", "."), unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="secao">Processos por área</div>',
                   unsafe_allow_html=True)
        area = dados["processos_por_area"]
        if area:
            rot = {"civel": "Cível", "criminal": "Criminal",
                  "a_confirmar": "A confirmar"}
            df = pd.DataFrame({"Processos": area}).rename(index=rot)
            st.bar_chart(df)
        else:
            st.caption("Nenhum processo cadastrado ainda.")

    with col2:
        st.markdown('<div class="secao">Prazos por situação</div>',
                   unsafe_allow_html=True)
        status = dados["prazos_por_status"]
        if status:
            rot = {"pendente_revisao": "A revisar", "confirmado": "Confirmado",
                  "cumprido": "Cumprido", "arquivado": "Arquivado"}
            df = pd.DataFrame({"Prazos": status}).rename(index=rot)
            st.bar_chart(df)
        else:
            st.caption("Nenhum prazo cadastrado ainda.")

    st.markdown('<div class="secao">Cumprimento de prazo</div>',
               unsafe_allow_html=True)
    if cump["total"]:
        st.write(f"Dos **{cump['total']}** prazos cumpridos, "
                f"**{cump['no_prazo']}** foram dentro da data fatal e "
                f"**{cump['atrasado']}** depois dela.")
    else:
        st.caption("Ainda não há prazos cumpridos para medir.")

    st.markdown('<div class="secao">Carga de tarefas por responsável</div>',
               unsafe_allow_html=True)
    carga = dados["carga_por_responsavel"]
    if carga:
        df = pd.DataFrame({"Tarefas abertas": carga})
        st.bar_chart(df)
    else:
        st.caption("Nenhuma tarefa aberta no momento.")
