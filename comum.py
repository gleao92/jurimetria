"""
Utilitários compartilhados pelas telas.

Ficam aqui as funções que TODAS as vistas usam — formatação de data e cálculo
de urgência. Estavam duplicadas no app.py monolítico; com as telas separadas,
duplicá-las seria o caminho mais curto para elas divergirem, e urgência
calculada de dois jeitos é exatamente o tipo de erro que derruba a confiança
no painel.
"""

from datetime import date

from prazos import dias_uteis_entre

DIAS_PT = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun",
            "jul", "ago", "set", "out", "nov", "dez"]

ROTULO_AREA = {"a_confirmar": "a confirmar", "civel": "cível",
               "criminal": "criminal"}


def d(x):
    return date.fromisoformat(str(x)[:10]) if x else None


def fmt(x):
    dd = d(x)
    return f"{dd.day:02d}/{dd.month:02d}" if dd else "—"


def fmt_longo(x):
    dd = d(x)
    return dd.strftime("%d/%m/%Y") if dd else "—"


def urgencia(p, hoje: date = None):
    """(numeral, unidade, cor, selo, dias_uteis_restantes).

    O número é a informação principal do painel; a cor apenas o traduz.
    dias = -1 vencido · 0 vence hoje · None sem data.
    """
    hoje = hoje or date.today()
    f = d(p.get("data_fatal"))
    if not f:
        return "—", "sem data", "#6B6E72", "a definir", None
    if f < hoje:
        return "!", "vencido", "#A31D1D", "vencido", -1
    if f == hoje:
        return "0", "hoje", "#A31D1D", "hoje", 0
    n = dias_uteis_entre(hoje, f)
    cor = "#A31D1D" if n <= 2 else ("#B45309" if n <= 5 else "#14453D")
    return f"{n:02d}", "dias úteis", cor, "", n


def rotulo_area(a) -> str:
    return ROTULO_AREA.get(a, "—")
