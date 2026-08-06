"""
Tela "Documentos" do Tempestivo — contratos, procurações, petições e afins.
"""

import streamlit as st

import documentos
from comum import fmt_longo


def render(ctx):
    USER = ctx["USER"]

    with st.expander("Enviar documento", expanded=False):
        with st.form("novo_doc", clear_on_submit=True):
            arq = st.file_uploader("Arquivo", type=None)
            c1, c2 = st.columns(2)
            categoria = c1.selectbox("Categoria", list(documentos.CATEGORIAS),
                                     format_func=lambda k: documentos.CATEGORIAS[k])
            c3, c4 = st.columns(2)
            cliente = c3.text_input("Cliente (opcional)")
            processo = c4.text_input("Processo (opcional)")
            if st.form_submit_button("Enviar", type="primary"):
                if not arq:
                    st.error("Escolha um arquivo.")
                else:
                    try:
                        documentos.salvar(arq.name, arq.getvalue(), categoria,
                                          cliente, processo, USER["nome"])
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    c1, c2 = st.columns(2)
    f_cliente = c1.text_input("Filtrar por cliente")
    f_processo = c2.text_input("Filtrar por processo")
    docs = documentos.listar(cliente=f_cliente or None, processo=f_processo or None)

    if not docs:
        st.caption("Nenhum documento enviado ainda.")
        return

    for d in docs:
        c1, c2, c3, c4, c5 = st.columns([2.5, 1.2, 1.3, 1, 1])
        c1.write(f"**{d['nome_arquivo']}**")
        c2.write(documentos.CATEGORIAS.get(d["categoria"], d["categoria"]))
        quem = " · ".join(filter(None, [d.get("cliente"), d.get("processo")]))
        c3.write(quem or "—")
        c4.write(f"{d['tamanho']/1024:.0f} KB")
        conteudo = documentos.obter_conteudo(d["id"])
        with c5:
            st.download_button("Baixar", data=conteudo, file_name=d["nome_arquivo"],
                               key=f"dl_{d['id']}")
        cc1, cc2 = st.columns([1, 5])
        cc1.caption(f"Enviado por {d['enviado_por']} em {fmt_longo(d['enviado_em'])}")
        if cc2.button("Excluir", key=f"del_{d['id']}"):
            documentos.excluir(d["id"], USER["nome"]); st.rerun()
        st.divider()
