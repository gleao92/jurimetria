"""
Regras de classificação — guardadas no banco, editáveis pela tela.

POR QUE NÃO UM ARQUIVO JSON
A sugestão original era mover as regras para um `.json` "para que advogados
revisem os termos sem risco de quebrar a sintaxe do Python". A intenção está
certa; o meio, não:

  - JSON é MAIS frágil que Python para quem não programa. Uma vírgula a mais
    e o arquivo não carrega — sem mensagem que o advogado entenda, e num
    módulo que decide prazo isso significa o sistema parar de classificar.
  - Ninguém vai abrir um arquivo de texto no servidor. Advogado mexe no que
    tem tela.
  - Arquivo solto não tem histórico: não dá para saber quem mudou o quê,
    justamente num ponto que altera cálculo de prazo.

Guardar no banco resolve os três: a edição é por formulário validado, o log
de auditoria registra autor e data, e um valor inválido é recusado na hora em
vez de derrubar o carregamento.

As regras de fábrica ficam em PADRAO e são semeadas na primeira execução.
"""

from datetime import datetime

import db

# (padrão no texto, rótulo do ato, dias presumidos)
# Compostos primeiro: "manifeste-se sobre a contestação" é RÉPLICA, não
# contestação — casar só a palavra rotula errado.
PADRAO = [
    ("sobre a contestação", "réplica", 15),
    ("sobre a defesa", "réplica", 15),
    ("sobre o laudo", "manifestar sobre laudo", 15),
    ("sobre a perícia", "manifestar sobre perícia", 15),
    ("sobre os documentos", "manifestar sobre documentos", None),
    ("sobre os embargos", "impugnar embargos", 15),
    ("resposta à acusação", "resposta à acusação", 10),
    ("alegações finais", "alegações finais", 5),
    ("memoriais", "alegações finais (memoriais)", 5),
    ("embargos de declaração", "embargos de declaração", 5),
    ("contrarrazões", "contrarrazões", 15),
    ("contestação", "contestação", 15),
    ("emenda", "emendar a inicial", 15),
    ("emendar", "emendar a inicial", 15),
    ("juntar aos autos", "juntar documentos", None),
    ("juntada", "juntar documentos", None),
    ("junte-se", "juntar documentos", None),
    ("comprovante", "juntar documentos", None),
    ("impugnação", "impugnação", 15),
    ("réplica", "réplica", 15),
    ("apelação", "apelação", 15),
    ("agravo", "agravo", 15),
    ("especifiquem as provas", "especificar provas", 5),
    ("especifique", "especificar provas", 5),
    ("provas que pretende", "especificar provas", 5),
    ("audiência", "audiência designada", None),
    ("perícia", "perícia", None),
    ("laudo", "manifestar sobre laudo", 15),
    ("recurso", "recurso", 15),
    ("manifest", "manifestação", None),
    ("cumpra", "cumprimento de determinação", None),
    ("ato ordinatório", "determinação do juízo", None),
]

_cache = None


def init():
    with db.conectar() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS regras_classificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT, padrao TEXT, rotulo TEXT,
            dias INTEGER, ordem INTEGER, ativa INTEGER DEFAULT 1,
            autor TEXT, criada_em TEXT)"""
            if not db.USA_POSTGRES else
            """CREATE TABLE IF NOT EXISTS regras_classificacao (
            id SERIAL PRIMARY KEY, padrao TEXT, rotulo TEXT,
            dias INTEGER, ordem INTEGER, ativa INTEGER DEFAULT 1,
            autor TEXT, criada_em TEXT)""")
    _semear()


def _semear():
    """Grava as regras de fábrica só se a tabela estiver vazia."""
    con = db.conectar()
    n = con.execute("SELECT COUNT(*) c FROM regras_classificacao").fetchone()["c"]
    if n:
        con.close(); return
    agora = datetime.now().isoformat(timespec="seconds")
    for i, (padrao, rotulo, dias) in enumerate(PADRAO):
        con.execute("""INSERT INTO regras_classificacao
            (padrao,rotulo,dias,ordem,ativa,autor,criada_em)
            VALUES (?,?,?,?,1,?,?)""",
            (padrao, rotulo, dias, i, "padrão de fábrica", agora))
    con.commit(); con.close()
    _invalidar()


def _invalidar():
    global _cache
    _cache = None


def listar(so_ativas: bool = False) -> list[dict]:
    con = db.conectar()
    sql = "SELECT * FROM regras_classificacao"
    if so_ativas:
        sql += " WHERE ativa = 1"
    sql += " ORDER BY ordem, id"
    r = [dict(x) for x in con.execute(sql).fetchall()]
    con.close()
    return r


def carregar() -> list[tuple]:
    """Regras ativas, em ordem, para o classificador. Em cache — a
    classificação roda uma vez por publicação e ir ao banco a cada chamada
    tornaria a ingestão de 60 publicações desnecessariamente lenta."""
    global _cache
    if _cache is None:
        try:
            todas = listar()
            _cache = [(r["padrao"].lower(), r["rotulo"], r["dias"])
                      for r in todas if r.get("padrao") and r.get("ativa")]
            # Diferença que importa: tabela VAZIA significa banco novo ou
            # indisponível, e aí valem as de fábrica. Tabela com regras, mas
            # todas desativadas, é escolha deliberada do usuário — voltar às
            # de fábrica por trás dele faria o sistema classificar de um jeito
            # que ele acabou de desligar.
            if not todas:
                _cache = [(p.lower(), r, d) for p, r, d in PADRAO]
        except Exception:
            _cache = [(p.lower(), r, d) for p, r, d in PADRAO]
    return _cache


def validar(padrao: str, rotulo: str, dias) -> tuple[bool, str]:
    if not (padrao or "").strip():
        return False, "O trecho a procurar não pode ficar vazio."
    if len((padrao or "").strip()) < 3:
        return False, "Trecho curto demais — casaria com quase tudo."
    if not (rotulo or "").strip():
        return False, "Informe o nome do ato."
    if dias not in (None, "") and not (str(dias).isdigit() and 1 <= int(dias) <= 180):
        return False, "Dias deve ficar entre 1 e 180, ou vazio."
    return True, ""


def salvar(regras: list[dict], autor: str) -> tuple[int, list[str]]:
    """Substitui o conjunto de regras. Devolve (quantas, erros)."""
    erros = []
    limpas = []
    for i, r in enumerate(regras):
        padrao = (r.get("padrao") or "").strip()
        rotulo = (r.get("rotulo") or "").strip()
        dias = r.get("dias")
        if not padrao and not rotulo:
            continue                  # linha em branco: ignora
        ok, msg = validar(padrao, rotulo, dias)
        if not ok:
            erros.append(f"linha {i+1}: {msg}")
            continue
        limpas.append((padrao, rotulo,
                       int(dias) if str(dias).isdigit() else None,
                       i, 1 if r.get("ativa", True) else 0))
    if erros:
        return 0, erros

    agora = datetime.now().isoformat(timespec="seconds")
    with db.conectar() as con:
        con.execute("DELETE FROM regras_classificacao")
        for padrao, rotulo, dias, ordem, ativa in limpas:
            con.execute("""INSERT INTO regras_classificacao
                (padrao,rotulo,dias,ordem,ativa,autor,criada_em)
                VALUES (?,?,?,?,?,?,?)""",
                (padrao, rotulo, dias, ordem, ativa, autor, agora))
    _invalidar()
    db.registrar("regras_alteradas", autor, f"{len(limpas)} regras")
    return len(limpas), []


def restaurar_padrao(autor: str) -> int:
    with db.conectar() as con:
        con.execute("DELETE FROM regras_classificacao")
    _invalidar()
    _semear()
    db.registrar("regras_restauradas", autor, f"{len(PADRAO)} de fábrica")
    return len(PADRAO)
