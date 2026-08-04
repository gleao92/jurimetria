"""Testes do .ics.  python test_agenda.py"""
from datetime import date
import agenda

ok = fail = 0
def check(n, c, e=""):
    global ok, fail
    if c: ok += 1; print(f"  PASS  {n}")
    else: fail += 1; print(f"  FALHA {n} {e}")

prazos = [
    {"id": "abc123", "status": "confirmado", "ato": "Contestação",
     "cliente": "Fazenda Boa Vista Ltda; Filial, S/A", "processo": "1002345-67.2026.8.09.0051",
     "area": "civel", "confirmado_por": "Dr. Fulano",
     "data_fatal": "2026-08-10", "prazo_interno": "2026-08-05"},
    {"id": "def456", "status": "pendente_revisao", "ato": "Apelação",
     "cliente": "Não confirmado", "processo": "1009876-54.2026.8.09.0051",
     "data_fatal": "2026-08-12", "prazo_interno": "2026-08-07"},
    {"id": "ghi789", "status": "confirmado", "ato": "Sem data",
     "cliente": "X", "processo": "0", "data_fatal": None, "prazo_interno": None},
]

ics = agenda.gerar_ics(prazos)
print("\n[1] Estrutura")
check("abre e fecha VCALENDAR",
      ics.startswith("BEGIN:VCALENDAR") and ics.rstrip().endswith("END:VCALENDAR"))
check("linhas terminam em CRLF", "\r\n" in ics and "\n\n" not in ics)
check("tem VERSION:2.0", "VERSION:2.0" in ics)

print("\n[2] O que entra e o que não entra")
check("prazo confirmado entra", "Contestação" in ics)
check("NÃO confirmado fica de fora", "Apelação" not in ics)
check("sem data fatal fica de fora", "Sem data" not in ics)
check("2 eventos do confirmado (interno + fatal)", ics.count("BEGIN:VEVENT") == 2,
      ics.count("BEGIN:VEVENT"))

print("\n[3] Conteúdo")
check("data fatal correta", "DTSTART;VALUE=DATE:20260810" in ics)
check("prazo interno correto", "DTSTART;VALUE=DATE:20260805" in ics)
check("DTEND é o dia seguinte", "DTEND;VALUE=DATE:20260811" in ics)
check("alarme presente", "BEGIN:VALARM" in ics)
check("UID estável com o id do prazo", "abc123@tempestivo" in ics)

print("\n[4] Escape — o que quebra importação")
check("ponto e vírgula escapado", r"\;" in ics)
check("vírgula escapada", r"\," in ics)
check("quebra de linha escapada", r"\n" in ics)

print("\n[5] Dobra de linha (RFC 5545: máx. 75 octetos)")
longas = [l for l in ics.split("\r\n")
          if not l.startswith(" ") and len(l.encode("utf-8")) > 75]
check("nenhuma linha acima de 75 octetos", not longas,
      longas[0][:60] if longas else "")

p_longo = [{"id": "z", "status": "confirmado", "processo": "1002345-67.2026.8.09.0051",
            "cliente": "Companhia Agropecuária de Desenvolvimento Rural do Cerrado "
                       "Goiano Sociedade Anônima de Capital Fechado",
            "ato": "Contrarrazões de apelação com preliminar de intempestividade",
            "data_fatal": "2026-08-10", "prazo_interno": "2026-08-05"}]
ics2 = agenda.gerar_ics(p_longo)
longas2 = [l for l in ics2.split("\r\n")
           if not l.startswith(" ") and len(l.encode("utf-8")) > 75]
check("texto muito longo também é dobrado", not longas2)
check("continuação começa com espaço", "\r\n " in ics2)

print("\n[6] Resumo")
r = agenda.resumo(prazos)
check("conta 1 prazo e 2 eventos", r == {"prazos": 1, "eventos": 2}, r)

print(f"\n{'='*46}\n{ok} passaram, {fail} falharam\n{'='*46}")
raise SystemExit(1 if fail else 0)
