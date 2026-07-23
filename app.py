"""
Tempestivo — controladoria de prazos.
Rodar:  python -m streamlit run app.py

Este arquivo é só o esqueleto: autenticação, cabeçalho, barra lateral e a
escolha da aba. Cada tela vive em vistas/, para que mexer na Agenda não
implique abrir o mesmo arquivo onde estão os Ajustes.
"""

from datetime import date

import streamlit as st

# Antes de qualquer coisa: confere se todos os arquivos estão na pasta.
# Faltando um, o Python mostra um traceback que não diz o que fazer.
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
            "reinicie o Streamlit (Ctrl+C e rodar de novo). Todos ficam na "
            "mesma pasta — não há subpastas.")
    st.stop()

import db, auth, pipeline, captura, configuracao, estilo
from config import NOME_SISTEMA, SUBTITULO, PAPEIS
from comum import urgencia, DIAS_PT, MESES_PT
from prazos import eh_dia_util, nome_do_feriado, MARGEM_SEGURANCA_DIAS
# Módulos achatados de propósito: em subpasta, cada atualização exigia
# recriar a pasta na mão — e um arquivo no lugar errado derrubava o app
# inteiro com ModuleNotFoundError. O ganho de organização não valia o
# atrito, e o prefixo vista_ já agrupa visualmente na listagem.
import vista_hoje as v_hoje
import vista_agenda as v_agenda
import vista_prazos as v_prazos
import vista_processos as v_processos
import vista_ajustes as v_ajustes

st.set_page_config(page_title=NOME_SISTEMA, page_icon="⚖️", layout="wide")
st.markdown(estilo.CSS + estilo.CSS_AGENDA, unsafe_allow_html=True)

HOJE = date.today()
db.init(); auth.init()
FONTE_CONECTADA = captura.fonte_conectada()


# ══════════════════ primeiro acesso ══════════════════
if not auth.existe_algum_usuario():
    c = st.columns([1, 1.3, 1])[1]
    with c:
        st.markdown(f'<div class="cabeca"><div class="marca">{NOME_SISTEMA}'
                    f'<small>{SUBTITULO}</small></div></div>',
                    unsafe_allow_html=True)
        st.markdown('<div class="secao">Criar o acesso do advogado</div>',
                    unsafe_allow_html=True)
        st.caption("Só o advogado confirma prazos. Quem der apoio entra depois, "
                   "com acesso próprio.")
        with st.form("setup"):
            nome = st.text_input("Nome", placeholder="Dr. Fulano de Tal")
            user = st.text_input("Usuário", placeholder="fulano")
            s1 = st.text_input("Senha", type="password",
                               help="Mínimo de 8 caracteres.")
            s2 = st.text_input("Repita a senha", type="password")
            if st.form_submit_button("Criar acesso", type="primary",
                                     width="stretch"):
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
    c = st.columns([1, 1.1, 1])[1]
    with c:
        st.markdown(f'<div class="cabeca"><div class="marca">{NOME_SISTEMA}'
                    f'<small>{SUBTITULO}</small></div></div>',
                    unsafe_allow_html=True)
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


# ══════════════════ lateral ══════════════════
with st.sidebar:
    st.markdown(f'<div class="marca" style="font-size:1.3rem">{NOME_SISTEMA}</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="secao">Publicações</div>', unsafe_allow_html=True)
    if FONTE_CONECTADA:
        cfg_l = configuracao.carregar()
        st.caption(f"{cfg_l['fonte'].upper()} · OAB {cfg_l['oab_numero']}/{cfg_l['oab_uf']}")
        if st.button("Buscar agora", type="primary", width="stretch"):
            try:
                r = pipeline.processar_publicacoes(captura.capturar_publicacoes(dias=15))
                st.success(f"{r['prazos_criados']} novos")
                st.rerun()
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")
    else:
        st.caption("Nenhuma fonte ligada. Configure em Ajustes.")
        if st.button("Usar dados de exemplo", width="stretch"):
            pipeline.carregar_exemplo(); st.rerun()



# ══════════════════ cabeçalho ══════════════════
extra = nome_do_feriado(HOJE)
sub = extra if extra else ("dia útil" if eh_dia_util(HOJE) else "sem expediente")

hc1, hc2, hc3 = st.columns([4, 2, 1.5])
with hc1:
    st.markdown(f'<div class="marca">{NOME_SISTEMA}<small>{SUBTITULO}</small></div>',
                unsafe_allow_html=True)
with hc2:
    st.markdown(f'<div class="hoje-topo">{DIAS_PT[HOJE.weekday()]}, {HOJE.day} de '
                f'{MESES_PT[HOJE.month-1]} de {HOJE.year}<br>'
                f'<span>{sub}</span></div>', unsafe_allow_html=True)
with hc3:
    # Identidade e configuração ficam JUNTAS, no alto à direita — é o canto
    # onde se procura por "quem sou eu" e "onde mudo isso".
    with st.popover(f"👤 {USER['nome'].split()[0]}", width="stretch"):
        st.markdown(f"**{USER['nome']}**  \n`{USER['papel']}`")
        st.divider()
        if PODE_CONFIRMAR and st.button("Ajustes do sistema", width="stretch"):
            st.session_state["tela"] = "ajustes"; st.rerun()
        with st.expander("Trocar minha senha"):
            b1 = st.text_input("Senha atual", type="password", key="hsa")
            b2 = st.text_input("Nova senha", type="password", key="hsn")
            if st.button("Alterar senha", width="stretch"):
                ok, msg = auth.trocar_senha(USER["usuario"], b1, b2)
                st.success(msg) if ok else st.error(msg)
        if PODE_CONFIRMAR:
            with st.expander("Quem tem acesso"):
                for u in auth.listar_usuarios():
                    st.caption(f"{u['nome']} · {u['papel']}")
                nn = st.text_input("Nome", key="hun")
                nu = st.text_input("Usuário", key="huu")
                np_ = st.text_input("Senha", type="password", key="hup")
                pp = st.selectbox("Papel", PAPEIS, index=1, key="hupa")
                if st.button("Criar acesso", width="stretch"):
                    ok, msg = auth.criar_usuario(nu, nn, np_, pp)
                    st.success(msg) if ok else st.error(msg)
        st.divider()
        if st.button("Sair", width="stretch"):
            del st.session_state["user"]; st.rerun()
st.markdown('<hr class="regua-topo">', unsafe_allow_html=True)

ativos = db.listar_prazos(["pendente_revisao", "confirmado"])
revisar = [p for p in ativos if p["status"] == "pendente_revisao"]
confirmados = [p for p in ativos if p["status"] == "confirmado"]
criticos = [p for p in ativos
            if (urgencia(p, HOJE)[4] is not None and 0 <= urgencia(p, HOJE)[4] <= 2)]
vencidos = [p for p in ativos if urgencia(p, HOJE)[4] == -1]

st.markdown(
    f'<div class="situacao">'
    f'<div><b>{len(revisar)}</b><span>a revisar</span></div>'
    f'<div><b>{len(confirmados)}</b><span>confirmados</span></div>'
    f'<div><b style="color:#A31D1D">{len(criticos)}</b>'
    f'<span>vencem em até 2 dias</span></div>'
    f'<div><b style="color:#A31D1D">{len(vencidos)}</b><span>vencidos</span></div>'
    f'</div>', unsafe_allow_html=True)

if not FONTE_CONECTADA:
    st.info("Mostrando dados de exemplo. Ligue uma fonte de publicações em "
            "Ajustes para usar com processos reais.")

CTX = {"USER": USER, "PODE_CONFIRMAR": PODE_CONFIRMAR, "HOJE": HOJE,
       "FONTE_CONECTADA": FONTE_CONECTADA, "ativos": ativos,
       "revisar": revisar, "confirmados": confirmados}

# Ajustes não é conteúdo do dia a dia: ficava lado a lado com "Hoje" e
# "Prazos" como se fosse mais uma tela de trabalho. Virou destino próprio,
# alcançado pelo menu do usuário, com volta explícita.
if st.session_state.get("tela") == "ajustes" and PODE_CONFIRMAR:
    if st.button("← Voltar ao painel"):
        st.session_state["tela"] = None; st.rerun()
    v_ajustes.render(CTX)
else:
    _t = st.tabs(["Hoje", "Agenda", "Prazos", "Processos"])
    with _t[0]:
        v_hoje.render(CTX)
    with _t[1]:
        v_agenda.render(CTX)
    with _t[2]:
        v_prazos.render(CTX)
    with _t[3]:
        v_processos.render(CTX)
