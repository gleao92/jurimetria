"""
Tempestivo — controladoria de prazos.
Rodar:  python -m streamlit run app.py

Este arquivo é só o esqueleto: autenticação, barra lateral, cabeçalho e a
escolha da tela. Cada tela vive em vista_*.py.
"""

from datetime import date

import streamlit as st

# Antes de tudo: confere se todos os arquivos estão na pasta. Faltando um, o
# Python mostra um traceback que não diz o que fazer.
_NECESSARIOS = [
    "db", "auth", "pipeline", "captura", "configuracao", "estilo", "comum",
    "prazos", "painel", "calendario", "agenda", "carteira", "compromissos",
    "regras", "modelos", "classificacao", "extrator_prazo", "config",
    "vista_hoje", "vista_agenda", "vista_prazos", "vista_processos",
    "vista_ajustes",
]
_faltando = []
for _m in _NECESSARIOS:
    try:
        __import__(_m)
    except ModuleNotFoundError as _e:
        if _e.name == _m:
            _faltando.append(_m + ".py")
if _faltando:
    st.error("**Faltam arquivos na pasta do sistema.**")
    st.write("Estes arquivos não foram encontrados:")
    for _f in _faltando:
        st.code(_f, language="text")
    st.info("Baixe todos os arquivos para a MESMA pasta do `app.py` e "
            "reinicie o Streamlit. Todos ficam na mesma pasta — não há subpastas.")
    st.stop()

import db, auth, pipeline, captura, configuracao, estilo
from config import NOME_SISTEMA, SUBTITULO, PAPEIS
from comum import urgencia, DIAS_PT, MESES_PT
from prazos import eh_dia_util, nome_do_feriado
import vista_hoje as v_hoje
import vista_agenda as v_agenda
import vista_prazos as v_prazos
import vista_processos as v_processos
import vista_ajustes as v_ajustes

st.set_page_config(page_title=NOME_SISTEMA, page_icon="⚖️", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(estilo.CSS + estilo.CSS_AGENDA, unsafe_allow_html=True)

HOJE = date.today()
db.init(); auth.init()
FONTE_CONECTADA = captura.fonte_conectada()


# ══════════════════ primeiro acesso ══════════════════
if not auth.existe_algum_usuario():
    c = st.columns([1, 1.25, 1])[1]
    with c:
        st.markdown(f'<div class="topo"><h1>{NOME_SISTEMA}</h1></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="secao">Criar o acesso do advogado</div>',
                    unsafe_allow_html=True)
        st.caption("Só o advogado confirma prazos. Quem der apoio entra depois, "
                   "com acesso próprio.")
        with st.form("setup"):
            nome = st.text_input("Nome", placeholder="Dr. Fulano de Tal")
            user = st.text_input("Usuário", placeholder="fulano")
            s1 = st.text_input("Senha", type="password", help="Mínimo de 8 caracteres.")
            s2 = st.text_input("Repita a senha", type="password")
            if st.form_submit_button("Criar acesso", type="primary", width="stretch"):
                if s1 != s2:
                    st.error("As senhas não conferem.")
                elif not nome.strip():
                    st.error("Informe o nome.")
                else:
                    ok, msg = auth.criar_usuario(user, nome, s1, "advogado")
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)
    st.stop()


# ══════════════════ entrar ══════════════════
if "user" not in st.session_state:
    c = st.columns([1, 1.05, 1])[1]
    with c:
        st.markdown(f'<div class="topo"><h1>{NOME_SISTEMA}</h1></div>',
                    unsafe_allow_html=True)
        st.caption(SUBTITULO)
        st.write("")
        with st.form("login"):
            u = st.text_input("Usuário")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary", width="stretch"):
                user = auth.verificar(u, s)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                st.error("Usuário ou senha incorretos.")
        st.caption("Acessos e tentativas ficam registrados.")
    st.stop()

USER = st.session_state["user"]
PODE_CONFIRMAR = auth.pode_confirmar(USER)

ativos = db.listar_prazos(["pendente_revisao", "confirmado"])
revisar = [p for p in ativos if p["status"] == "pendente_revisao"]
confirmados = [p for p in ativos if p["status"] == "confirmado"]
criticos = [p for p in ativos
            if (urgencia(p, HOJE)[4] is not None and 0 <= urgencia(p, HOJE)[4] <= 2)]
vencidos = [p for p in ativos if urgencia(p, HOJE)[4] == -1]

TELAS = [
    ("hoje", "Hoje", ":material/bolt:"),
    ("agenda", "Agenda", ":material/calendar_month:"),
    ("prazos", "Prazos", ":material/timer:"),
    ("processos", "Processos", ":material/folder:"),
]
if "tela" not in st.session_state or st.session_state["tela"] not in \
        [t[0] for t in TELAS] + ["ajustes"]:
    st.session_state["tela"] = "hoje"
if st.session_state["tela"] == "ajustes" and not PODE_CONFIRMAR:
    st.session_state["tela"] = "hoje"
TELA = st.session_state["tela"]


# ══════════════════ barra lateral ══════════════════
with st.sidebar:
    st.markdown(f'<div class="marca-barra">{NOME_SISTEMA}'
                f'<small>{SUBTITULO}</small></div>', unsafe_allow_html=True)

    st.markdown('<div class="grupo-barra">Painel</div>', unsafe_allow_html=True)
    for chave, rotulo, icone in TELAS:
        ativo = (TELA == chave)
        # Chave do container diferente para o item ativo — é o que permite ao
        # CSS destacá-lo sem depender de índice ou ordem.
        with st.container(key=f"{'menuativo' if ativo else 'menu'}_{chave}"):
            if st.button(rotulo, icon=icone, key=f"btn_{chave}", width="stretch"):
                st.session_state["tela"] = chave
                st.rerun()

    if PODE_CONFIRMAR:
        st.markdown('<div class="grupo-barra">Sistema</div>', unsafe_allow_html=True)
        ativo = (TELA == "ajustes")
        with st.container(key=f"{'menuativo' if ativo else 'menu'}_ajustes"):
            if st.button("Ajustes", icon=":material/settings:", key="btn_ajustes",
                         width="stretch"):
                st.session_state["tela"] = "ajustes"
                st.rerun()

    st.markdown('<div class="grupo-barra">Publicações</div>', unsafe_allow_html=True)
    if FONTE_CONECTADA:
        cfg_l = configuracao.carregar()
        st.caption(f"{cfg_l['fonte'].upper()} · OAB {cfg_l['oab_numero']}/{cfg_l['oab_uf']}")
        with st.container(key="acao_buscar"):
            if st.button("Buscar agora", icon=":material/download:", key="btn_buscar"):
                try:
                    r = pipeline.processar_publicacoes(captura.capturar_publicacoes(dias=15))
                    st.success(f"{r['prazos_criados']} novos")
                    st.rerun()
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
    else:
        st.caption("Nenhuma fonte ligada.")
        with st.container(key="acao_exemplo"):
            if st.button("Usar dados de exemplo", key="btn_exemplo"):
                pipeline.carregar_exemplo(); st.rerun()

    st.markdown(f'<div class="rodape-barra"><b>{USER["nome"]}</b>'
                f'<span>{USER["papel"]}</span></div>', unsafe_allow_html=True)
    with st.expander("Minha conta"):
        a1 = st.text_input("Senha atual", type="password", key="sa")
        a2 = st.text_input("Nova senha", type="password", key="sn")
        if st.button("Alterar senha", width="stretch"):
            ok, msg = auth.trocar_senha(USER["usuario"], a1, a2)
            st.success(msg) if ok else st.error(msg)
        if PODE_CONFIRMAR:
            st.divider()
            st.caption("Quem tem acesso")
            for u in auth.listar_usuarios():
                st.caption(f"· {u['nome']} — {u['papel']}")
            nn = st.text_input("Nome", key="un")
            nu = st.text_input("Usuário", key="uu")
            np_ = st.text_input("Senha", type="password", key="up")
            pp = st.selectbox("Papel", PAPEIS, index=1, key="upa")
            if st.button("Criar acesso", width="stretch"):
                ok, msg = auth.criar_usuario(nu, nn, np_, pp)
                st.success(msg) if ok else st.error(msg)
        st.divider()
        if st.button("Sair", icon=":material/logout:", width="stretch"):
            del st.session_state["user"]; st.rerun()


# ══════════════════ cabeçalho ══════════════════
# Título e uma linha dizendo o que se faz ali. O subtítulo existe para quem
# abre a tela sem saber o que esperar — some da memória depois de dois usos,
# mas evita a primeira hesitação.
TITULOS = {
    "hoje": ("Hoje", "O que precisa da sua atenção agora."),
    "agenda": ("Agenda", "Prazos e compromissos no calendário."),
    "prazos": ("Prazos", "Todos os prazos, com filtros e exportação."),
    "processos": ("Processos", "Sua carteira e a área de contagem de cada um."),
    "ajustes": ("Ajustes", "Fonte das publicações, regras e feriados."),
}
extra = nome_do_feriado(HOJE)
sub = extra if extra else ("dia útil" if eh_dia_util(HOJE) else "sem expediente")

_titulo, _sub = TITULOS[TELA]
st.markdown(
    f'<div class="topo"><div><h1>{_titulo}</h1>'
    f'<div class="sub">{_sub}</div></div>'
    f'<div class="data"><b>{DIAS_PT[HOJE.weekday()]}, {HOJE.day} de '
    f'{MESES_PT[HOJE.month-1]} de {HOJE.year}</b><br>{sub}</div></div>',
    unsafe_allow_html=True)

# O painel de situação acompanha as telas de trabalho, não os Ajustes.
if TELA != "ajustes":
    st.markdown(
        f'<div class="situacao">'
        f'<div><b>{len(revisar)}</b><span>a revisar</span></div>'
        f'<div><b>{len(confirmados)}</b><span>confirmados</span></div>'
        f'<div><b style="color:var(--urgente)">{len(criticos)}</b>'
        f'<span>vencem em até 2 dias</span></div>'
        f'<div><b style="color:var(--urgente)">{len(vencidos)}</b>'
        f'<span>vencidos</span></div></div>', unsafe_allow_html=True)

if not FONTE_CONECTADA and TELA != "ajustes":
    st.info("Mostrando dados de exemplo. Ligue uma fonte de publicações em Ajustes.")

CTX = {"USER": USER, "PODE_CONFIRMAR": PODE_CONFIRMAR, "HOJE": HOJE,
       "FONTE_CONECTADA": FONTE_CONECTADA, "ativos": ativos,
       "revisar": revisar, "confirmados": confirmados}

if TELA == "hoje":
    v_hoje.render(CTX)
elif TELA == "agenda":
    v_agenda.render(CTX)
elif TELA == "prazos":
    v_prazos.render(CTX)
elif TELA == "processos":
    v_processos.render(CTX)
elif TELA == "ajustes":
    v_ajustes.render(CTX)
