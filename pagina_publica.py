"""
Página pública de captação — a porta de entrada de quem ainda não é cliente.

SEM LOGIN, DE PROPÓSITO
Todo o resto do sistema exige login porque lida com dado de cliente já
existente. Esta página é o oposto: quem acessa ainda não tem nada aqui — é
justamente quem o escritório quer que consiga entrar em contato sem
fricção. Fica atrás de `?pagina=contato` na URL (ver app.py), não do login.

O QUE ELA FAZ E O QUE ELA NÃO FAZ
Não anuncia, não compra tráfego, não aparece sozinha no Google — isso é
marketing, de fora do sistema. O que ela faz: quando alguém chega até aqui
(por um link que você divulgou, um QR code, um anúncio que você pagou), dá
duas formas de contato imediato — WhatsApp direto ou um formulário curto —
e QUALQUER uma das duas cai automaticamente na aba Captação, sem digitar de
novo.
"""

from urllib.parse import quote

import streamlit as st

import captacao
from config import (NOME_SISTEMA, NOME_ESCRITORIO, WHATSAPP_NUMERO,
                    AREAS_ATUACAO, CIDADE_REGIAO)


def _link_whatsapp(mensagem: str = "") -> str:
    numero = "".join(c for c in WHATSAPP_NUMERO if c.isdigit())
    texto = quote(mensagem or f"Olá! Vim pelo site do {NOME_ESCRITORIO} "
                             "e gostaria de falar com um advogado.")
    return f"https://wa.me/{numero}?text={texto}"


def render():
    numero_ok = WHATSAPP_NUMERO.replace("5562900000000", "") != ""
    st.markdown(f"""
<div class="publica-hero">
  <div class="publica-marca"><span class="ms">balance</span>{NOME_ESCRITORIO}</div>
  <h1>Precisa de um advogado?</h1>
  <p>Atendimento em {', '.join(AREAS_ATUACAO)} — {CIDADE_REGIAO}.
     Fale agora e receba retorno o mais rápido possível.</p>
</div>""", unsafe_allow_html=True)

    if WHATSAPP_NUMERO == "5562900000000":
        st.warning("**Número de WhatsApp ainda não configurado** — edite "
                   "`WHATSAPP_NUMERO` em `config.py` antes de divulgar este "
                   "link. Por enquanto o botão abaixo não vai funcionar de "
                   "verdade.")

    c1, c2 = st.columns([1, 1.3], gap="large")

    with c1:
        st.markdown('<div class="secao">Fale direto pelo WhatsApp</div>',
                   unsafe_allow_html=True)
        st.link_button("💬 Chamar no WhatsApp agora", _link_whatsapp(),
                       type="primary", width="stretch")
        st.caption("Abre uma conversa direta — sem cadastro, sem espera.")

    with c2:
        st.markdown('<div class="secao">Ou prefere que a gente te chame?</div>',
                   unsafe_allow_html=True)
        with st.form("contato_publico", clear_on_submit=True):
            nome = st.text_input("Seu nome")
            telefone = st.text_input("WhatsApp para retorno",
                                     placeholder="(62) 90000-0000")
            area = st.selectbox("Sobre o que você precisa falar?",
                                AREAS_ATUACAO + ["Outro assunto"])
            mensagem = st.text_area("Conte rapidamente o que aconteceu",
                                    height=90)
            enviado = st.form_submit_button("Solicitar contato", type="primary",
                                            width="stretch")
        if enviado:
            if not nome.strip() or not telefone.strip():
                st.error("Preencha nome e telefone para retornarmos.")
            else:
                captacao.criar(nome, telefone, "site", area, 0.0,
                               "", mensagem, autor="página pública")
                st.success("Recebemos seu contato! Vamos retornar em breve. "
                          "Se quiser adiantar, chame no WhatsApp ao lado.")

    st.markdown("""
<div class="publica-rodape">
  Suas informações ficam só com o escritório — usadas exclusivamente para
  retornar o seu contato.
</div>""", unsafe_allow_html=True)
