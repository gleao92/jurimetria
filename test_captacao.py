"""Fluxo do funil de captação. Uso: python test_captacao.py"""
import db, captacao

print(f"BACKEND: {'POSTGRES' if db.USA_POSTGRES else 'SQLITE'}")
db.init()

con = db.conectar()
con.execute("DELETE FROM leads")
con.commit(); con.close()
print(" banco limpo")

l1 = captacao.criar("Maria Souza", "11999990000", "indicacao", "cível",
                    5000.0, "Dr. Fulano", "Indicação de outro cliente",
                    autor="Dr. Fulano")
l2 = captacao.criar("João Lima", "62988887777", "site", "criminal", 8000.0,
                    "Dr. Fulano", autor="Dr. Fulano")
assert len(captacao.listar()) == 2
assert len(captacao.por_estagio()["novo"]) == 2

captacao.mover_estagio(l1, "contato_feito", "Dr. Fulano")
captacao.mover_estagio(l1, "reuniao_marcada", "Dr. Fulano")
captacao.mover_estagio(l1, "ganho", "Dr. Fulano")
captacao.mover_estagio(l2, "perdido", "Dr. Fulano", motivo_perda="Não retornou contato")

r = captacao.funil_resumo()
assert r["contagem"]["ganho"] == 1
assert r["contagem"]["perdido"] == 1
assert r["taxa_conversao"] == 50.0, f"esperado 50.0, veio {r['taxa_conversao']}"
assert r["valor_aberto"] == 0.0, "ganho/perdido não deveriam contar como 'em aberto'"
print(" funil:", r)

perdido = [l for l in captacao.listar() if l["id"] == l2][0]
assert perdido["motivo_perda"] == "Não retornou contato"
print(" motivo de perda registrado: OK")

captacao.excluir(l1, "Dr. Fulano")
assert len(captacao.listar()) == 1
print(" excluir: OK")

print(" >>> TUDO OK\n")
