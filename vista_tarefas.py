"""
Tela "Tarefas" do Tempestivo — o que fazer além dos prazos do tribunal.
"""

from datetime import date

import streamlit as st

import tarefas as tarefas_mod
import estilo
from comum import fmt_longo


def render(ctx):
    USER = ctx["USER"]

    with st.expander("Nova tarefa", expanded=False):
        with st.form("nova_tarefa", clear_on_submit=True):
            c1, c2 = st.columns([2, 1])
            titulo = c1.text_input("Título", placeholder="Ligar para o cliente")
            prioridade = c2.selectbox("Prioridade", list(tarefas_mod.PRIORIDADES),
                                      index=1,
                                      format_func=lambda k: tarefas_mod.PRIORIDADES[k]["rotulo"])
            c3, c4, c5 = st.columns(3)
            responsavel = c3.text_input("Responsável", value=USER["nome"])
            cliente = c4.text_input("Cliente (opcional)")
            processo = c5.text_input("Processo (opcional)")
            tem_prazo = st.checkbox("Tem data para concluir?")
            prazo = st.date_input("Concluir até", value=date.today()) if tem_prazo else None
            descricao = st.text_area("Descrição (opcional)", height=80)
            if st.form_submit_button("Criar tarefa", type="primary"):
                if not titulo.strip():
                    st.error("Preencha o título.")
                else:
                    tarefas_mod.criar(titulo, descricao, responsavel, cliente,
                                      processo, prazo, prioridade, USER["nome"])
                    st.rerun()

    abertas = tarefas_mod.listar(status="aberta")
    concluidas = tarefas_mod.listar(status="concluida")

    st.markdown(f'<div class="secao">Abertas · {len(abertas)}</div>',
               unsafe_allow_html=True)
    if not abertas:
        st.markdown(estilo.vazio("Nenhuma tarefa aberta.",
                                 "Use \"Nova tarefa\" acima para criar uma."),
                    unsafe_allow_html=True)
    for t in abertas:
        _cartao_tarefa(t, USER)

    if concluidas:
        with st.expander(f"Concluídas · {len(concluidas)}"):
            for t in concluidas:
                _cartao_tarefa(t, USER)


def _cartao_tarefa(t: dict, USER: dict):
    pr = tarefas_mod.PRIORIDADES.get(t.get("prioridade"), {}).get("rotulo", "Normal")
    cor_classe = {"alta": "etq-revisar", "normal": "etq-confirmar",
                  "baixa": "etq-cumprido"}.get(t.get("prioridade"), "etq-confirmar")
    meta = []
    if t.get("responsavel"):
        meta.append(f'<span><span class="ms">person</span>{t["responsavel"]}</span>')
    if t.get("cliente"):
        meta.append(f'<span><span class="ms">badge</span>{t["cliente"]}</span>')
    if t.get("processo"):
        meta.append(f'<span><span class="ms">gavel</span>{t["processo"]}</span>')
    if t.get("prazo"):
        meta.append(f'<span><span class="ms">event</span>Até {fmt_longo(t["prazo"])}</span>')

    st.markdown(f"""
<div class="cartao" style="margin-bottom:.6rem;">
  <div class="etiquetas"><span class="etq {cor_classe}">{pr}</span></div>
  <div class="ato">{t['titulo']}</div>
  {f'<div class="cliente">{t["descricao"]}</div>' if t.get("descricao") else ''}
  <div class="cartao-pe">{''.join(meta)}</div>
</div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 4])
    if t["status"] == "aberta":
        if c1.button("Concluir", key=f"conc_{t['id']}"):
            tarefas_mod.concluir(t["id"], USER["nome"]); st.rerun()
    else:
        if c1.button("Reabrir", key=f"reab_{t['id']}"):
            tarefas_mod.reabrir(t["id"], USER["nome"]); st.rerun()
    if c2.button("Excluir", key=f"exc_{t['id']}"):
        tarefas_mod.excluir(t["id"], USER["nome"]); st.rerun()
