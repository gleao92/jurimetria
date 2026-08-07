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
from config import (NOME_ESCRITORIO, SUBTITULO_ESCRITORIO, WHATSAPP_NUMERO,
                    AREAS_ATUACAO, CIDADE_REGIAO, HERO_TITULO, HERO_SUBTITULO,
                    MENSAGEM_WHATSAPP_PADRAO)

_NUMERO_EXEMPLO = "5562900000000"

# Paleta da marca do escritório (vinho + dourado sobre creme) — deliberadamente
# DIFERENTE do tema escuro/âmbar do painel interno: aqui é a identidade visual
# do escritório, de quem visita de fora; lá dentro é a ferramenta de trabalho.
_CSS_FIRMA = """
<style>
.stApp{ background:#EDE6D8 !important; }
.publica-hero{ border-bottom-color:rgba(92,31,48,.18) !important; }
.publica-logo{
  width:64px; height:64px; margin:0 auto 1rem;
}
.publica-marca{ color:#9C7A46 !important; }
.publica-marca .nome{
  font-family:'Playfair Display',Georgia,serif; font-size:1.3rem; font-weight:700;
  color:#5C1F30; letter-spacing:.08em;
}
.publica-marca .sub{
  display:block; font-size:.62rem; font-weight:600; letter-spacing:.18em;
  color:#B8935A; text-transform:uppercase; margin-top:.25rem;
}
.publica-titulo{
  font-family:'Playfair Display',Georgia,serif; font-size:2.6rem; font-weight:700;
  color:#5C1F30; letter-spacing:-.02em; margin:1.3rem 0 .7rem;
}
.publica-hero p{ color:#5A4A3F !important; }
.publica-hero .etq{
  background:rgba(184,147,90,.14) !important; color:#7A5A28 !important;
  border:1px solid rgba(184,147,90,.35) !important;
}
.secao{ color:#9C7A46 !important; border-bottom-color:rgba(92,31,48,.18) !important; }
.publica-rodape{ color:#8A7A68 !important; border-top-color:rgba(92,31,48,.18) !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] input, [data-testid="stSelectbox"] [role="group"]{
  background:#FBF8F2 !important; color:#3A2E28 !important;
  border-color:#D9CFBC !important;
}
[data-testid="stSelectboxVirtualDropdown"] li{
  background:#FBF8F2 !important; color:#3A2E28 !important;
}
[data-testid="stSelectboxVirtualDropdown"] li:hover{ background:#EDE0C8 !important; }
[data-testid="stWidgetLabel"] p{ color:#5A4A3F !important; }
[data-testid="stBaseLinkButton-primary"], [data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"]{
  background:#5C1F30 !important; border-color:#5C1F30 !important;
  color:#F5EFE3 !important;
}
[data-testid="stBaseLinkButton-primary"]:hover, [data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover{
  background:#4A1826 !important; border-color:#4A1826 !important;
}
[data-testid="stCaptionContainer"], .stMarkdown p{ color:#5A4A3F; }
</style>
"""


def _link_whatsapp(mensagem: str = "") -> str:
    numero = "".join(c for c in WHATSAPP_NUMERO if c.isdigit())
    texto = quote(mensagem or MENSAGEM_WHATSAPP_PADRAO)
    return f"https://wa.me/{numero}?text={texto}"


_LOGO_SVG = """
<svg class="publica-logo" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="50" cy="50" r="46" stroke="#B8935A" stroke-width="1.5"/>
  <text x="50" y="46" text-anchor="middle" font-family="Playfair Display, Georgia, serif"
        font-size="34" fill="#B8935A">M</text>
  <line x1="50" y1="55" x2="50" y2="72" stroke="#B8935A" stroke-width="1.3"/>
  <line x1="36" y1="60" x2="64" y2="60" stroke="#B8935A" stroke-width="1.3"/>
  <path d="M30 60 L36 70 A7 7 0 0 1 24 70 Z" stroke="#B8935A" stroke-width="1.1" fill="none"/>
  <path d="M70 60 L76 70 A7 7 0 0 1 64 70 Z" stroke="#B8935A" stroke-width="1.1" fill="none"/>
</svg>
"""


def render():
    st.markdown(_CSS_FIRMA, unsafe_allow_html=True)
    tags = "".join(f'<span class="etq">{a}</span>' for a in AREAS_ATUACAO)
    st.markdown(f"""
<div class="publica-hero">
  {_LOGO_SVG}
  <div class="publica-marca">
    <span class="nome">{NOME_ESCRITORIO.upper()}</span>
    <small class="sub">{SUBTITULO_ESCRITORIO}</small>
  </div>
  <div class="publica-titulo">{HERO_TITULO}</div>
  <p>{HERO_SUBTITULO}</p>
  <div class="etiquetas" style="justify-content:center; margin-top:1.3rem;">{tags}</div>
  <p style="margin-top:1rem; font-size:.85rem;">{CIDADE_REGIAO}</p>
</div>""", unsafe_allow_html=True)

    if WHATSAPP_NUMERO == _NUMERO_EXEMPLO:
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
