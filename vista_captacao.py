"""
Tela "Captação" do Tempestivo — funil de clientes em potencial, em quadro.
"""

import streamlit as st

import captacao
from comum import fmt_longo


def render(ctx):
    USER = ctx["USER"]

    resumo = captacao.funil_resumo()
    taxa = f"{resumo['taxa_conversao']:.0f}%" if resumo["taxa_conversao"] is not None else "—"
    st.markdown(
        f'<div class="situacao">'
        f'<div class="tile-azul"><span class="rot"><span class="ms">groups</span>'
        f'em aberto</span><b>{sum(v for k, v in resumo["contagem"].items() if k not in ("ganho", "perdido"))}</b></div>'
        f'<div class="tile-esmeralda"><span class="rot"><span class="ms">'
        f'trending_up</span>taxa de conversão</span><b>{taxa}</b></div>'
        f'<div class="tile-ambar"><span class="rot"><span class="ms">payments</span>'
        f'em negociação</span><b>R$ {resumo["valor_aberto"]:,.0f}</b></div>'
        f'<div class="tile-rosa"><span class="rot"><span class="ms">cancel</span>'
        f'perdidos</span><b>{resumo["contagem"]["perdido"]}</b></div></div>'
        .replace(",", "."), unsafe_allow_html=True)

    with st.expander("Novo contato", expanded=False):
        with st.form("novo_lead", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome")
            contato = c2.text_input("Telefone/e-mail")
            c3, c4, c5 = st.columns(3)
            origem = c3.selectbox("Origem", list(captacao.ORIGENS),
                                  format_func=lambda k: captacao.ORIGENS[k])
            area = c4.text_input("Área de interesse")
            valor = c5.number_input("Valor estimado (R$)", min_value=0.0, step=100.0)
            responsavel = st.text_input("Responsável", value=USER["nome"])
            obs = st.text_area("Observação", height=70)
            if st.form_submit_button("Adicionar ao funil", type="primary"):
                if not nome.strip():
                    st.error("Preencha o nome.")
                else:
                    captacao.criar(nome, contato, origem, area, valor,
                                   responsavel, obs, USER["nome"])
                    st.rerun()

    st.markdown('<div class="secao">Funil</div>', unsafe_allow_html=True)
    quadro = captacao.por_estagio()
    colunas = st.columns(len(captacao.ESTAGIOS))
    for col, estagio in zip(colunas, captacao.ESTAGIOS):
        with col:
            st.markdown(f'<div class="grupo-barra" style="margin-top:0">'
                       f'{captacao.ROTULOS_ESTAGIO[estagio]} · {len(quadro[estagio])}'
                       f'</div>', unsafe_allow_html=True)
            for lead in quadro[estagio]:
                _cartao_lead(lead, estagio)


def _cartao_lead(lead: dict, estagio_atual: str):
    valor = f"R$ {lead['valor_estimado']:,.0f}".replace(",", ".") \
        if lead.get("valor_estimado") else ""
    st.markdown(f"""
<div class="cartao" style="margin-bottom:.6rem; padding:.7rem .8rem .6rem;">
  <div class="ato" style="font-size:.86rem;">{lead['nome']}</div>
  <div class="cliente">{lead.get('contato') or '—'}</div>
  {f'<div class="cliente" style="opacity:.6">{valor}</div>' if valor else ''}
</div>""", unsafe_allow_html=True)

    opcoes = [e for e in captacao.ESTAGIOS if e != estagio_atual]
    destino = st.selectbox(
        "Mover para", opcoes, key=f"mv_{lead['id']}",
        format_func=lambda e: captacao.ROTULOS_ESTAGIO[e],
        label_visibility="collapsed")
    motivo = ""
    if destino == "perdido":
        motivo = st.text_input("Motivo da perda", key=f"mot_{lead['id']}",
                               label_visibility="collapsed",
                               placeholder="Motivo da perda (opcional)")
    if st.button("Mover", key=f"btnmv_{lead['id']}", width="stretch"):
        captacao.mover_estagio(lead["id"], destino, st.session_state["user"]["nome"], motivo)
        st.rerun()
