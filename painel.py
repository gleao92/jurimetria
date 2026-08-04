"""
Painel de revisão de um prazo — usado na aba Hoje E na Agenda.

POR QUE VIROU MÓDULO
Antes o painel existia só na aba Hoje. Na Agenda havia um botão "Revisar em
Hoje" que apenas marcava a intenção — e o Streamlit não permite trocar de aba
por código, então nada acontecia na tela. Botão que parece quebrado.

A resposta certa não é pedir para o usuário mudar de aba: é revisar onde ele
está. Como o painel agora é um só, as duas telas mostram exatamente os mesmos
campos e o mesmo cálculo — sem chance de divergirem com o tempo.
"""

from datetime import date

from prazos import calcular_prazo, area_para_calculo

AREAS = ["a_confirmar", "civel", "criminal"]
ROTULO_AREA = {"a_confirmar": "a confirmar", "civel": "cível",
               "criminal": "criminal"}


def _data(x):
    return date.fromisoformat(str(x)[:10]) if x else None


def _fmt(x):
    d = _data(x)
    return d.strftime("%d/%m/%Y") if d else "—"


def revisar(st, db, p: dict, usuario: str, prefixo: str = "",
            pode_confirmar: bool = True) -> None:
    """Desenha o painel. `prefixo` mantém as chaves únicas quando o mesmo
    prazo aparece em duas telas."""
    k = f"{prefixo}{p['id']}"
    hoje = date.today()

    with st.container(border=True):
        # Identificação: sem isto o advogado não sabe QUAL processo está
        # decidindo, e decidir prazo às cegas é pior que não decidir.
        st.markdown(
            f'<div class="cab-rev">'
            f'<span class="proc">{p.get("processo") or "—"}</span>'
            f'<span class="org">{p.get("tribunal") or p.get("sistema") or ""}</span>'
            f'</div>'
            f'<div class="cli-rev">{p.get("cliente") or "cliente não identificado"}'
            f' · publicado {_fmt(p.get("data_disponibilizacao"))}</div>',
            unsafe_allow_html=True)

        # O trecho de onde saiu o prazo, em destaque. É o que permite conferir
        # em um olhar, sem ler dois mil caracteres de fundamentação.
        trecho = (p.get("trecho") or "").strip()
        if trecho and not trecho.startswith(("prazo não declarado", "sem prazo")):
            st.markdown(f'<div class="trecho"><b>Onde está o prazo</b>'
                        f'<div>…{trecho}…</div></div>', unsafe_allow_html=True)

        if p.get("teor"):
            with st.expander("Ler a publicação inteira", expanded=not trecho):
                st.markdown(f'<div class="teor-completo">{p["teor"]}</div>',
                            unsafe_allow_html=True)

        c1, c2, c3 = st.columns([2, 1, 1.4])
        ato = c1.text_input("Ato", p.get("ato") or "", key=f"a{k}")
        dias = c2.number_input("Dias", 1, 180, int(p.get("prazo_dias") or 15),
                               key=f"n{k}")
        guardada = p.get("area") if p.get("area") in AREAS else "a_confirmar"
        area = c3.selectbox("Área", AREAS, index=AREAS.index(guardada),
                            format_func=lambda x: ROTULO_AREA[x], key=f"ar{k}",
                            help="Cível conta em dias úteis; criminal, em dias "
                                 "corridos. Em 'a confirmar' o sistema usa a "
                                 "contagem que dá a data mais cedo.")

        fonte = p.get("fonte") or ""
        if fonte.startswith("declarado"):
            st.success("Prazo **declarado na própria publicação**.")
        elif fonte.startswith("presumido"):
            st.warning("A publicação **não declara o prazo**. Este número foi "
                       "presumido pelo tipo de ato — confira no texto acima.")
        if "·" in fonte:
            st.error(fonte.split("·", 1)[1].strip())

        base = _data(p.get("data_disponibilizacao")) or hoje
        # Mesma regra do pipeline: a data do DJEN já é publicação, não
        # disponibilização. Recalcular sem isso mostraria ao advogado uma data
        # um dia à frente da lista — a divergência que ele apontou contra o PJe.
        from pipeline import _tipo_data
        td = _tipo_data(p)
        rc = calcular_prazo(base, int(dias), area_para_calculo(area), tipo_data=td)
        outra = "criminal" if area_para_calculo(area) == "civel" else "civel"
        rc2 = calcular_prazo(base, int(dias), outra, tipo_data=td)
        aviso = (" · contagem conservadora até você confirmar a área"
                 if area == "a_confirmar" else "")
        st.caption(
            f"{rc['contagem']}{aviso} · início "
            f"{rc['inicio_contagem'].strftime('%d/%m')} · "
            f"**fatal {rc['data_fatal'].strftime('%d/%m/%Y')}** · "
            f"interno {rc['prazo_interno'].strftime('%d/%m')}  \n"
            f"Em contagem {'de dias úteis' if outra == 'civel' else 'corrida'}, "
            f"a data fatal seria {rc2['data_fatal'].strftime('%d/%m/%Y')}.")

        obs = st.text_input("Observação", key=f"o{k}")

        if not pode_confirmar:
            st.caption("A confirmação é do advogado.")

        b1, b2, b3 = st.columns(3)
        if b1.button("Confirmar prazo", key=f"c{k}", type="primary",
                     width="stretch", disabled=not pode_confirmar):
            db.confirmar(p["id"], usuario, int(dias), rc["data_fatal"],
                         rc["prazo_interno"], ato, obs)
            con = db.conectar()
            con.execute("UPDATE prazos SET area=? WHERE id=?", (area, p["id"]))
            con.commit(); con.close()
            _fechar(st)
        if b2.button("Não gera prazo", key=f"x{k}", width="stretch",
                     disabled=not pode_confirmar):
            db.arquivar(p["id"], usuario, obs or "sem prazo")
            _fechar(st)
        if b3.button("Fechar", key=f"f{k}", width="stretch"):
            _fechar(st)


def _fechar(st):
    st.session_state["abrir"] = None
    st.session_state["sel_prazo"] = None
    st.rerun()
