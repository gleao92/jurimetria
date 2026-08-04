"""Roda o fluxo completo no banco configurado. Uso: python test_backends.py"""
import db, auth, pipeline
from datetime import date

print(f"BACKEND: {'POSTGRES' if db.USA_POSTGRES else 'SQLITE'}")
db.init(); auth.init()

# Limpa antes de rodar — teste que só passa em banco virgem não é teste.
con = db.conectar()
for t in ("prazos", "publicacoes", "processos", "log", "usuarios"):
    con.execute(f"DELETE FROM {t}")
con.commit(); con.close()
print(" banco limpo")

ok, msg = auth.criar_usuario("drfulano", "Dr. Fulano", "senhaforte1", "advogado")
print(" criar usuário:", ok, msg)
print(" duplicado    :", auth.criar_usuario("drfulano", "x", "senhaforte1"))  # testa rollback
u = auth.verificar("drfulano", "senhaforte1")
assert u and auth.pode_confirmar(u), "login/papel falhou"
print(" login+papel  : OK")

r = pipeline.carregar_exemplo()
print(" ingestão     :", r)
r2 = pipeline.carregar_exemplo()
assert r2["prazos_criados"] == 0, "idempotência quebrou"
print(" idempotente  : OK")

ps = db.listar_prazos(["pendente_revisao"])
assert len(ps) == 7, f"esperado 7, veio {len(ps)}"
alvo = ps[0]
db.confirmar(alvo["id"], u["nome"], 15, date(2026, 8, 20), date(2026, 8, 17), "contestação", "ok")
db.marcar_cumprido(alvo["id"], u["nome"])
dep = [p for p in db.listar_prazos() if p["id"] == alvo["id"]][0]
assert dep["status"] == "cumprido" and dep["confirmado_por"] == u["nome"]
print(" confirmar+cumprir: OK")

sem = [p for p in db.listar_prazos() if p["data_fatal"] is None]
print(f" sem data (a identificar): {len(sem)}")
print(f" log: {len(db.ultimos_logs())} registros")
print(" >>> TUDO OK\n")
