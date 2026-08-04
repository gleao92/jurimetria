"""
Tela "Ajustes" do Tempestivo.

Extraída do app.py, que passara de 700 linhas e concentrava todas as telas —
qualquer ajuste numa aba exigia navegar o arquivo inteiro e arriscava mexer
noutra. Cada vista agora recebe o contexto de que precisa e nada mais.
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import db, pipeline, captura, configuracao, carteira, estilo, agenda, calendario, painel, regras
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

    cfg = configuracao.carregar()

    st.markdown('<div class="secao">Certificado da OAB</div>',
                unsafe_allow_html=True)
    st.caption("O token não entra aqui. A chave dele fica dentro do "
               "dispositivo e não sai — continua sendo usado no navegador, "
               "para assinar e protocolar. Para acompanhar prazos, o "
               "sistema precisa apenas consultar.")

    st.markdown('<div class="secao">De onde vêm as publicações</div>',
                unsafe_allow_html=True)

    st.markdown('<span class="passo">1 · Identificação</span>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    oab = c1.text_input("Número da OAB", cfg["oab_numero"], placeholder="61423",
                        disabled=configuracao.vindo_do_ambiente("oab_numero"))
    uf = c2.text_input("UF", cfg["oab_uf"], max_chars=2,
                       disabled=configuracao.vindo_do_ambiente("oab_uf"))

    st.markdown('<span class="passo">2 · Fonte</span>', unsafe_allow_html=True)
    fontes = {"djen": "Diário Nacional — só a OAB, sem senha",
              "mni": "Webservice do tribunal — exige usuário e senha",
              "ambas": "As duas, com cruzamento automático"}
    fonte = st.radio("Fonte", list(fontes), format_func=lambda k: fontes[k],
                     index=list(fontes).index(cfg.get("fonte", "djen")),
                     label_visibility="collapsed")
    if fonte != cfg.get("fonte"):
        for k in ("amostra", "res_mni", "canario", "resumo_proc"):
            st.session_state.pop(k, None)

    mni_user = cfg["mni_usuario"]; mni_senha = cfg["mni_senha"]
    mni_wsdl = cfg.get("mni_wsdl", "")
    if fonte in ("mni", "ambas"):
        m1, m2 = st.columns(2)
        mni_user = m1.text_input("Usuário no tribunal", mni_user,
                                 help="No TJGO costuma ser o CPF sem pontuação.")
        mni_senha = m2.text_input("Senha", mni_senha, type="password")
        mni_wsdl = st.text_input("Endereço do serviço (WSDL)", mni_wsdl,
                                 placeholder="https://.../IntercomunicacaoService?WSDL")

    st.markdown('<span class="passo">3 · Conferir</span>', unsafe_allow_html=True)
    b1, b2 = st.columns([1, 2])
    if b1.button("Testar", type="primary", width="stretch"):
        configuracao.salvar({"oab_numero": oab.strip(), "oab_uf": uf.strip().upper(),
                             "fonte": fonte, "mni_usuario": mni_user,
                             "mni_senha": mni_senha, "mni_wsdl": mni_wsdl})
        st.session_state["amostra"] = st.session_state["res_mni"] = None
        if fonte in ("djen", "ambas"):
            with st.spinner("Consultando o Diário Nacional..."):
                try:
                    import captura_djen
                    st.session_state["amostra"] = captura_djen.amostra(
                        oab.strip(), uf.strip().upper())
                except Exception as e:
                    st.session_state["amostra"] = {"erro": f"{type(e).__name__}: {e}"}
        if fonte in ("mni", "ambas"):
            with st.spinner("Conectando ao tribunal..."):
                import mni as _mni
                st.session_state["res_mni"] = _mni.testar()

    am = st.session_state.get("amostra")
    if am:
        if am.get("erro"):
            st.error(am["erro"])
        elif not am.get("total"):
            st.warning("Nenhuma publicação nesse período. Confira a OAB e a UF.")
        else:
            st.success(f"**{am['total']} publicações** em 60 dias · "
                       f"{len(am['processos'])} processos · "
                       f"{', '.join(am['tribunais'])}")
            vaz = {k: v for k, v in am.get("campos_vazios", {}).items() if v}
            if vaz:
                st.error(f"Campos vazios: {vaz}. O nome do campo mudou na "
                         "origem — sem isso o prazo sai errado.")
            if am.get("orgaos"):
                crim = [o for o in am["orgaos"] if any(
                    t in o.lower() for t in ("crim", "penal", "júri", "juri"))]
                st.caption("**Varas:** " + " · ".join(am["orgaos"][:12]))
                if crim:
                    st.caption(f"Criminal presente: {', '.join(crim)}")
            with st.expander("Processos encontrados"):
                st.caption(" · ".join(am["processos"]))

    rm = st.session_state.get("res_mni")
    if rm:
        if rm["ok"] and rm.get("vazio"):
            st.warning(rm["msg"])
            st.caption(rm.get("dica", ""))
        elif rm["ok"]:
            st.success(rm["msg"])
        else:
            st.error(rm["msg"])
            if rm.get("dica"):
                st.caption(rm["dica"])

        with st.expander("Verificações do serviço"):
            import mni as _m
            st.caption(f"módulo: `{getattr(_m,'VERSAO','versão antiga')}`")
            if st.button("Conferir se a senha é mesmo exigida"):
                st.session_state["canario"] = _m.verificar_autenticacao()
            can = st.session_state.get("canario")
            if can:
                if can["confiavel"] is True:
                    st.success(can["msg"])
                elif can["confiavel"] is False:
                    st.error(can["msg"])
                else:
                    st.warning(can["msg"])
            st.divider()
            pn = st.text_input("Consultar um processo", key="pnum",
                               placeholder="1002345-67.2026.8.09.0051")
            if st.button("Consultar") and pn.strip():
                try:
                    st.session_state["resumo_proc"] = _m.resumo_processo(pn.strip())
                except Exception as e:
                    st.session_state["resumo_proc"] = {"erro": str(e)[:400]}
            rp = st.session_state.get("resumo_proc")
            if rp:
                if rp.get("erro"):
                    st.error(rp["erro"])
                else:
                    st.write(f"**{rp.get('provavel_cliente') or '—'}** · "
                             f"{rp.get('orgao') or '—'}")
                    a = carteira.area_por_orgao(rp.get("orgao", ""))
                    st.caption(f"Área deduzida: {a or 'não foi possível'}")

    st.markdown('<span class="passo">4 · Ligar</span>', unsafe_allow_html=True)
    conectada = st.toggle("Usar esta fonte no lugar dos dados de exemplo",
                          value=cfg.get("conectada", False))
    if conectada != cfg.get("conectada", False):
        configuracao.salvar({"conectada": conectada})
        db.registrar("config_conectada", USER["nome"], str(conectada))
        st.rerun()

    st.markdown('<div class="secao">Contagem de prazos</div>',
                unsafe_allow_html=True)
    st.caption("Quando o sistema não consegue identificar a área do "
               "processo, ele precisa escolher uma contagem. Cível conta "
               "em dias úteis; criminal, em dias corridos.")
    padroes = {"conservadora": "A mais curta (protege, mas adianta as datas)",
               "civel": "Cível — dias úteis (carteira predominantemente cível)",
               "criminal": "Criminal — dias corridos"}
    ap = st.radio("Na dúvida, contar como", list(padroes),
                  format_func=lambda x: padroes[x],
                  index=list(padroes).index(cfg.get("area_padrao", "conservadora")),
                  label_visibility="collapsed")
    if ap != cfg.get("area_padrao", "conservadora"):
        configuracao.salvar({"area_padrao": ap})
        db.registrar("area_padrao", USER["nome"], ap)
        st.rerun()
    st.caption("Se a maior parte da carteira é previdenciária, cível ou "
               "trabalhista, escolha **cível** — o conservador adianta "
               "todas as datas e o painel perde credibilidade.")

    st.divider()
    st.caption("As regras de identificação melhoram com o uso. Depois de "
               "mudar algo aqui, recalcule os prazos ainda **não "
               "confirmados** para que o painel reflita a regra nova. "
               "Prazo já confirmado não é tocado — ele carrega a sua decisão.")
    if st.button("Recalcular prazos não confirmados"):
        with st.spinner("Recalculando..."):
            r = pipeline.recalcular_pendentes()
        st.success(f"{r['atualizados']} de {r['analisados']} atualizados · "
                   f"{r['area_corrigida']} tiveram a área corrigida.")
        st.rerun()

    st.markdown('<div class="secao">Como o sistema lê as publicações</div>',
                unsafe_allow_html=True)
    st.caption("Quando a publicação **declara** o prazo (\"no prazo de 15 "
               "(quinze) dias\"), é isso que vale. Estas regras servem para o "
               "resto: dizem qual é o ato e, quando o texto não informa, "
               "quantos dias presumir. A ordem importa — a primeira que casar "
               "vence, então deixe as expressões compostas acima das soltas.")

    todas = regras.listar()
    tab_regras = pd.DataFrame([{
        "Trecho a procurar": r["padrao"], "Ato": r["rotulo"],
        "Dias": r["dias"], "Ativa": bool(r["ativa"]),
    } for r in todas])

    editadas = st.data_editor(
        tab_regras, width="stretch", hide_index=True, num_rows="dynamic",
        key="edregras",
        column_config={
            "Trecho a procurar": st.column_config.TextColumn(
                help="Texto que aparece na publicação. Sem acento não casa — "
                     "escreva como o tribunal escreve."),
            "Ato": st.column_config.TextColumn(
                help="Nome que aparecerá na lista de prazos."),
            "Dias": st.column_config.NumberColumn(
                min_value=1, max_value=180,
                help="Deixe vazio quando o ato não tiver prazo fixo."),
            "Ativa": st.column_config.CheckboxColumn(
                help="Desmarque para desligar sem apagar."),
        })

    cr1, cr2, _ = st.columns([1, 1, 2])
    if cr1.button("Salvar regras", type="primary", width="stretch"):
        novas = [{"padrao": l["Trecho a procurar"], "rotulo": l["Ato"],
                  "dias": None if pd.isna(l["Dias"]) else int(l["Dias"]),
                  "ativa": bool(l["Ativa"])}
                 for _, l in editadas.iterrows()]
        n, erros = regras.salvar(novas, USER["nome"])
        if erros:
            for e in erros:
                st.error(e)
        else:
            st.success(f"{n} regras salvas. Recalcule os prazos não "
                       "confirmados para aplicá-las ao que já está no sistema.")
            st.rerun()
    if cr2.button("Restaurar as de fábrica", width="stretch"):
        n = regras.restaurar_padrao(USER["nome"])
        st.success(f"{n} regras restauradas.")
        st.rerun()

    st.markdown('<div class="secao">Feriados considerados</div>',
                unsafe_allow_html=True)
    fer = feriados_do_ano(HOJE.year)
    st.caption(" · ".join(f"{k.day:02d}/{k.month:02d} {v}"
                          for k, v in sorted(fer.items())))
    st.caption("Faltam os feriados forenses do tribunal — preencha "
               "`feriados_local.py`. Sem eles alguns prazos saem mais cedo "
               "que o real: protege, mas aperta.")

    st.markdown('<div class="secao">Registro de atividade</div>',
                unsafe_allow_html=True)
    logs = db.ultimos_logs(120)
    if logs:
        st.dataframe(pd.DataFrame(logs)[["quando", "acao", "detalhe"]]
                     .rename(columns={"quando": "Quando", "acao": "Ação",
                                      "detalhe": "Detalhe"}),
                     width="stretch", hide_index=True, height=260)
    else:
        st.caption("Sem registros.")
