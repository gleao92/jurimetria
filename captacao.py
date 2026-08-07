"""
Captação — funil de clientes em potencial, antes de virarem processo.

POR QUE ISTO FALTAVA
Todo o resto do sistema (prazo, financeiro, documento) só existe depois que
alguém já é cliente. Mas o escritório perde controle bem antes disso: quem
ligou e não foi respondido, quem teve reunião marcada e sumiu, quem recebeu
proposta e não retornou. Sem um lugar pra isso, cada contato em potencial
vive na memória de quem atendeu — e se essa pessoa sai do escritório, o
histórico vai junto.

ESTÁGIOS, NÃO STATUS BINÁRIO
"Fechado" ou "não fechado" esconde ONDE a captação está travando. Estágios
em sequência (novo -> contato -> reunião -> proposta -> ganho/perdido)
permitem ver, por exemplo, "a maioria trava depois da proposta" — informação
que muda o que o escritório precisa consertar.
"""

import hashlib
from datetime import datetime

import db
from cache_wrap import leitura, limpar

ESTAGIOS = ["novo", "contato_feito", "reuniao_marcada", "proposta_enviada",
           "ganho", "perdido"]

ROTULOS_ESTAGIO = {
    "novo": "Novo contato", "contato_feito": "Contato feito",
    "reuniao_marcada": "Reunião marcada", "proposta_enviada": "Proposta enviada",
    "ganho": "Ganho", "perdido": "Perdido",
}

ORIGENS = {"indicacao": "Indicação", "site": "Site", "telefone": "Telefone",
          "redes_sociais": "Redes sociais", "outro": "Outro"}


def init():
    with db.conectar() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY, nome TEXT, contato TEXT, origem TEXT,
            area_interesse TEXT, valor_estimado REAL, estagio TEXT DEFAULT 'novo',
            responsavel TEXT, observacao TEXT, motivo_perda TEXT,
            criado_por TEXT, criado_em TEXT, atualizado_em TEXT)""")


def _novo_id(*partes) -> str:
    base = "|".join(str(p) for p in partes) + datetime.now().isoformat()
    return "l" + hashlib.sha1(base.encode()).hexdigest()[:14]


def criar(nome: str, contato: str = "", origem: str = "outro",
         area_interesse: str = "", valor_estimado: float = 0.0,
         responsavel: str = "", observacao: str = "", autor: str = "") -> str:
    lid = _novo_id(nome, contato)
    agora = datetime.now().isoformat(timespec="seconds")
    with db.conectar() as con:
        con.execute("""INSERT INTO leads
            (id,nome,contato,origem,area_interesse,valor_estimado,estagio,
             responsavel,observacao,criado_por,criado_em,atualizado_em)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (lid, nome.strip(), contato.strip(),
             origem if origem in ORIGENS else "outro", area_interesse.strip(),
             float(valor_estimado or 0), "novo", responsavel.strip(),
             observacao.strip(), autor, agora, agora))
    db.registrar("lead_criado", lid, f"{nome} · {ORIGENS.get(origem, origem)}")
    limpar()
    return lid


def mover_estagio(lid: str, novo_estagio: str, autor: str,
                  motivo_perda: str = "") -> None:
    if novo_estagio not in ESTAGIOS:
        raise ValueError(f"estágio inválido: {novo_estagio}")
    with db.conectar() as con:
        con.execute("""UPDATE leads SET estagio=?, motivo_perda=?,
                       atualizado_em=? WHERE id=?""",
                    (novo_estagio, motivo_perda if novo_estagio == "perdido" else "",
                     datetime.now().isoformat(timespec="seconds"), lid))
    db.registrar("lead_movido", lid,
                 f"para {ROTULOS_ESTAGIO.get(novo_estagio, novo_estagio)} por {autor}"
                 + (f" · motivo: {motivo_perda}" if motivo_perda else ""))
    limpar()


def atualizar(lid: str, campos: dict, autor: str) -> None:
    permitidos = {"nome", "contato", "origem", "area_interesse",
                  "valor_estimado", "responsavel", "observacao"}
    campos = {k: v for k, v in campos.items() if k in permitidos}
    if not campos:
        return
    campos["atualizado_em"] = datetime.now().isoformat(timespec="seconds")
    with db.conectar() as con:
        con.execute(f"UPDATE leads SET {','.join(f'{k}=?' for k in campos)} "
                    f"WHERE id=?", (*campos.values(), lid))
    db.registrar("lead_editado", lid, f"por {autor}: {list(campos)}")
    limpar()


def excluir(lid: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("DELETE FROM leads WHERE id=?", (lid,))
    db.registrar("lead_excluido", lid, f"por {autor}")
    limpar()


@leitura()
def listar(estagio: str = None) -> list[dict]:
    con = db.conectar()
    sql = "SELECT * FROM leads"
    args = ()
    if estagio:
        sql += " WHERE estagio = ?"; args = (estagio,)
    sql += " ORDER BY atualizado_em DESC"
    r = [dict(x) for x in con.execute(sql, args).fetchall()]
    con.close()
    return r


def por_estagio() -> dict:
    """{estagio: [leads]} — formato que o quadro Kanban consome."""
    saida = {e: [] for e in ESTAGIOS}
    for lead in listar():
        saida.setdefault(lead["estagio"], []).append(lead)
    return saida


def funil_resumo() -> dict:
    """Quantos leads em cada estágio + taxa de conversão (ganho / (ganho+perdido)),
    que é a métrica que diz se o funil está funcionando ou só acumulando."""
    contagem = {e: 0 for e in ESTAGIOS}
    valor_aberto = 0.0
    for lead in listar():
        contagem[lead["estagio"]] = contagem.get(lead["estagio"], 0) + 1
        if lead["estagio"] not in ("ganho", "perdido"):
            valor_aberto += lead.get("valor_estimado") or 0
    decididos = contagem["ganho"] + contagem["perdido"]
    taxa = (contagem["ganho"] / decididos * 100) if decididos else None
    return {"contagem": contagem, "valor_aberto": valor_aberto, "taxa_conversao": taxa}
