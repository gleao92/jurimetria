"""Testes das regras editáveis. python test_regras.py"""
import os, tempfile
os.environ["DB_DIR"] = tempfile.mkdtemp()
import db, regras
from classificacao import classificar

ok = fail = 0
def check(n, c, e=""):
    global ok, fail
    if c: ok += 1; print(f"  PASS  {n}")
    else: fail += 1; print(f"  FALHA {n} → {e}")

db.init()

print("\n[1] Semeadura")
check("regras de fábrica gravadas", len(regras.listar()) == len(regras.PADRAO))
check("classificador usa o banco",
      classificar("apresentar contestação em 15 dias")["ato"] == "contestação")
regras.init()
check("semear de novo não duplica", len(regras.listar()) == len(regras.PADRAO))

print("\n[2] Validação — recusa antes de gravar")
casos = [("", "ato", 5), ("ab", "ato", 5), ("valido", "", 5),
         ("valido", "ato", 0), ("valido", "ato", 999)]
for p, r, dias in casos:
    check(f"recusa ({p!r},{r!r},{dias})", not regras.validar(p, r, dias)[0])
check("aceita regra boa", regras.validar("intimação para pagar", "pagamento", 15)[0])

print("\n[3] Edição pelo advogado")
atuais = [{"padrao": r["padrao"], "rotulo": r["rotulo"], "dias": r["dias"],
           "ativa": True} for r in regras.listar()]
atuais.insert(0, {"padrao": "implantação do benefício",
                  "rotulo": "acompanhar implantação", "dias": 30, "ativa": True})
n, erros = regras.salvar(atuais, "Dr. Teste")
check("salvou sem erro", not erros, erros)
check("regra nova classifica",
      classificar("Intime-se para implantação do benefício")["ato"]
      == "acompanhar implantação")

print("\n[4] Ordem importa — a primeira que casar vence")
sub = [{"padrao": "sobre a contestação", "rotulo": "réplica", "dias": 15, "ativa": True},
       {"padrao": "contestação", "rotulo": "contestação", "dias": 15, "ativa": True}]
regras.salvar(sub, "Dr. Teste")
check("composto antes da palavra solta",
      classificar("manifeste-se sobre a contestação")["ato"] == "réplica")
regras.salvar(list(reversed(sub)), "Dr. Teste")
check("invertendo a ordem, muda o resultado",
      classificar("manifeste-se sobre a contestação")["ato"] == "contestação")

print("\n[5] Desativar e restaurar")
regras.salvar([{"padrao": "contestação", "rotulo": "contestação",
                "dias": 15, "ativa": False}], "Dr. Teste")
check("regra desativada não classifica",
      classificar("apresentar contestação")["ato"] == "a identificar")
regras.restaurar_padrao("Dr. Teste")
check("restaura as de fábrica", len(regras.listar()) == len(regras.PADRAO))
check("volta a classificar",
      classificar("apresentar contestação")["ato"] == "contestação")

print("\n[6] Erro em uma linha não grava nenhuma")
antes = len(regras.listar())
n2, erros2 = regras.salvar([{"padrao": "ok agora", "rotulo": "bom", "dias": 5,
                             "ativa": True},
                            {"padrao": "x", "rotulo": "ruim", "dias": 5,
                             "ativa": True}], "Dr. Teste")
check("recusa o lote inteiro", n2 == 0 and erros2)
check("regras anteriores intactas", len(regras.listar()) == antes)

print(f"\n{'='*46}\n{ok} passaram, {fail} falharam\n{'='*46}")
raise SystemExit(1 if fail else 0)
