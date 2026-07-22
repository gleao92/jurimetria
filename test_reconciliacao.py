"""
Testes do de-para DJEN x MNI.  python test_reconciliacao.py

Os casos PERIGOSOS (não unir o que é diferente) valem mais que os
convenientes (unir o que é igual). Um falso positivo aqui apaga um prazo.
"""
from datetime import date, timedelta
from reconciliacao import reconciliar, combinam, similaridade

ok = fail = 0
def check(nome, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print(f"  PASS  {nome}")
    else: fail += 1; print(f"  FALHA {nome} {extra}")

P = "1002345-67.2026.8.09.0051"
Q = "0007654-32.2026.8.09.0100"
D = date(2026, 7, 15)

def pub(proc, d, teor, sistema, tipo=""):
    return {"processo": proc, "data_disponibilizacao": d, "teor": teor,
            "sistema": sistema, "tipo": tipo}

print("\n[1] DEVE UNIR — mesma intimação descrita pelas duas fontes")
a = pub(P, D, "Intimação para apresentar contestação no prazo legal.", "DJEN")
b = pub(P, D, "Intimacao para apresentar contestacao no prazo legal", "TJGO_PROJUDI")
u, m = combinam(a, b)
check("texto quase idêntico une", u, m)

a2 = pub(P, D, "Cite-se o réu para contestação.", "DJEN")
b2 = pub(P, D + timedelta(days=2), "Fica a parte intimada para contestação.", "TJGO_PROJUDI")
u2, m2 = combinam(a2, b2)
check("mesmo ato + 2 dias de diferença une", u2, m2)

print("\n[2] NÃO PODE UNIR — os casos que apagariam um prazo")
c = pub(P, D, "Intimação para contestação.", "DJEN")
d_ = pub(P, D, "Intimação para alegações finais.", "TJGO_PROJUDI")
u3, _ = combinam(c, d_)
check("atos DIFERENTES no mesmo dia NÃO unem", not u3)

e = pub(P, D, "Contestação", "DJEN")
f = pub(Q, D, "Contestação", "TJGO_PROJUDI")
u4, _ = combinam(e, f)
check("processos diferentes NÃO unem", not u4)

g = pub(P, D, "Contestação", "DJEN")
h = pub(P, D + timedelta(days=20), "Contestação", "TJGO_PROJUDI")
u5, _ = combinam(g, h)
check("mesma intimação a 20 dias NÃO une", not u5)

i = pub(P, D, "Despacho ilegível xyz", "DJEN")
j = pub(P, D, "Outro despacho qualquer abc", "TJGO_PROJUDI")
u6, _ = combinam(i, j)
check("dois indefinidos diferentes NÃO unem", not u6)

print("\n[3] Fluxo completo")
entrada = [
    pub(P, D, "Intimação para apresentar contestação no prazo legal.", "DJEN"),
    pub(P, D, "Intimacao para apresentar contestacao no prazo legal", "TJGO_PROJUDI"),
    pub(Q, D, "Intimação para alegações finais.", "DJEN"),
    pub(P, D, "Intimação para réplica.", "DJEN"),
]
r = reconciliar(entrada)
check("4 entradas -> 3 saídas", r["saida"] == 3, f"veio {r['saida']}")
check("1 união registrada", len(r["unioes"]) == 1)
check("união traz as duas fontes",
      r["unioes"] and len(r["unioes"][0]["fontes"]) == 2)
check("réplica no mesmo processo ficou separada (suspeita)",
      any(s["processo"] == P for s in r["suspeitas"]))

print("\n[4] Nada se perde")
textos = [
    "Junte-se o comprovante de recolhimento das custas processuais.",
    "Designo audiência de conciliação para o dia 10 do mês vindouro.",
    "Certifico o decurso do prazo sem manifestação da parte contrária.",
    "Ao contador judicial para elaboração do cálculo de liquidação.",
    "Expeça-se mandado de citação no endereço indicado na inicial.",
]
todos = [pub(P, D, t, "DJEN") for t in textos]
r2 = reconciliar(todos)
check("5 atos distintos permanecem 5", r2["saida"] == 5, f"veio {r2['saida']}")

print(f"\n{'='*46}\n{ok} passaram, {fail} falharam\n{'='*46}")
raise SystemExit(1 if fail else 0)
