"""
Agenda — exporta os prazos em iCalendar (.ics).

POR QUE .ics E NÃO INTEGRAÇÃO COM O GOOGLE
O arquivo .ics é entendido por Google Agenda, Outlook, Apple e praticamente
tudo. Não exige OAuth, cadastro de aplicativo, token que expira nem guardar
credencial de e-mail do advogado. Ele importa uma vez e os prazos aparecem no
calendário que já usa.

POR QUE USAR A BIBLIOTECA `icalendar`
A versão anterior montava o RFC 5545 na mão: dobra de linha a cada 75 octetos,
escape de vírgula, ponto e vírgula e quebra de linha. Funcionava e estava
testado, mas era código meu resolvendo um problema já resolvido — e as bordas
(Unicode, caractere combinante, campo muito longo) são exatamente onde uma
implementação artesanal falha em silêncio, num arquivo que o advogado só
descobre quebrado quando o compromisso não aparece.

O QUE VAI PARA A AGENDA
Cada prazo confirmado vira DOIS compromissos:
  - o PRAZO INTERNO, com alarme — o dia de trabalhar a peça;
  - a DATA FATAL, com alarme na véspera e no dia — o limite real.
Quem marca só a data fatal descobre o prazo no dia em que ele acaba.

Prazo ainda não confirmado NÃO entra. Data sugerida por classificação
automática, sem revisão do advogado, não pode virar compromisso.
"""

from datetime import date, datetime, time, timedelta

from icalendar import Alarm, Calendar, Event

PRODID = "-//Tempestivo//Controladoria de Prazos//PT-BR"


def _data(x):
    if isinstance(x, date):
        return x
    return date.fromisoformat(str(x)[:10]) if x else None


def _alarme(dias_antes: int, texto: str) -> Alarm:
    a = Alarm()
    a.add("action", "DISPLAY")
    a.add("description", texto)
    a.add("trigger", timedelta(days=-dias_antes) if dias_antes
          else timedelta(hours=9))
    return a


def _evento(uid: str, dia: date, titulo: str, descricao: str,
            alarmes: list[int]) -> Event:
    ev = Event()
    ev.add("uid", uid)
    ev.add("dtstamp", datetime.now())
    ev.add("dtstart", dia)                    # VALUE=DATE (dia inteiro)
    ev.add("dtend", dia + timedelta(days=1))  # DTEND é exclusivo
    ev.add("summary", titulo)
    ev.add("description", descricao)
    ev.add("transp", "TRANSPARENT")
    ev.add("categories", ["PRAZO PROCESSUAL"])
    for d in alarmes:
        ev.add_component(_alarme(d, titulo))
    return ev


def gerar_ics(prazos: list[dict], apenas_confirmados: bool = True,
              comps: list[dict] = None) -> str:
    cal = Calendar()
    cal.add("prodid", PRODID)
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "Prazos processuais")
    cal.add("x-wr-timezone", "America/Sao_Paulo")

    for p in prazos:
        if apenas_confirmados and p.get("status") != "confirmado":
            continue
        fatal = _data(p.get("data_fatal"))
        if not fatal:
            continue

        cliente = p.get("cliente") or "cliente não identificado"
        ato = p.get("ato") or "Prazo"
        proc = p.get("processo") or ""
        desc = (f"Cliente: {cliente}\n"
                f"Processo: {proc}\n"
                f"Área: {p.get('area') or 'a confirmar'}\n"
                f"Confirmado por: {p.get('confirmado_por') or '—'}\n\n"
                f"Gerado pelo Tempestivo. Confira sempre nos autos.")

        # UID estável: reimportar ATUALIZA o evento em vez de duplicar.
        base = f"{p.get('id', proc)}@tempestivo"

        interno = _data(p.get("prazo_interno"))
        if interno and interno < fatal:
            cal.add_component(_evento(
                f"i-{base}", interno, f"Preparar: {ato} — {cliente}",
                desc + f"\n\nData fatal: {fatal.strftime('%d/%m/%Y')}", [1]))

        cal.add_component(_evento(
            f"f-{base}", fatal, f"PRAZO FATAL: {ato} — {cliente}", desc, [1, 0]))

    if comps:
        adicionar_compromissos(cal, comps)
    return cal.to_ical().decode("utf-8")


def adicionar_compromissos(cal: Calendar, comps: list[dict]) -> int:
    """Audiência e reunião no MESMO arquivo dos prazos.

    Separar em dois calendários obrigaria o advogado a conferir duas listas —
    exatamente o que o sistema deveria eliminar. Compromisso com hora vira
    evento com horário; sem hora, dia inteiro.
    """
    import compromissos as _c
    n = 0
    for c in comps:
        if c.get("cancelado"):
            continue
        try:
            dia = date.fromisoformat(str(c["data"])[:10])
        except (ValueError, KeyError, TypeError):
            continue
        rotulo = _c.TIPOS.get(c.get("tipo"), {}).get("rotulo", "Compromisso")
        titulo = f"{rotulo}: {c.get('titulo') or ''}".strip(": ")
        desc = "\n".join(filter(None, [
            f"Cliente: {c['cliente']}" if c.get("cliente") else "",
            f"Local: {c['local']}" if c.get("local") else "",
            f"Processo: {c['processo']}" if c.get("processo") else "",
            c.get("observacao") or "",
            "\nRegistrado no Tempestivo."]))

        ev = Event()
        ev.add("uid", f"c-{c['id']}@tempestivo")
        ev.add("dtstamp", datetime.now())
        hora = (c.get("hora") or "").strip()
        if hora and ":" in hora:
            try:
                h, m = [int(x) for x in hora.split(":")[:2]]
                inicio = datetime.combine(dia, time(h, m))
                ev.add("dtstart", inicio)
                ev.add("dtend", inicio + timedelta(minutes=int(c.get("duracao_min") or 60)))
            except ValueError:
                ev.add("dtstart", dia)
                ev.add("dtend", dia + timedelta(days=1))
        else:
            ev.add("dtstart", dia)
            ev.add("dtend", dia + timedelta(days=1))
        ev.add("summary", titulo)
        ev.add("description", desc)
        if c.get("local"):
            ev.add("location", c["local"])
        # Audiência avisa com 1 dia e 1 hora de antecedência: perder audiência
        # tem consequência processual imediata.
        ev.add_component(_alarme(1, titulo))
        if c.get("tipo") in ("audiencia", "pericia"):
            al = Alarm()
            al.add("action", "DISPLAY")
            al.add("description", titulo)
            al.add("trigger", timedelta(hours=-1))
            ev.add_component(al)
        cal.add_component(ev)
        n += 1
    return n


def resumo(prazos: list[dict], apenas_confirmados: bool = True) -> dict:
    """Quantos compromissos o arquivo terá — para avisar antes de baixar."""
    def vale(p):
        return (not apenas_confirmados or p.get("status") == "confirmado") \
            and _data(p.get("data_fatal"))

    n = sum(1 for p in prazos if vale(p))
    com_interno = sum(
        1 for p in prazos if vale(p) and _data(p.get("prazo_interno"))
        and _data(p["prazo_interno"]) < _data(p["data_fatal"]))
    return {"prazos": n, "eventos": n + com_interno}
