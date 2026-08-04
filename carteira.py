"""
Importação da carteira de processos.

POR QUE ISTO EXISTE (e por que não é um robô de login no Projudi):
Nenhuma via oficial lista a carteira de um advogado. O MNI consulta processo
por processo; o webservice do Projudi exige idProcesso + hashProcesso, ou
seja, você já tem que conhecer o processo. Sobra a busca web "Processo por
Advogado" — página, com captcha, sujeita a mudar de layout e a contrariar as
condições de uso. Raspar isso arrisca o ACESSO DO ADVOGADO ao próprio sistema.

Trocar esse risco por uma importação manual de dez minutos, feita uma vez, é
o negócio certo. Depois dela, tudo volta a ser automático: o DJEN traz as
publicações e o MNI completa os dados.

POR QUE A ÁREA IMPORTA TANTO:
Cível conta em dias ÚTEIS; criminal, em CORRIDOS. Para o mesmo prazo de 15
dias isso dá ~7 dias de diferença, e o cível cai MAIS TARDE. Tratar um
criminal como cível empurra a data fatal para depois da real — e faz perder
prazo. Por isso a área de cada processo precisa estar certa.
"""

import re
import db

# Número CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO (aceita com ou sem pontuação)
RE_CNJ = re.compile(r"\b(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})\b")

# Pistas no nome do órgão/vara para deduzir a área.
# A direção do erro importa: cível conta em dias ÚTEIS (data mais TARDE),
# criminal em CORRIDOS (data mais CEDO). Classificar um criminal como cível
# empurra o prazo para depois do real = PERDE. Logo, só afirmamos "cível"
# quando o nome do órgão não deixa dúvida.
PISTAS_CRIMINAL = (
    "crim", "penal", "júri", "juri", "execuç penal", "execucao penal",
    "tóxic", "toxic", "entorpecente", "violência doméstica",
    "violencia domestica", "maria da penha", "delito", "infrações penais",
    "infracoes penais", "auditoria militar",
)
# Radicais, não palavras inteiras: o nome real da vara vem no plural
# ("Varas Cíveis", "Vara das Fazendas Públicas") e o padrão no singular não
# casava. Comparação sempre sem acento e em minúsculas.
PISTAS_CIVEL = (
    "cive",              # cível, cíveis
    "familia", "sucess", "orfaos",
    "fazenda",           # fazenda pública, fazendas públicas
    "empresaria", "falenc", "recuperacao judicial",
    "consumidor", "registros publicos", "acidentes de trabalho",
    "precatori", "previdenci", "execucoes fiscais", "execucao fiscal",
)
# Casos em que NÃO dá para afirmar: regra de contagem própria ou ambígua.
PISTAS_AMBIGUAS = (
    "juizado especial civel e criminal",   # foro cumulativo: só o assunto decide
    "infância", "infancia", # cível e infracional na mesma vara
    "unica",                # vara única acumula cível e criminal
    "cumulativa", "plantao",
)
def formatar_cnj(m) -> str:
    return f"{m.group(1)}-{m.group(2)}.{m.group(3)}.{m.group(4)}.{m.group(5)}.{m.group(6)}"


def extrair_numeros(texto: str) -> list[str]:
    """Puxa todos os números CNJ de um texto colado — aceita lista solta,
    CSV, ou texto copiado direto da tela do Projudi."""
    vistos, saida = set(), []
    for m in RE_CNJ.finditer(texto or ""):
        n = formatar_cnj(m)
        if n not in vistos:
            vistos.add(n)
            saida.append(n)
    return saida


def area_por_orgao(orgao: str) -> str:
    """Deduz a área pelo nome da vara.

    Retorna "" quando não dá para afirmar — e "" é uma resposta legítima.
    Chutar aqui vira prazo errado; o sistema prefere marcar "a confirmar"
    e usar a contagem mais curta enquanto isso.
    """
    import unicodedata
    o = unicodedata.normalize("NFKD", (orgao or "").lower())
    o = "".join(c for c in o if not unicodedata.combining(c))
    if not o:
        return ""
    if any(p in o for p in PISTAS_AMBIGUAS):
        return ""                      # vara mista/regra própria: não afirmamos
    if any(p in o for p in PISTAS_CRIMINAL):
        return "criminal"
    if any(p in o for p in PISTAS_CIVEL):
        return "civel"
    return ""


# ── Dedução pelo ASSUNTO ────────────────────────────────────────────────
# O nome da vara falha em foro cumulativo ("Juizado Especial Cível E
# Criminal"). O assunto não falha: auxílio-doença é cível, denúncia é
# criminal, não importa em que vara tramite. Por isso o assunto tem
# prioridade sobre o nome do órgão.
ASSUNTO_CIVEL = (
    # previdenciário — o grosso de quem litiga contra o INSS
    "inss", "instituto nacional do seguro social", "auxilio-doenca",
    "auxilio doenca", "aposentadoria", "beneficio por incapacidade",
    "incapacidade temporaria", "incapacidade permanente", "pensao por morte",
    "salario-maternidade", "salario maternidade", "auxilio-acidente",
    "beneficio assistencial", "loas", "bpc", "qualidade de segurad",
    "periodo de carencia", "tempo de contribuicao", "revisao da vida toda",
    # cível em geral
    "execucao fiscal", "cobranca", "indenizacao", "danos morais",
    "danos materiais", "usucapiao", "reintegracao de posse", "despejo",
    "alimentos", "divorcio", "inventario", "consumidor", "busca e apreensao",
    "monitoria", "embargos a execucao", "cumprimento de sentenca",
)
ASSUNTO_CRIMINAL = (
    "denuncia", "acusacao", "reu", "delito", "crime", "pena privativa",
    "habeas corpus", "inquerito policial", "flagrante", "execucao penal",
    "trafico de drogas", "furto", "roubo", "homicidio", "lesao corporal",
    "estelionato", "sursis", "livramento condicional", "regime prisional",
    "medida protetiva", "queixa-crime", "acao penal",
)


def area_por_assunto(texto: str) -> str:
    """Deduz a área pelo ASSUNTO do processo. "" quando não dá para afirmar."""
    import unicodedata
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    if not t:
        return ""
    crim = any(p in t for p in ASSUNTO_CRIMINAL)
    civ = any(p in t for p in ASSUNTO_CIVEL)
    if crim and civ:
        return ""              # texto cita os dois: não afirmamos nada
    if crim:
        return "criminal"
    if civ:
        return "civel"
    return ""


def deduzir_area(orgao: str = "", teor: str = "") -> str:
    """Assunto primeiro; nome do órgão depois. "" se nenhum dos dois resolver."""
    return area_por_assunto(teor) or area_por_orgao(orgao)


def formatar_numero(n: str) -> str:
    """Aplica a máscara CNJ: 20 dígitos -> 0000000-00.0000.0.00.0000."""
    d = "".join(c for c in str(n or "") if c.isdigit())
    if len(d) != 20:
        return str(n or "")
    return f"{d[:7]}-{d[7:9]}.{d[9:13]}.{d[13]}.{d[14:16]}.{d[16:]}"


def importar(numeros: list[str], area_padrao: str = "") -> dict:
    """Grava os processos na carteira. area_padrao vazio = 'a_confirmar'."""
    db.init()
    processos = [{"numero": n, "cliente": "", "area": area_padrao or "a_confirmar",
                  "sistema": "", "tribunal": "", "assunto": ""} for n in numeros]
    db.salvar_processos(processos)
    db.registrar("carteira_importada", "", f"{len(numeros)} processos")
    return {"importados": len(numeros)}


def enriquecer_via_mni(numeros: list[str], limite: int = 25) -> dict:
    """Completa cliente, órgão e área consultando o MNI processo a processo.

    Vai devagar de propósito: consulta em lote agressiva contra o tribunal
    pode derrubar o acesso — e quem fica sem acesso é o advogado.
    """
    import mni
    ok = erros = 0
    detalhes = []
    con = db.conectar()
    for numero in numeros[:limite]:
        try:
            r = mni.resumo_processo(numero)
            area = area_por_orgao(r.get("orgao", "")) or "a_confirmar"
            con.execute("""UPDATE processos SET cliente=?, tribunal=?,
                           assunto=?, area=? WHERE numero=?""",
                        (r.get("provavel_cliente", ""), r.get("orgao", ""),
                         r.get("classe", ""), area, numero))
            ok += 1
            detalhes.append({"numero": numero, "cliente": r.get("provavel_cliente"),
                             "orgao": r.get("orgao"), "area": area})
        except Exception as e:
            erros += 1
            detalhes.append({"numero": numero, "erro": f"{type(e).__name__}: {str(e)[:80]}"})
    con.commit(); con.close()
    db.registrar("carteira_enriquecida", "", f"{ok} ok, {erros} erros")
    return {"ok": ok, "erros": erros, "detalhes": detalhes}
