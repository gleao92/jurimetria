"""
Tela "Agenda" do Tempestivo.

Extraída do app.py, que passara de 700 linhas e concentrava todas as telas —
qualquer ajuste numa aba exigia navegar o arquivo inteiro e arriscava mexer
noutra. Cada vista agora recebe o contexto de que precisa e nada mais.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db, pipeline, captura, configuracao, carteira, estilo, agenda, calendario, painel, compromissos
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

    from datetime import timedelta
    if "cal_ref" not in st.session_state:
        st.session_state["cal_ref"] = HOJE
    ref = st.session_state["cal_ref"]

    c1, c2, c3, c4, c5 = st.columns([2.2, 0.45, 0.45, 0.7, 1.6])
    modo = c1.radio("Ver por", ["Mês", "Semana", "Dia"], horizontal=True,
                    label_visibility="collapsed")
    passo = {"Mês": 31, "Semana": 7, "Dia": 1}[modo]
    c2 = c2.container(key="navcal_ant")
    c3 = c3.container(key="navcal_prox")
    c4 = c4.container(key="navcal_hoje")
    if c5.button("+ Novo compromisso", type="primary", width="stretch"):
        st.session_state["novo_comp"] = True
        st.session_state["sel_prazo"] = None
        st.session_state["sel_compromisso"] = None
    if c2.button("‹", width="stretch", help="Anterior"):
        st.session_state["cal_ref"] = (
            (ref.replace(day=1) - timedelta(days=1)).replace(day=1)
            if modo == "Mês" else ref - timedelta(days=passo))
        st.rerun()
    if c3.button("›", width="stretch", help="Próximo"):
        if modo == "Mês":
            ultimo = calendario.calendar.monthrange(ref.year, ref.month)[1]
            st.session_state["cal_ref"] = ref.replace(day=ultimo) + timedelta(days=1)
        else:
            st.session_state["cal_ref"] = ref + timedelta(days=passo)
        st.rerun()
    if c4.button("Hoje", width="stretch"):
        st.session_state["cal_ref"] = HOJE
        st.rerun()

    prazos_cal = db.listar_prazos(["pendente_revisao", "confirmado"])
    comps_dia = compromissos.por_dia()

    # ── novo compromisso ────────────────────────────────────────────
    if st.session_state.get("novo_comp"):
        with st.container(border=True):
            st.markdown('<div class="secao">Novo compromisso</div>',
                        unsafe_allow_html=True)
            f1, f2, f3 = st.columns([1.2, 1, 0.8])
            tipo = f1.selectbox(
                "Tipo", list(compromissos.TIPOS),
                format_func=lambda t: compromissos.TIPOS[t]["rotulo"])
            dt = f2.date_input("Data", value=ref, format="DD/MM/YYYY")
            hr = f3.text_input("Hora", placeholder="14:30")
            titulo = st.text_input("Título",
                                   placeholder="Audiência de instrução e julgamento")
            g1, g2 = st.columns(2)
            cliente = g1.text_input("Cliente", key="ncli")
            local = g2.text_input("Local", placeholder="Fórum de Aparecida")
            proc = st.text_input("Processo (opcional)",
                                 placeholder="1005386-79.2026.4.01.3504")
            obs = st.text_area("Observação", height=70)
            b1, b2, _ = st.columns([1, 1, 3])
            if b1.button("Salvar compromisso", type="primary", width="stretch"):
                if not titulo.strip():
                    st.error("Dê um título ao compromisso.")
                else:
                    compromissos.criar(tipo, titulo, dt, hr, 60, proc, cliente,
                                       local, obs, USER["nome"])
                    st.session_state["novo_comp"] = False
                    st.rerun()
            if b2.button("Cancelar", width="stretch"):
                st.session_state["novo_comp"] = False; st.rerun()
        st.divider()

    # ── compromisso selecionado: ver e editar ───────────────────────
    sel_c = st.session_state.get("sel_compromisso")
    if sel_c:
        alvo = next((c for c in compromissos.listar(incluir_cancelados=True)
                     if c["id"] == sel_c), None)
        if alvo:
            cfg_t = compromissos.TIPOS.get(alvo["tipo"], {})
            with st.container(border=True):
                st.markdown(
                    f'<div class="detalhe" style="border-left-color:'
                    f'{cfg_t.get("cor", "#1E4D6B")}">'
                    f'<div class="t">{alvo["titulo"]}</div>'
                    f'<div class="c">{cfg_t.get("rotulo", alvo["tipo"])}'
                    f'{" · " + alvo["cliente"] if alvo.get("cliente") else ""}</div>'
                    f'</div>', unsafe_allow_html=True)
                e1, e2, e3 = st.columns([1.2, 1, 0.8])
                n_tipo = e1.selectbox(
                    "Tipo", list(compromissos.TIPOS),
                    index=list(compromissos.TIPOS).index(alvo["tipo"])
                    if alvo["tipo"] in compromissos.TIPOS else 0,
                    format_func=lambda t: compromissos.TIPOS[t]["rotulo"],
                    key="etipo")
                n_data = e2.date_input(
                    "Data", value=date.fromisoformat(str(alvo["data"])[:10]),
                    format="DD/MM/YYYY", key="edata")
                n_hora = e3.text_input("Hora", alvo.get("hora") or "", key="ehora")
                n_tit = st.text_input("Título", alvo["titulo"], key="etit")
                h1, h2 = st.columns(2)
                n_cli = h1.text_input("Cliente", alvo.get("cliente") or "", key="ecli")
                n_loc = h2.text_input("Local", alvo.get("local") or "", key="eloc")
                n_proc = st.text_input("Processo", alvo.get("processo") or "",
                                       key="eproc")
                n_obs = st.text_area("Observação", alvo.get("observacao") or "",
                                     height=70, key="eobs")
                i1, i2, i3 = st.columns(3)
                if i1.button("Salvar", type="primary", width="stretch"):
                    compromissos.atualizar(alvo["id"], {
                        "tipo": n_tipo, "titulo": n_tit, "data": str(n_data),
                        "hora": n_hora, "cliente": n_cli, "local": n_loc,
                        "processo": n_proc, "observacao": n_obs}, USER["nome"])
                    st.session_state["sel_compromisso"] = None; st.rerun()
                if i2.button("Cancelar compromisso", width="stretch"):
                    compromissos.cancelar(alvo["id"], USER["nome"])
                    st.session_state["sel_compromisso"] = None; st.rerun()
                if i3.button("Fechar", width="stretch"):
                    st.session_state["sel_compromisso"] = None; st.rerun()
        else:
            st.session_state["sel_compromisso"] = None
        st.divider()

    # A seleção vive na SESSÃO, não na URL. Link HTML recarrega a página, e no
    # Streamlit recarregar cria uma sessão nova — o que derrubava o login a
    # cada clique no calendário.
    sel_id = st.session_state.get("sel_prazo")
    sel_dia = None

    if sel_id:
        alvo = next((p for p in db.listar_prazos() if p["id"] == sel_id), None)
        if alvo:
            num, un, cor, selo, n = urgencia(alvo)
            restante = ("vencido" if n == -1 else "vence hoje" if n == 0
                        else f"{n} dias úteis restantes" if n is not None else "sem data")
            area_txt = {"a_confirmar": "a confirmar", "civel": "cível",
                        "criminal": "criminal"}.get(alvo.get("area"), "—")
            st.markdown(
                f'<div class="detalhe" style="border-left-color:{cor}">'
                f'<div class="t">{alvo["ato"]}</div>'
                f'<div class="c">{alvo.get("cliente") or "cliente não identificado"}</div>'
                f'<dl>'
                f'<dt>Processo</dt><dd>{alvo["processo"]}</dd>'
                f'<dt>Órgão</dt><dd>{alvo.get("tribunal") or alvo.get("sistema") or "—"}</dd>'
                f'<dt>Área</dt><dd>{area_txt}</dd>' 
                f'<dt>Publicado</dt><dd>{fmt(alvo.get("data_disponibilizacao"))}</dd>'
                f'<dt>Preparar até</dt><dd>{fmt(alvo.get("prazo_interno"))}</dd>'
                f'<dt>Data fatal</dt><dd><b style="color:{cor}">'
                f'{fmt(alvo.get("data_fatal"))} · {restante}</b></dd>'
                f'<dt>Situação</dt><dd>{alvo["status"].replace("_"," ")}'
                + (f' · por {alvo["confirmado_por"]}' if alvo.get("confirmado_por") else "")
                + '</dd>'
                + f'<dt>Origem do prazo</dt><dd>{alvo.get("fonte") or "—"}</dd>'
                + '</dl></div>', unsafe_allow_html=True)

            if alvo["status"] == "pendente_revisao":
                # Revisão AQUI mesmo. O Streamlit não troca de aba por código,
                # então mandar o usuário "para a aba Hoje" era botão morto.
                if alvo.get("teor"):
                    with st.expander("Teor da publicação"):
                        st.write(alvo["teor"])
                painel.revisar(st, db, alvo, USER["nome"], prefixo="ag",
                               pode_confirmar=PODE_CONFIRMAR)
            else:
                if alvo.get("teor"):
                    with st.expander("Teor da publicação"):
                        st.write(alvo["teor"])
                b1, b2, _ = st.columns([1, 1, 3])
                if alvo["status"] == "confirmado":
                    if b1.button("Marcar cumprido", type="primary",
                                 width="stretch"):
                        db.marcar_cumprido(alvo["id"], USER["nome"])
                        st.session_state["sel_prazo"] = None; st.rerun()
                if b2.button("Fechar", width="stretch"):
                    st.session_state["sel_prazo"] = None; st.rerun()
        else:
            st.warning("Prazo não encontrado — pode ter sido cumprido ou arquivado.")
            if st.button("Fechar"):
                st.session_state["sel_prazo"] = None; st.rerun()

        st.divider()

    if modo == "Mês":
        st.markdown(f'<div class="secao">{calendario.MESES[ref.month-1]} '
                    f'de {ref.year}</div>', unsafe_allow_html=True)
        calendario.render_mes(st, ref.year, ref.month, prazos_cal, HOJE,
                              comps=comps_dia)
    elif modo == "Semana":
        ini = ref - timedelta(days=ref.weekday())
        fim = ini + timedelta(days=6)
        st.markdown(f'<div class="secao">{ini.day:02d}/{ini.month:02d} a '
                    f'{fim.day:02d}/{fim.month:02d} de {fim.year}</div>',
                    unsafe_allow_html=True)
        calendario.render_semana(st, ini, prazos_cal, HOJE, comps=comps_dia)
    else:
        calendario.render_dia(st, ref, prazos_cal, HOJE, comps=comps_dia)


# ══════════════════ Hoje ══════════════════
