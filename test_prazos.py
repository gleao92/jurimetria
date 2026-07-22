"""
Testes do motor de prazos. Rode com:  python test_prazos.py

Se algum destes falhar, NÃO use o sistema até corrigir — cada um cobre um
caso onde um erro vira prazo perdido.
"""
from datetime import date, timedelta
from prazos import (pascoa, feriados_moveis, eh_dia_util, calcular_prazo,
                    dias_uteis_entre, em_recesso_forense, recuar_dias_uteis)

ok = fail = 0
def check(nome, cond, detalhe=""):
    global ok, fail
    if cond:
        ok += 1; print(f"  PASS  {nome}")
    else:
        fail += 1; print(f"  FALHA {nome}  {detalhe}")

print("\n[1] Páscoa (referência para todos os feriados móveis)")
check("Páscoa 2024 = 31/03", pascoa(2024) == date(2024, 3, 31), pascoa(2024))
check("Páscoa 2025 = 20/04", pascoa(2025) == date(2025, 4, 20), pascoa(2025))
check("Páscoa 2026 = 05/04", pascoa(2026) == date(2026, 4, 5), pascoa(2026))
check("Páscoa 2027 = 28/03", pascoa(2027) == date(2027, 3, 28), pascoa(2027))

print("\n[2] Feriados móveis derivados")
m26 = feriados_moveis(2026)
check("Carnaval (terça) 2026 = 17/02", date(2026, 2, 17) in m26)
check("Sexta-feira Santa 2026 = 03/04", date(2026, 4, 3) in m26)
check("Corpus Christi 2026 = 04/06", date(2026, 6, 4) in m26)
check("Carnaval não é dia útil", not eh_dia_util(date(2026, 2, 17)))
check("Sexta Santa não é dia útil", not eh_dia_util(date(2026, 4, 3)))

print("\n[3] Dias úteis básicos")
check("Sábado não é útil", not eh_dia_util(date(2026, 7, 18)))
check("Domingo não é útil", not eh_dia_util(date(2026, 7, 19)))
check("Segunda comum é útil", eh_dia_util(date(2026, 7, 20)))
check("Natal não é útil", not eh_dia_util(date(2026, 12, 25)))

print("\n[4] Cível — 15 dias úteis (CPC art. 219)")
r = calcular_prazo(date(2026, 3, 2), 15, "civel")     # 02/03/26 = segunda
check("publicação = 1º dia útil seguinte", r["publicacao"] == date(2026, 3, 3))
check("início = dia útil seguinte à publicação", r["inicio_contagem"] == date(2026, 3, 4))
check("data fatal cai em dia útil", eh_dia_util(r["data_fatal"]))
check("15 dias úteis a partir do início",
      dias_uteis_entre(r["inicio_contagem"], r["data_fatal"]) == 14, r["data_fatal"])
check("prazo interno vem antes do fatal", r["prazo_interno"] < r["data_fatal"])

print("\n[5] Cível atravessando feriado móvel (Carnaval 2026)")
r = calcular_prazo(date(2026, 2, 9), 15, "civel")
check("fatal não cai em feriado/fim de semana", eh_dia_util(r["data_fatal"]))
check("pulou o Carnaval (fatal > 17/02+15d corridos)", r["data_fatal"] > date(2026, 3, 4), r["data_fatal"])

print("\n[6] Recesso (CPC art. 220) — prazos cíveis suspensos 20/12 a 20/01")
check("22/12 está no recesso", em_recesso_forense(date(2026, 12, 22)))
check("15/01 está no recesso", em_recesso_forense(date(2027, 1, 15)))
check("21/01 NÃO está no recesso", not em_recesso_forense(date(2027, 1, 21)))
r = calcular_prazo(date(2026, 12, 15), 15, "civel")
check("fatal atravessa o recesso e cai depois de 20/01",
      r["data_fatal"] > date(2027, 1, 20), r["data_fatal"])
check("dias_uteis_entre concorda com o motor (bug antigo)",
      dias_uteis_entre(r["inicio_contagem"], r["data_fatal"]) == 14,
      dias_uteis_entre(r["inicio_contagem"], r["data_fatal"]))

print("\n[7] Criminal — dias corridos (CPP art. 798)")
r = calcular_prazo(date(2026, 3, 2), 10, "criminal")
check("10 dias corridos a partir de 03/03", r["data_fatal"] >= date(2026, 3, 12))
check("fatal prorrogado para dia útil", eh_dia_util(r["data_fatal"]))
r = calcular_prazo(date(2026, 3, 5), 5, "criminal")   # cairia sábado 11/03? -> prorroga
check("prazo criminal curto prorroga p/ dia útil", eh_dia_util(r["data_fatal"]), r["data_fatal"])
check("criminal é mais curto que cível de mesmo nº de dias",
      calcular_prazo(date(2026, 3, 2), 15, "criminal")["data_fatal"]
      < calcular_prazo(date(2026, 3, 2), 15, "civel")["data_fatal"])

print("\n[8] Área desconhecida usa a contagem mais CEDO")
from prazos import area_para_calculo
check("area vazia -> criminal (corridos, data mais cedo)",
      area_para_calculo("") == "criminal")
check("a_confirmar -> criminal", area_para_calculo("a_confirmar") == "criminal")
check("civel permanece civel", area_para_calculo("civel") == "civel")
check("criminal permanece criminal", area_para_calculo("criminal") == "criminal")
d_desc = calcular_prazo(date(2026, 3, 2), 15, area_para_calculo(""))["data_fatal"]
d_civ = calcular_prazo(date(2026, 3, 2), 15, "civel")["data_fatal"]
check("desconhecida vence ANTES da cível (protege)", d_desc < d_civ,
      f"{d_desc} vs {d_civ}")

print("\n[9] Margem de segurança")
d = recuar_dias_uteis(date(2026, 3, 24), 3)
check("recuar 3 dias úteis cai em dia útil", eh_dia_util(d), d)
check("recuo é anterior à data original", d < date(2026, 3, 24))

print("\n[9] Disponibilização x publicação (o bug batido contra o PJe)")
# Caso real: Diário 03/07 (sexta), publicação/ciência 06/07 (segunda),
# prazo 15 dias úteis, fatal correto no PJe = 27/07.
# Partindo da DISPONIBILIZAÇÃO 03/07, o motor avança para a publicação sozinho:
r_disp = calcular_prazo(date(2026, 7, 3), 15, "civel", tipo_data="disponibilizacao")
check("da disponibilização 03/07 -> fatal 27/07",
      r_disp["data_fatal"] == date(2026, 7, 27), r_disp["data_fatal"])
# Partindo da PUBLICAÇÃO 06/07 (o que o DJEN entrega), NÃO avança de novo:
r_pub = calcular_prazo(date(2026, 7, 6), 15, "civel", tipo_data="publicacao")
check("da publicação 06/07 -> fatal 27/07 (não conta dia extra)",
      r_pub["data_fatal"] == date(2026, 7, 27), r_pub["data_fatal"])
# As duas rotas têm que chegar na MESMA data — é o ponto do parâmetro.
check("disponibilização e publicação convergem",
      r_disp["data_fatal"] == r_pub["data_fatal"])
# Regressão do erro original: tratar a publicação como disponibilização
# (default) produz a data ERRADA de 28/07 — provando que o parâmetro importa.
r_errado = calcular_prazo(date(2026, 7, 6), 15, "civel")  # default disponibilizacao
check("tratar publicação como disponibilização erra em 1 dia (28/07)",
      r_errado["data_fatal"] == date(2026, 7, 28), r_errado["data_fatal"])

print("\n[10] O pipeline aplica a semântica por fonte")
import db as _db
import pipeline as _pl
import os as _os
_os.environ.setdefault("DB_DIR", "/tmp/tp_" + str(_os.getpid()))
_db.init()
_pl.processar_publicacoes([{
    "processo": "10053867920264013504", "sistema": "PJe",
    "orgao": "Juizado Especial Cível", "data_disponibilizacao": date(2026, 7, 6),
    "teor": "Fica a parte intimada para juntar aos autos, no prazo de "
            "15 (quinze) dias, sob pena de indeferimento"}])
_p = _db.listar_prazos()[0]
check("publicação do PJe via pipeline -> fatal 27/07",
      str(_p["data_fatal"]) == "2026-07-27", _p["data_fatal"])

print(f"\n{'='*50}\n{ok} passaram, {fail} falharam\n{'='*50}")
raise SystemExit(1 if fail else 0)
