"""
Tela "Sala de Reunião" do Tempestivo — grava a reunião, guarda o áudio.

SEM TRANSCRIÇÃO, DE PROPÓSITO
Transcrever áudio decentemente exige ou uma API paga (Whisper etc., cobrada
por minuto) ou um modelo local pesado — inviável no servidor modesto do
Railway sem travar a reunião de verdade. Decisão: só grava e guarda,
vinculado a cliente/processo. Se precisar de transcrição, é feita depois,
fora do sistema, com a gravação já em mãos.

REUSA documentos.py
Uma gravação é só mais um arquivo — em vez de outra tabela, entra em
`documentos` com categoria 'gravacao'. Menos código, mesma trilha de
auditoria e o mesmo limite de tamanho que já protegem os outros arquivos.
"""

import streamlit as st

import documentos
from comum import fmt_longo


def render(ctx):
    USER = ctx["USER"]

    st.markdown('<div class="secao">Gravar</div>', unsafe_allow_html=True)
    st.caption("Grave pelo microfone do navegador. Ao terminar, dê um título "
               "e salve — a gravação fica guardada como um documento, sem "
               "transcrição automática.")

    audio = st.audio_input("Gravar reunião")

    if audio is not None:
        with st.form("salvar_gravacao"):
            c1, c2 = st.columns(2)
            titulo = c1.text_input("Título da reunião",
                                   placeholder="Reunião com o cliente — 06/08")
            cliente = c2.text_input("Cliente (opcional)")
            processo = st.text_input("Processo (opcional)")
            if st.form_submit_button("Salvar gravação", type="primary"):
                if not titulo.strip():
                    st.error("Dê um título para a gravação.")
                else:
                    try:
                        nome = f"{titulo.strip()}.wav"
                        documentos.salvar(nome, audio.getvalue(), "gravacao",
                                          cliente, processo, USER["nome"])
                        st.success("Gravação salva.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    st.markdown('<div class="secao">Gravações salvas</div>', unsafe_allow_html=True)
    gravacoes = documentos.listar(categoria="gravacao")
    if not gravacoes:
        st.caption("Nenhuma gravação ainda.")
        return

    for g in gravacoes:
        quem = " · ".join(filter(None, [g.get("cliente"), g.get("processo")]))
        st.markdown(f"**{g['nome_arquivo'].rsplit('.', 1)[0]}**"
                   + (f" — {quem}" if quem else ""))
        conteudo = documentos.obter_conteudo(g["id"])
        st.audio(conteudo)
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.caption(f"Gravado por {g['enviado_por']} em {fmt_longo(g['enviado_em'])} "
                  f"· {g['tamanho']/1024/1024:.1f} MB")
        c2.download_button("Baixar", data=conteudo, file_name=g["nome_arquivo"],
                           key=f"dlg_{g['id']}")
        if c3.button("Excluir", key=f"delg_{g['id']}"):
            documentos.excluir(g["id"], USER["nome"]); st.rerun()
        st.divider()
