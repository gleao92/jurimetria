"""Fluxo completo dos módulos de escritório (tarefas, financeiro, documentos,
relatórios). Uso: python test_escritorio.py"""
from datetime import date, timedelta

import db, tarefas, financeiro, documentos, relatorios

print(f"BACKEND: {'POSTGRES' if db.USA_POSTGRES else 'SQLITE'}")
db.init()

con = db.conectar()
for t in ("tarefas", "honorarios", "parcelas", "documentos"):
    con.execute(f"DELETE FROM {t}")
con.commit(); con.close()
print(" banco limpo")

# ── tarefas ──────────────────────────────────────────────────────────
tid = tarefas.criar("Ligar para o cliente", responsavel="Dr. Fulano",
                    cliente="Marcos", prioridade="alta", autor="Dr. Fulano")
assert len(tarefas.listar(status="aberta")) == 1
tarefas.concluir(tid, "Dr. Fulano")
assert tarefas.contagem_abertas() == 0
assert len(tarefas.listar(status="concluida")) == 1
tarefas.reabrir(tid, "Dr. Fulano")
assert tarefas.contagem_abertas() == 1
print(" tarefas: OK")

# ── financeiro ───────────────────────────────────────────────────────
hoje = date.today()
hid = financeiro.criar_honorario(
    "Marcos A. de Souza", "0007654-32.2026.8.09.0100", "fixo", 3000.0,
    "Honorário contratual", "Dr. Fulano",
    parcelas=[(1000.0, hoje - timedelta(days=5)),
             (1000.0, hoje + timedelta(days=25)),
             (1000.0, hoje + timedelta(days=55))])
parcelas = financeiro.listar_parcelas(honorario_id=hid)
assert len(parcelas) == 3
# a primeira já venceu -> deve virar 'atrasado' ao listar
atrasadas = [p for p in parcelas if p["status"] == "atrasado"]
assert len(atrasadas) == 1, f"esperado 1 atrasada, veio {len(atrasadas)}"
financeiro.marcar_pago(atrasadas[0]["id"], "Dr. Fulano")
r = financeiro.resumo(hoje)
assert r["contratado"] == 3000.0
assert r["recebido"] == 1000.0
assert r["atrasado"] == 0.0
assert r["pendente"] == 2000.0
print(" financeiro:", r)

# ── documentos ───────────────────────────────────────────────────────
did = documentos.salvar("contrato.pdf", b"conteudo de teste" * 100,
                        "contrato", cliente="Marcos A. de Souza",
                        autor="Dr. Fulano")
listados = documentos.listar(cliente="Marcos A. de Souza")
assert len(listados) == 1
conteudo = documentos.obter_conteudo(did)
assert conteudo == b"conteudo de teste" * 100, "conteúdo não bate após round-trip"
try:
    documentos.salvar("grande.bin", b"x" * (21 * 1024 * 1024))
    assert False, "deveria ter recusado arquivo grande"
except ValueError:
    pass
documentos.excluir(did, "Dr. Fulano")
assert documentos.listar() == []
print(" documentos: OK")

# ── relatórios ───────────────────────────────────────────────────────
painel = relatorios.painel_geral(hoje)
assert "financeiro" in painel and "carga_por_responsavel" in painel
assert painel["carga_por_responsavel"].get("Dr. Fulano") == 1
print(" relatórios:", {k: painel[k] for k in ("financeiro", "carga_por_responsavel")})

print(" >>> TUDO OK\n")
