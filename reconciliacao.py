"""
De-para entre DJEN e MNI — cruza as duas fontes sem inventar.

O PROBLEMA
As duas fontes descrevem a MESMA intimação de formas diferentes: o texto muda,
e a data pode divergir (o DJEN informa a disponibilização; o MNI, a data do
expediente). Deduplicar por igualdade exata não pega nada, e o mesmo prazo
aparece duas vezes.

O PRINCÍPIO (o mais importante deste arquivo)
Os dois erros possíveis não têm o mesmo peso:

    não unir o que era igual   -> prazo repetido, revisado duas vezes. Chato.
    unir o que era diferente   -> uma intimação some junto com a outra. FATAL.

Portanto só unimos com evidência. Na dúvida, mantém separado e marca para o
advogado olhar. Um de-para agressivo é pior que nenhum.

CRITÉRIO PARA UNIR (todos precisam valer)
  1. Mesmo número de processo.
  2. Datas dentro de JANELA_DIAS.
  3. Textos parecidos (>= LIMIAR) OU o mesmo ato classificado.

Tudo que for unido fica registrado com as duas fontes e o motivo, para dar
para auditar depois.
"""

import re
import unicodedata
from datetime import date, timedelta
from difflib import SequenceMatcher

JANELA_DIAS = 3          # DJEN e MNI podem divergir alguns dias
LIMIAR_QUASE_IGUAL = 0.85  # sem ato reconhecido, exige texto quase idêntico
MIN_CARACTERES = 25        # texto curto: similaridade não significa nada


def normalizar_texto(t: str) -> str:
    t = (t or "").lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def similaridade(a: str, b: str) -> float:
    na, nb = normalizar_texto(a), normalizar_texto(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _data(p) -> date:
    d = p.get("data_disponibilizacao")
    if isinstance(d, str):
        try:
            return date.fromisoformat(d[:10])
        except Exception:
            return date.today()
    return d or date.today()


def combinam(a: dict, b: dict) -> tuple[bool, str]:
    """Decide se dois registros são a MESMA intimação.

    Ordem importa. O ato classificado manda; a similaridade de texto é só
    desempate. Publicação jurídica é cheia de fórmula pronta — "Intimação
    para contestação" e "Intimação para alegações finais" passam de 60% de
    semelhança e são atos completamente diferentes. Deixar a similaridade
    decidir sozinha faz sumir prazo.
    """
    from classificacao import classificar

    if a.get("processo") != b.get("processo") or not a.get("processo"):
        return False, ""
    dias = abs((_data(a) - _data(b)).days)
    if dias > JANELA_DIAS:
        return False, ""

    ca = classificar(a.get("teor", ""), a.get("tipo", ""))
    cb = classificar(b.get("teor", ""), b.get("tipo", ""))
    a_ok = ca["prazo_dias"] is not None
    b_ok = cb["prazo_dias"] is not None

    if a_ok and b_ok:
        # VETO: dois atos reconhecidos e diferentes são intimações distintas,
        # por mais parecido que o texto seja. Este é o guarda-corpo principal.
        if ca["ato"] != cb["ato"]:
            return False, ""
        return True, f"mesmo ato ({ca['ato']}), {dias}d de diferença"

    # Pelo menos um não foi reconhecido: só une se o texto for quase idêntico
    # e tiver tamanho suficiente para a comparação querer dizer algo.
    na, nb = normalizar_texto(a.get("teor", "")), normalizar_texto(b.get("teor", ""))
    if min(len(na), len(nb)) < MIN_CARACTERES:
        return False, ""
    sim = SequenceMatcher(None, na, nb).ratio()
    if sim >= LIMIAR_QUASE_IGUAL:
        return True, f"texto {int(sim*100)}% idêntico, {dias}d de diferença"
    return False, ""


def reconciliar(publicacoes: list[dict]) -> dict:
    """Cruza as publicações das duas fontes.

    Devolve:
      unificadas -> lista final para o pipeline (sem duplicata confirmada)
      unioes     -> o que foi unido e por quê (auditoria)
      suspeitas  -> mesmo processo e data próxima, mas SEM evidência de serem
                    iguais. Ficam SEPARADAS de propósito; é só um alerta.
    """
    restantes = list(publicacoes)
    unificadas, unioes, suspeitas = [], [], []

    while restantes:
        base = restantes.pop(0)
        fontes = {base.get("sistema", "?")}
        juntou = []

        i = 0
        while i < len(restantes):
            ok, motivo = combinam(base, restantes[i])
            if ok:
                outro = restantes.pop(i)
                fontes.add(outro.get("sistema", "?"))
                # Fica com o teor mais completo das duas fontes.
                if len(outro.get("teor", "")) > len(base.get("teor", "")):
                    base = {**base, "teor": outro["teor"]}
                if not base.get("tipo") and outro.get("tipo"):
                    base["tipo"] = outro["tipo"]
                juntou.append({"processo": base.get("processo"),
                               "motivo": motivo,
                               "fontes": sorted(fontes)})
            else:
                # Mesmo processo e data perto, mas sem evidência: NÃO une.
                if (restantes[i].get("processo") == base.get("processo")
                        and abs((_data(base) - _data(restantes[i])).days) <= JANELA_DIAS):
                    suspeitas.append({
                        "processo": base.get("processo"),
                        "datas": [str(_data(base)), str(_data(restantes[i]))],
                        "similaridade": round(
                            similaridade(base.get("teor", ""),
                                         restantes[i].get("teor", "")), 2),
                        "nota": "mantidos SEPARADOS — podem ser 2 intimações "
                                "distintas. Confirme na revisão."})
                i += 1

        base["fontes"] = sorted(fontes)
        unificadas.append(base)
        unioes.extend(juntou)

    return {"unificadas": unificadas, "unioes": unioes, "suspeitas": suspeitas,
            "entrada": len(publicacoes), "saida": len(unificadas)}
