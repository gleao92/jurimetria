"""Testes do extrator de prazo. python test_extrator.py"""
from extrator_prazo import extrair

ok = fail = 0
def check(n, c, e=""):
    global ok, fail
    if c: ok += 1; print(f"  PASS  {n}")
    else: fail += 1; print(f"  FALHA {n} → {e}")

print("\n[1] O texto REAL que expôs o problema")
real = ("PODER JUDICIÁRIO JUSTIÇA FEDERAL Subseção Judiciária de Aparecida de "
        "Goiânia-GO Juizado Especial Cível e Criminal Processo: "
        "1005386-79.2026.4.01.3504 ATO ORDINATÓRIO (art. 203, § 4º do CPC e "
        "Portaria n. 11791314 deste Juízo) Trata-se de ação em que a parte "
        "autora pretende a concessão de benefício por incapacidade temporária "
        "em face do INSS. Fica a parte autora intimada para juntar aos autos, "
        "no prazo de 15 (quinze) dias, sob pena de indeferimento da petição "
        "inicial, o(s) seguinte(s) documento(s)")
r = extrair(real)
check("extrai 15 dias", r["dias"] == 15, r)
check("marca como declarado", r["fonte"] == "declarado")
check("sem conflito", r["conflito"] is None)
check("unidade dias", r["unidade"] == "dias")

print("\n[2] Variações comuns de redação")
casos = [
    ("no prazo de 5 (cinco) dias", 5),
    ("no prazo de 05 (cinco) dias úteis", 5),
    ("prazo de 10 dias", 10),
    ("em 48 (quarenta e oito) horas", 48),
    ("no prazo comum de 15 (quinze) dias", 15),
    ("no prazo sucessivo de 30 (trinta) dias", 30),
    ("no prazo improrrogável de 5 dias", 5),
    ("Manifeste-se no prazo de quinze dias", 15),
    ("no prazo legal de 15 (quinze) dias", 15),
    ("dentro de 10 (dez) dias", 10),
]
for texto, esperado in casos:
    r = extrair(texto)
    check(f"“{texto[:42]}”", r["dias"] == esperado, r["dias"])

print("\n[3] Contagem explícita no texto")
check("reconhece dias úteis", extrair("no prazo de 15 dias úteis")["contagem"] == "uteis")
check("reconhece dias corridos", extrair("no prazo de 15 dias corridos")["contagem"] == "corridos")
check("sem menção fica vazio", extrair("no prazo de 15 dias")["contagem"] == "")
check("horas identificadas", extrair("em 48 horas")["unidade"] == "horas")

print("\n[4] Divergência algarismo x extenso — NÃO pode escolher sozinho")
r = extrair("no prazo de 10 (quinze) dias")
check("detecta o conflito", r["conflito"] is not None, r["conflito"])
check("ainda devolve um número para revisão", r["dias"] == 10)

print("\n[5] Quando NÃO há prazo declarado")
for texto in ["Junte-se aos autos.", "Sentença publicada.",
              "no prazo legal", "Cite-se o réu.", ""]:
    r = extrair(texto)
    check(f"“{texto[:28] or '(vazio)'}” → sem prazo", r["dias"] is None, r["dias"])

print("\n[6] Dedução da área — o caso INSS que estava errado")
import carteira as _c
inss = ("Trata-se de ação em que a parte autora pretende a concessão de "
        "benefício por incapacidade temporária e/ou aposentadoria por "
        "incapacidade permanente em face do INSS")
check("INSS/previdenciário -> cível", _c.area_por_assunto(inss) == "civel",
      _c.area_por_assunto(inss))
check("vara cumulativa não decide sozinha",
      _c.area_por_orgao("Juizado Especial Cível e Criminal") == "")
check("assunto resolve a vara cumulativa",
      _c.deduzir_area("Juizado Especial Cível e Criminal", inss) == "civel")
check("penal continua criminal",
      _c.area_por_assunto("réu denunciado, resposta à acusação") == "criminal")
check("texto com os dois assuntos não afirma nada",
      _c.area_por_assunto("aposentadoria e também ação penal por estelionato") == "")
check("sem pistas devolve vazio", _c.area_por_assunto("despacho") == "")

print("\n[7] Nomes REAIS de vara (o plural quebrava o padrão antigo)")
for orgao, esperado in [
        ("Goiás - Vara das Fazendas Públicas", "civel"),
        ("Goiânia - 3ª UPJ Varas Cíveis: 6ª Vara Cível", "civel"),
        ("Jussara - Vara de Família e Sucessões", "civel"),
        ("15ª Vara Federal de Juizado Especial Cível", "civel"),
        ("2ª Vara Criminal de Goiânia", "criminal"),
        ("Vara de Execução Penal", "criminal"),
        ("Juizado Especial Cível e Criminal de Aparecida", "")]:
    got = _c.area_por_orgao(orgao)
    check(f"{orgao[:40]}", got == esperado, f"veio {got!r}")

print("\n[8] Ato composto — a palavra no texto não é o ato")
from classificacao import classificar as _cl
check("manifestar SOBRE a contestação = réplica",
      _cl("no prazo de 15 dias, manifeste-se sobre a contestação")["ato"] == "réplica",
      _cl("no prazo de 15 dias, manifeste-se sobre a contestação")["ato"])
check("apresentar contestação continua contestação",
      _cl("cite-se para apresentar contestação no prazo de 15 dias")["ato"] == "contestação")
check("manifestar sobre laudo",
      _cl("manifeste-se sobre o laudo em 15 dias")["ato"] == "manifestar sobre laudo")

print(f"\n{'='*46}\n{ok} passaram, {fail} falharam\n{'='*46}")
raise SystemExit(1 if fail else 0)
