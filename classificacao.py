"""
Classificação da publicação: QUAL o ato e QUANTOS dias.

ORDEM DE CONFIANÇA — a mudança mais importante deste arquivo
  1. PRAZO DECLARADO no texto ("no prazo de 15 (quinze) dias"). É o que a
     publicação afirma; nada supera isso.
  2. PRAZO PRESUMIDO pelo tipo de ato ("contestação" -> 15). Só quando o texto
     não declara. Nasce marcado para conferência.
  3. NADA. Vai para revisão sem data, nunca com um chute.

A versão anterior fazia só o passo 2 e errava feio: uma intimação para juntar
documentos por ato ordinatório foi rotulada "contestação". O prazo até bateu
por sorte — e prazo certo por sorte é pior que prazo errado, porque cria
confiança que não se sustenta.

A CONTAGEM TAMBÉM PODE VIR DECLARADA
Se o texto diz "dias úteis" ou "dias corridos", isso prevalece sobre a
dedução por área. O juízo escreveu; não cabe ao sistema discordar.

VERSÃO COM LLM
As regras abaixo cobrem o comum. Para o resto, um LLM lendo o teor classifica
melhor — mas a regra continua valendo: a IA SUGERE, o advogado CONFIRMA
(art. 34 do EOAB; Resolução CNJ 615/2025).
"""

from extrator_prazo import extrair
from modelos import Classificacao

# As regras vivem no banco e são editáveis pela tela (regras.py). Aqui fica
# só o acesso; a lista de fábrica está em regras.PADRAO.
import regras


def classificar(teor: str, tipo: str = "") -> Classificacao:
    """Identifica o ato e o prazo. O prazo declarado no texto tem prioridade."""
    texto = f"{tipo or ''} {teor or ''}"
    t = texto.lower()

    # 1) o que a publicação DIZ
    achado = extrair(texto)

    # 2) qual o ato (para o rótulo e para o prazo presumido)
    ato, presumido = "", None
    for padrao, rotulo, dias in regras.carregar():
        if padrao in t:
            ato, presumido = rotulo, dias
            break

    if achado["dias"] is not None:
        dias = achado["dias"]
        if achado["unidade"] == "horas":
            # Prazo em horas não cabe na contagem em dias. Vai para revisão.
            return Classificacao(
                ato=ato or "prazo em horas", prazo_dias=None,
                fonte="declarado",
                conflito=f"prazo de {dias} horas — confirme a contagem",
                revisar=True, trecho=achado["trecho"])
        return Classificacao(
            ato=ato or "determinação do juízo", prazo_dias=dias,
            fonte="declarado", contagem_declarada=achado["contagem"],
            conflito=achado["conflito"],
            revisar=achado["conflito"] is not None, trecho=achado["trecho"])

    if presumido is not None:
        return Classificacao(
            ato=ato, prazo_dias=presumido, fonte="presumido", revisar=True,
            trecho="prazo não declarado no texto — presumido pelo ato")

    return Classificacao(
        ato=ato or "a identificar", prazo_dias=None, fonte="", revisar=True,
        trecho="sem prazo declarado e ato não reconhecido")
