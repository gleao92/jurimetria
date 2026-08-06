"""
Agenda visual — mês, semana e dia.

O QUE APARECE EM CADA DIA
  - DATA FATAL (barra colorida, cor pela urgência): o limite real.
  - PRAZO INTERNO (barra cinza, texto apagado): o dia de trabalhar a peça.
São coisas diferentes e precisam parecer diferentes. Quem enxerga só a data
fatal no calendário descobre o prazo no dia em que ele acaba.

Feriados e fins de semana ficam com o fundo alterado, porque num sistema de
prazo o dia sem expediente não é detalhe: é o que faz a conta mudar.
"""

import calendar
from datetime import date, timedelta

from prazos import eh_dia_util, nome_do_feriado, dias_uteis_entre

DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _d(x):
    return date.fromisoformat(str(x)[:10]) if x else None


def _cor_classe(dia: date, hoje: date) -> str:
    n = dias_uteis_entre(hoje, dia) if dia > hoje else -1
    if dia < hoje or n <= 2:
        return ""            # vermelho (padrão do .chip.fatal)
    return "perto" if n <= 5 else "folga"


def indexar(prazos: list[dict], hoje: date, compromissos: dict = None) -> dict:
    """Agrupa por dia: {data: [{tipo, texto, classe}]}.

    Junta prazos e compromissos na mesma grade. Audiência ao lado da data
    fatal é o que faz o advogado enxergar a semana inteira num lugar só —
    duas agendas separadas é o mesmo que nenhuma.
    """
    por_dia = {}
    for p in prazos:
        if p.get("status") in ("cumprido", "arquivado"):
            continue
        # Sem cliente identificado, o número do processo diz muito mais que
        # um travessão. Só o primeiro bloco: é o que o advogado reconhece.
        quem = p.get("cliente") or ""
        if not quem:
            quem = (p.get("processo") or "").split("-")[0] or "processo"
        rotulo = f'{p.get("ato") or "Prazo"} · {quem}'
        pid = p.get("id", "")
        fatal = _d(p.get("data_fatal"))
        interno = _d(p.get("prazo_interno"))
        if interno and fatal and interno < fatal:
            por_dia.setdefault(interno, []).append(
                {"tipo": "interno", "texto": f"preparar · {rotulo}",
                 "classe": "", "id": pid})
        if fatal:
            por_dia.setdefault(fatal, []).append(
                {"tipo": "fatal", "texto": rotulo,
                 "classe": _cor_classe(fatal, hoje), "id": pid})
    for dia, itens in (compromissos or {}).items():
        for c in itens:
            import compromissos as _comp
            cfg = _comp.TIPOS.get(c.get("tipo"), {})
            por_dia.setdefault(dia, []).append({
                "tipo": "compromisso", "texto": _comp.rotulo(c),
                "classe": c.get("tipo") or "lembrete",
                "id": c.get("id"), "cor": cfg.get("cor", "#1E4D6B")})

    ordem = {"fatal": 0, "compromisso": 1, "interno": 2}
    for v in por_dia.values():
        v.sort(key=lambda x: ordem.get(x["tipo"], 9))
    return por_dia


def _celula(dia: date, hoje: date, por_dia: dict, do_mes: bool,
            max_chips: int = 3) -> str:
    classes = []
    if not do_mes:
        classes.append("fora")
    if dia == hoje:
        classes.append("hoje")
    fer = nome_do_feriado(dia)
    if not eh_dia_util(dia):
        classes.append("feriado")

    marca = ""
    if fer:
        marca = f"<em>{fer[:12]}</em>"
    elif dia == hoje:
        marca = "<em>hoje</em>"

    itens = por_dia.get(dia, [])
    chips = ""
    for it in itens[:max_chips]:
        cls = f'chip {it["tipo"]} {it["classe"]}'.strip()
        chips += f'<span class="{cls}" title="{it["texto"]}">{it["texto"]}</span>'
    if len(itens) > max_chips:
        chips += f'<span class="chip mais">+{len(itens)-max_chips}</span>'
    return (f'<td class="{" ".join(classes)}">'
            f'<div class="dia">{dia.day}{marca}</div>{chips}</td>')


def grade_mes(ano: int, mes: int, prazos: list[dict], hoje: date) -> str:
    por_dia = indexar(prazos, hoje, comps)
    cal = calendar.Calendar(firstweekday=0)     # segunda
    linhas = ""
    for semana in cal.monthdatescalendar(ano, mes):
        linhas += "<tr>" + "".join(
            _celula(dia, hoje, por_dia, dia.month == mes) for dia in semana
        ) + "</tr>"
    cab = "".join(f"<th>{d}</th>" for d in DIAS)
    return f'<table class="cal"><tr>{cab}</tr>{linhas}</table>' + legenda()


def grade_semana(inicio: date, prazos: list[dict], hoje: date) -> str:
    por_dia = indexar(prazos, hoje)
    dias = [inicio + timedelta(days=i) for i in range(7)]
    cab = "".join(f"<th>{DIAS[i]} {d.day:02d}/{d.month:02d}</th>"
                  for i, d in enumerate(dias))
    cels = "".join(_celula(d, hoje, por_dia, True, max_chips=6) for d in dias)
    return (f'<table class="cal sem"><tr>{cab}</tr><tr>{cels}</tr></table>'
            + legenda())


def lista_dia(dia: date, prazos: list[dict], hoje: date) -> str:
    por_dia = indexar(prazos, hoje)
    itens = por_dia.get(dia, [])
    fer = nome_do_feriado(dia)
    cabec = (f'<div class="secao">{DIAS[dia.weekday()]}, {dia.day} de '
             f'{MESES[dia.month-1]}'
             + (f' · {fer}' if fer else
                ('' if eh_dia_util(dia) else ' · sem expediente'))
             + '</div>')
    if not itens:
        return cabec + ('<div class="vazio">'
                        '<div class="vazio-t">Nenhum prazo neste dia.</div></div>')
    corpo = ""
    for it in itens:
        cor = ("#A31D1D" if it["tipo"] == "fatal" and not it["classe"]
               else "#B45309" if it["classe"] == "perto"
               else "#14453A" if it["classe"] == "folga" else "#B8B5AE")
        rotulo = "Data fatal" if it["tipo"] == "fatal" else "Preparar a peça"
        corpo += (f'<div class="diaLista" style="border-color:{cor}">'
                  f'<div class="t">{it["texto"]}</div>'
                  f'<div class="s">{rotulo}</div></div>')
    return cabec + corpo


def legenda() -> str:
    return ('<div class="legenda">'
            '<span><i style="background:#A31D1D"></i>vence em até 2 dias úteis</span>'
            '<span><i style="background:#B45309"></i>até 5 dias</span>'
            '<span><i style="background:#14453A"></i>com folga</span>'
            '<span><i style="background:#7C2D12"></i>audiência / perícia</span>'
            '<span><i style="background:#1E4D6B"></i>reunião</span>'
            '<span><i style="background:#E2E0DA"></i>preparar a peça</span>'
            '<span><i style="background:#F1EFEA"></i>sem expediente</span>'
            '</div>')


def render_mes(st, ano: int, mes: int, prazos: list, hoje: date,
               chave_selecao: str = "sel_prazo",
               comps: dict = None) -> None:
    """Desenha o mês com BOTÕES do Streamlit, não links.

    Link HTML recarrega a página, e no Streamlit recarregar cria uma sessão
    nova — o que derruba o login. Botão nativo processa o clique sem sair da
    página. É por isso que o calendário é montado em colunas em vez de uma
    tabela HTML só.
    """
    por_dia = indexar(prazos, hoje, comps)
    cal = calendar.Calendar(firstweekday=0)

    cols = st.columns(7, gap="small")
    for i, nome in enumerate(DIAS):
        cols[i].markdown(f'<div class="cabdia">{nome}</div>',
                         unsafe_allow_html=True)

    for semana in cal.monthdatescalendar(ano, mes):
        cols = st.columns(7, gap="small")
        for i, dia in enumerate(semana):
            with cols[i]:
                _celula_nativa(st, dia, hoje, por_dia, dia.month == mes,
                               chave_selecao)
    st.markdown(legenda(), unsafe_allow_html=True)


def render_semana(st, inicio: date, prazos: list, hoje: date,
                  chave_selecao: str = "sel_prazo",
               comps: dict = None) -> None:
    por_dia = indexar(prazos, hoje, comps)
    dias = [inicio + timedelta(days=i) for i in range(7)]
    cols = st.columns(7, gap="small")
    for i, dia in enumerate(dias):
        cols[i].markdown(f'<div class="cabdia">{DIAS[i]} {dia.day:02d}/{dia.month:02d}</div>',
                         unsafe_allow_html=True)
    cols = st.columns(7, gap="small")
    for i, dia in enumerate(dias):
        with cols[i]:
            _celula_nativa(st, dia, hoje, por_dia, True, chave_selecao, max_chips=8)
    st.markdown(legenda(), unsafe_allow_html=True)


def render_dia(st, dia: date, prazos: list, hoje: date,
               chave_selecao: str = "sel_prazo",
               comps: dict = None) -> None:
    por_dia = indexar(prazos, hoje, comps)
    itens = por_dia.get(dia, [])
    fer = nome_do_feriado(dia)
    st.markdown(f'<div class="secao">{DIAS[dia.weekday()]}, {dia.day} de '
                f'{MESES[dia.month-1]}'
                + (f' · {fer}' if fer else
                   ('' if eh_dia_util(dia) else ' · sem expediente'))
                + '</div>', unsafe_allow_html=True)
    if not itens:
        st.markdown('<div class="vazio"><div class="vazio-t">'
                    'Nenhum prazo neste dia.</div></div>',
                    unsafe_allow_html=True)
        return
    for j, it in enumerate(itens):
        cor = _cor_hex(it)
        c1, c2 = st.columns([6, 1.2])
        c1.markdown(f'<div class="diaLista" style="border-color:{cor}">'
                    f'<div class="t">{it["texto"]}</div>'
                    f'<div class="s">'
                    f'{"Data fatal" if it["tipo"]=="fatal" else "Preparar a peça"}'
                    f'</div></div>', unsafe_allow_html=True)
        if it.get("id") and c2.button("Abrir", key=f"ab{dia}{j}",
                                      width="stretch"):
            if it["tipo"] == "compromisso":
                st.session_state["sel_compromisso"] = it["id"]
            else:
                st.session_state[chave_selecao] = it["id"]
            st.rerun()


def _cor_hex(it: dict) -> str:
    if it["tipo"] == "compromisso":
        return it.get("cor", "#1E4D6B")
    if it["tipo"] != "fatal":
        return "#B8B5AE"
    return {"": "#A31D1D", "perto": "#B45309", "folga": "#14453A"}.get(
        it["classe"], "#B8B5AE")


def _celula_nativa(st, dia: date, hoje: date, por_dia: dict, do_mes: bool,
                   chave: str, max_chips: int = 3) -> None:
    itens = por_dia.get(dia, [])
    fer = nome_do_feriado(dia)
    cls = []
    if not do_mes:
        cls.append("fora")
    if dia == hoje:
        cls.append("hoje")
    if not eh_dia_util(dia):
        cls.append("feriado")

    marca = f'<em>{fer[:10]}</em>' if fer else ('<em>hoje</em>' if dia == hoje else '')
    with st.container(border=False, key=f"cel{dia.isoformat()}{do_mes}"):
        st.markdown(f'<div class="cel {" ".join(cls)}">'
                    f'<div class="dia">{dia.day}{marca}</div></div>',
                    unsafe_allow_html=True)
        for j, it in enumerate(itens[:max_chips]):
            tag = f'chip{it["tipo"]}{it["classe"] or "urg"}'
            with st.container(key=f"{tag}_{dia.isoformat()}_{j}"):
                if st.button(it["texto"], key=f"bt{dia.isoformat()}{j}",
                             width="stretch", help=it["texto"]):
                    if it["tipo"] == "compromisso":
                        st.session_state["sel_compromisso"] = it.get("id")
                        st.session_state[chave] = None
                    else:
                        st.session_state[chave] = it.get("id")
                        st.session_state["sel_compromisso"] = None
                    st.rerun()
        if len(itens) > max_chips:
            st.caption(f"+{len(itens)-max_chips}")
