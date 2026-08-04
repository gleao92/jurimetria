"""
Extração do prazo DECLARADO no texto da publicação.

O ERRO QUE ISTO CORRIGE
A versão anterior adivinhava o número de dias a partir de uma palavra-chave
("contestação" -> 15). Mas a publicação quase sempre DIZ o prazo:

    "Fica a parte autora intimada para juntar aos autos, no prazo de
     15 (quinze) dias, sob pena de indeferimento da petição inicial"

Adivinhar quando o texto informa é indefensável: erra o ato, erra o número, e
o advogado perde a confiança no sistema inteiro na primeira conferência.

HIERARQUIA DE CONFIANÇA
  1. declarado  -> o número está escrito na publicação. Confiável.
  2. presumido  -> deduzido do tipo de ato. Serve, mas exige conferência.
  3. nenhum     -> não dá para afirmar. Vai para revisão sem data.

DIVERGÊNCIA ALGARISMO x EXTENSO
"10 (quinze) dias" acontece — erro de digitação do cartório. Quando os dois
não batem, NÃO escolhemos: devolvemos as duas leituras e mandamos revisar.
Escolher sozinho aqui é escolher a chance de perder prazo.
"""

import re
import unicodedata

EXTENSO = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5,
    "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11,
    "doze": 12, "treze": 13, "catorze": 14, "quatorze": 14, "quinze": 15,
    "dezesseis": 16, "dezessete": 17, "dezoito": 18, "dezenove": 19,
    "vinte": 20, "trinta": 30, "quarenta": 40, "quarenta e oito": 48,
    "sessenta": 60, "noventa": 90, "cento e vinte": 120,
}

# "no prazo de 15 (quinze) dias" · "em 05 (cinco) dias úteis" · "prazo: 10 dias"
RE_PRAZO = re.compile(
    r"(?:prazo\s+(?:comum\s+|sucessivo\s+|legal\s+|improrrogavel\s+|unico\s+|"
    r"de\s+lei\s+|assinalado\s+)?(?:de\s+|:\s*)?|em\s+|dentro\s+de\s+)"
    r"(\d{1,3})\s*"
    r"(?:\(\s*([a-z\s]{3,25}?)\s*\)\s*)?"
    r"(dias?\s+uteis|dias?\s+corridos|dias?|horas?)",
    re.IGNORECASE)

# Prazo por extenso sem algarismo: "no prazo de quinze dias"
RE_PRAZO_EXTENSO = re.compile(
    r"prazo\s+(?:comum\s+|sucessivo\s+|legal\s+|improrrogavel\s+)?de\s+"
    r"([a-z]+(?:\s+e\s+[a-z]+)?)\s+(dias?\s+uteis|dias?|horas?)",
    re.IGNORECASE)


def _sem_acento(t: str) -> str:
    t = unicodedata.normalize("NFKD", (t or "").lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def extrair(texto: str) -> dict:
    """Procura o prazo declarado.

    Devolve:
      {"dias": int|None, "unidade": "dias"|"horas",
       "contagem": "uteis"|"corridos"|"", "fonte": "declarado"|"",
       "conflito": str|None, "trecho": str}
    """
    t = _sem_acento(texto)
    vazio = {"dias": None, "unidade": "", "contagem": "", "fonte": "",
             "conflito": None, "trecho": ""}
    if not t:
        return vazio

    m = RE_PRAZO.search(t)
    if m:
        num = int(m.group(1))
        palavra = (m.group(2) or "").strip()
        unidade_txt = m.group(3)

        conflito = None
        if palavra:
            por_extenso = EXTENSO.get(palavra)
            if por_extenso and por_extenso != num:
                # Cartório errou a digitação. Não escolhemos por conta própria.
                conflito = (f"a publicação diz “{num}” em algarismo e "
                            f"“{palavra}” ({por_extenso}) por extenso")

        contagem = ("uteis" if "utei" in unidade_txt
                    else "corridos" if "corrido" in unidade_txt else "")
        unidade = "horas" if unidade_txt.startswith("hora") else "dias"
        return {"dias": num, "unidade": unidade, "contagem": contagem,
                "fonte": "declarado", "conflito": conflito,
                "trecho": texto[max(0, m.start() - 40):m.end() + 20].strip()}

    m2 = RE_PRAZO_EXTENSO.search(t)
    if m2:
        palavra = m2.group(1).strip()
        num = EXTENSO.get(palavra)
        if num:
            unidade_txt = m2.group(2)
            return {"dias": num,
                    "unidade": "horas" if unidade_txt.startswith("hora") else "dias",
                    "contagem": "uteis" if "utei" in unidade_txt else "",
                    "fonte": "declarado", "conflito": None,
                    "trecho": texto[max(0, m2.start() - 40):m2.end() + 20].strip()}

    return vazio
