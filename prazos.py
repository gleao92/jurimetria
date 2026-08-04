"""
Motor de cálculo de prazos processuais — o coração da controladoria.

REGRAS IMPLEMENTADAS
- CÍVEL (CPC/2015 art. 219): prazos em DIAS ÚTEIS.
  Contagem exclui o dia do começo e inclui o do vencimento (art. 224).
  Disponibilização no DJEN (D0) -> Publicação = 1º dia útil seguinte
  -> Início da contagem = 1º dia útil seguinte à publicação.
- CRIMINAL (CPP art. 798): prazos em DIAS CORRIDOS, com prorrogação para o
  próximo dia útil se o vencimento cair em dia não útil (art. 798, §3º).
- RECESSO (CPC art. 220): 20/12 a 20/01, prazos CÍVEIS suspensos.
- FERIADOS MÓVEIS: Carnaval, Sexta-feira Santa e Corpus Christi calculados
  automaticamente a partir da Páscoa, para qualquer ano.
- FERIADOS FORENSES LOCAIS: em feriados_local.py (você preenche com a portaria
  do TJGO — ver aviso lá).

>>> A DIREÇÃO DO ERRO IMPORTA <<<
Feriado A MAIS que não existe  -> data fatal calculada DEPOIS da real -> PERDE O PRAZO.
Feriado A MENOS que existe     -> data fatal calculada ANTES da real  -> protocola adiantado.
Por isso o padrão aqui é CONSERVADOR: na dúvida, NÃO marque como feriado.
"""

from datetime import date, timedelta
from functools import lru_cache

try:
    from feriados_local import FERIADOS_FORENSES_LOCAIS, INCLUIR_QUARTA_CINZAS
except ImportError:  # funciona mesmo sem o arquivo local
    FERIADOS_FORENSES_LOCAIS, INCLUIR_QUARTA_CINZAS = {}, False

# Margem de segurança: prazo INTERNO exibido N dias úteis antes do fatal.
MARGEM_SEGURANCA_DIAS = 3

# Criminal: iniciar contagem no dia seguinte à DISPONIBILIZAÇÃO (padrão, mais
# conservador) ou no dia seguinte à PUBLICAÇÃO. Confirme com o advogado.
CRIMINAL_CONTA_DA_PUBLICACAO = False

# Criminal no recesso: por padrão NÃO suspende (art. 220 do CPC é cível).
# Direção conservadora — deixa o prazo mais cedo.
CRIMINAL_SUSPENDE_NO_RECESSO = False

FERIADOS_NACIONAIS_FIXOS = {
    (1, 1): "Confraternização Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independência",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamação da República",
    (11, 20): "Consciência Negra",
    (12, 25): "Natal",
}


def pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher)."""
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriados_moveis(ano: int) -> dict:
    """Feriados que dependem da Páscoa — matemática, sem chute."""
    p = pascoa(ano)
    fer = {
        p - timedelta(days=48): "Carnaval (segunda)",
        p - timedelta(days=47): "Carnaval (terça)",
        p - timedelta(days=2): "Sexta-feira Santa",
        p + timedelta(days=60): "Corpus Christi",
    }
    if INCLUIR_QUARTA_CINZAS:  # em muitos foros é meio expediente, não feriado
        fer[p - timedelta(days=46)] = "Quarta-feira de Cinzas"
    return fer


@lru_cache(maxsize=64)
def feriados_do_ano(ano: int) -> dict:
    """Todos os feriados do ano: nacionais + móveis + forenses locais."""
    fer = {date(ano, m, d): nome for (m, d), nome in FERIADOS_NACIONAIS_FIXOS.items()}
    fer.update(feriados_moveis(ano))
    for d, nome in FERIADOS_FORENSES_LOCAIS.items():
        if d.year == ano:
            fer[d] = nome
    return fer


def nome_do_feriado(d: date):
    return feriados_do_ano(d.year).get(d)


def eh_dia_util(d: date) -> bool:
    return d.weekday() < 5 and d not in feriados_do_ano(d.year)


def em_recesso_forense(d: date) -> bool:
    """Art. 220 do CPC: prazos suspensos de 20/12 a 20/01."""
    return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)


def _bloqueado(d: date, suspende_recesso: bool) -> bool:
    return (not eh_dia_util(d)) or (suspende_recesso and em_recesso_forense(d))


def proximo_dia_util(d: date, suspende_recesso: bool = True) -> date:
    d += timedelta(days=1)
    while _bloqueado(d, suspende_recesso):
        d += timedelta(days=1)
    return d


def dias_uteis_entre(inicio: date, fim: date, suspende_recesso: bool = True) -> int:
    """Dias úteis em (inicio, fim] — exclui o início, inclui o fim.
    Respeita o recesso, igual ao motor de cálculo (antes divergia)."""
    if fim <= inicio:
        return 0
    count, d = 0, inicio
    while d < fim:
        d += timedelta(days=1)
        if not _bloqueado(d, suspende_recesso):
            count += 1
    return count


def recuar_dias_uteis(d: date, n: int, suspende_recesso: bool = True) -> date:
    """Recua N dias úteis — usado para o prazo interno (margem de segurança)."""
    for _ in range(n):
        d -= timedelta(days=1)
        while _bloqueado(d, suspende_recesso):
            d -= timedelta(days=1)
    return d


# Área desconhecida: usar a contagem que dá a data MAIS CEDO.
# Cível conta em dias úteis (data mais tarde); criminal em corridos (mais cedo).
# Errar para tarde faz perder prazo; errar para cedo só faz protocolar antes.
AREA_CONSERVADORA = "criminal"


def area_para_calculo(area: str) -> str:
    """Traduz a área guardada para a área usada no cálculo.

    Existe para que pipeline e tela usem EXATAMENTE a mesma regra. Antes o
    pipeline usava a contagem conservadora e a tela abria em "cível" — a lista
    mostrava uma data e o painel outra, para o mesmo prazo.

    Quando a área é desconhecida, vale o padrão configurado. O padrão de
    fábrica é o conservador (data mais cedo), mas numa carteira quase toda
    cível — previdenciário contra o INSS, por exemplo — isso adianta TODAS as
    datas e o advogado deixa de confiar no sistema. Aí o certo é configurar
    "cível" e deixar o conservador para as exceções.
    """
    if area in ("civel", "criminal"):
        return area
    try:
        import configuracao
        padrao = configuracao.carregar().get("area_padrao", "conservadora")
    except Exception:
        padrao = "conservadora"
    return padrao if padrao in ("civel", "criminal") else AREA_CONSERVADORA


def calcular_prazo(data_base: date, prazo_dias: int,
                   area: str = "civel", margem: int = None,
                   contagem_forcada: str = "", tipo_data: str = "disponibilizacao") -> dict:
    """Retorna as datas-chave, a data fatal e o prazo interno de segurança.

    tipo_data: diz QUAL data está entrando, para não contar duas vezes o passo
        "primeiro dia útil seguinte" (art. 224 §2º do CPC):
          "disponibilizacao" -> data em que saiu no diário. O sistema avança
                                 para a publicação (próximo dia útil).
          "publicacao"       -> a data em que já se CONSIDERA publicada/houve
                                 ciência. Usa direto, sem avançar.
        O DJEN entrega a data de publicação, não a de disponibilização — por
        isso este parâmetro existe. Tratar uma como a outra desloca a data
        fatal em um dia útil, que foi o erro batido contra o PJe.

    contagem_forcada: "uteis" ou "corridos". Usado quando a PRÓPRIA publicação
        declara a forma de contagem — o juízo escreveu, o sistema não discute.
        Vence a dedução por área.
    """
    area = (area or "civel").lower()
    margem = MARGEM_SEGURANCA_DIAS if margem is None else margem

    if contagem_forcada == "uteis":
        area = "civel"
    elif contagem_forcada == "corridos":
        area = "criminal"

    # A disponibilização vira publicação no primeiro dia útil seguinte.
    # Se já recebemos a publicação, esse passo não se repete.
    ja_publicada = (tipo_data == "publicacao")

    if area == "criminal":
        susp = CRIMINAL_SUSPENDE_NO_RECESSO
        if ja_publicada or not CRIMINAL_CONTA_DA_PUBLICACAO:
            publicacao = data_base
        else:
            publicacao = proximo_dia_util(data_base, susp)
        inicio = publicacao + timedelta(days=1)
        fatal = inicio + timedelta(days=prazo_dias - 1)
        while _bloqueado(fatal, susp):   # prorrogação, art. 798 §3º
            fatal += timedelta(days=1)
        contagem = "dias corridos (CPP art. 798)"
    else:
        susp = True
        publicacao = data_base if ja_publicada else proximo_dia_util(data_base)
        inicio = proximo_dia_util(publicacao)
        fatal, contados = inicio, 1
        while contados < prazo_dias:
            fatal = proximo_dia_util(fatal)
            contados += 1
        contagem = "dias úteis (CPC art. 219)"

    return {
        "area": area,
        "disponibilizacao": data_base,
        "publicacao": publicacao,
        "inicio_contagem": inicio,
        "data_fatal": fatal,
        "prazo_interno": recuar_dias_uteis(fatal, margem, susp),
        "contagem": contagem,
    }
