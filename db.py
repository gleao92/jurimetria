"""
Persistência — roda em SQLite (local) ou Postgres (nuvem), mesmo código.

Escolha automática:
  DATABASE_URL definida  -> Postgres  (nuvem)
  DATABASE_URL ausente   -> SQLite    (arquivo local controladoria.db)

>>> POR QUE ISSO IMPORTA <<<
Plataformas com disco efêmero (Streamlit Community Cloud, tiers grátis de
PaaS) APAGAM o arquivo SQLite a cada reboot/redeploy — sem aviso e sem erro.
Num sistema de prazos, perder o banco em silêncio é o pior defeito possível.
Na nuvem: ou Postgres, ou VPS com disco de verdade. Nunca SQLite em disco
efêmero.
"""

import os
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

from cache_wrap import leitura, limpar

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USA_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
# DB_DIR permite apontar o SQLite para um volume persistente (Docker/VPS).
# Sem ele, o banco fica ao lado do código — bom local, FATAL em disco efêmero.
_DIR = Path(os.environ.get("DB_DIR", "")).expanduser() if os.environ.get("DB_DIR") \
    else Path(__file__).parent
_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = _DIR / "controladoria.db"

# pendente_revisao -> confirmado -> cumprido        (ou arquivado)
STATUS = ["pendente_revisao", "confirmado", "cumprido", "arquivado"]


class _Con:
    """Camada fina para o mesmo SQL rodar nos dois bancos."""

    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, args=()):
        if USA_POSTGRES:
            s = sql.strip()
            if s.upper().startswith("INSERT OR IGNORE"):
                sql = (s.replace("INSERT OR IGNORE", "INSERT", 1).rstrip().rstrip(";")
                       + " ON CONFLICT DO NOTHING")
            sql = sql.replace("?", "%s")
        return self._raw.execute(sql, args)

    def commit(self): self._raw.commit()
    def rollback(self): self._raw.rollback()
    def close(self): self._raw.close()

    # Context manager: commita ao sair bem, desfaz e fecha se houver exceção.
    # Sem isto, um erro no meio de uma operação deixava a conexão aberta —
    # vazamento que só aparece sob carga, quando já é tarde.
    def __enter__(self):
        return self

    def __exit__(self, exc_tipo, exc, tb):
        try:
            if exc_tipo is None:
                self._raw.commit()
            else:
                self._raw.rollback()
        finally:
            self._raw.close()
        return False


def conectar() -> _Con:
    if USA_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row
        return _Con(psycopg.connect(DATABASE_URL, row_factory=dict_row))
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return _Con(con)


_SERIAL = "SERIAL PRIMARY KEY" if USA_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"

ESQUEMA = [
    """CREATE TABLE IF NOT EXISTS publicacoes (
        id TEXT PRIMARY KEY, processo TEXT, sistema TEXT,
        data_disponibilizacao TEXT, teor TEXT, capturada_em TEXT,
        fontes TEXT)""",
    """CREATE TABLE IF NOT EXISTS processos (
        numero TEXT PRIMARY KEY, cliente TEXT, area TEXT,
        sistema TEXT, tribunal TEXT, assunto TEXT)""",
    """CREATE TABLE IF NOT EXISTS prazos (
        id TEXT PRIMARY KEY, publicacao_id TEXT, processo TEXT, area TEXT,
        ato TEXT, prazo_dias INTEGER, data_fatal TEXT, prazo_interno TEXT,
        status TEXT DEFAULT 'pendente_revisao', fonte TEXT,
        confirmado_por TEXT, confirmado_em TEXT, cumprido_em TEXT,
        observacao TEXT, criado_em TEXT, trecho TEXT)""",
    f"""CREATE TABLE IF NOT EXISTS log (
        id {_SERIAL}, quando TEXT, acao TEXT, referencia TEXT, detalhe TEXT)""",
]


def init():
    con = conectar()
    for ddl in ESQUEMA:
        con.execute(ddl)
    con.commit()
    _migrar(con)
    con.close()
    for mod in ("regras", "compromissos", "tarefas", "financeiro", "documentos",
               "captacao"):
        try:
            __import__(mod).init()
        except Exception:
            pass      # sem a tabela, cada módulo cai no seu comportamento padrão


def _migrar(con):
    """Acrescenta colunas novas em bancos já existentes, sem apagar dados."""
    novas = [("prazos", "trecho", "TEXT"),
             ("publicacoes", "fontes", "TEXT")]
    for tabela, coluna, tipo in novas:
        try:
            if USA_POSTGRES:
                con.execute(f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS "
                            f"{coluna} {tipo}")
            else:
                existentes = [r[1] for r in
                              con.execute(f"PRAGMA table_info({tabela})").fetchall()]
                if coluna not in existentes:
                    con.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}")
            con.commit()
        except Exception:
            con.rollback()

    # Uma publicação = um prazo. Garantia no BANCO, não só no código: se algum
    # caminho tentar inserir a segunda, o banco recusa. Falha em silêncio (e
    # segue) se ainda houver duplicata da época em que a regra não existia —
    # nesse caso rode dedupe_prazos.sql primeiro.
    try:
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_prazos_publicacao "
                    "ON prazos (publicacao_id)")
        con.commit()
    except Exception:
        con.rollback()


def _hash(*partes) -> str:
    return hashlib.sha1("|".join(str(p) for p in partes).encode()).hexdigest()[:16]


def registrar(acao, referencia="", detalhe=""):
    with conectar() as con:
        con.execute(
            "INSERT INTO log (quando,acao,referencia,detalhe) VALUES (?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), acao, referencia, detalhe))


def salvar_processos(processos):
    with conectar() as con:
        for p in processos:
            con.execute("""INSERT OR IGNORE INTO processos
                (numero,cliente,area,sistema,tribunal,assunto)
                VALUES (?,?,?,?,?,?)""",
                (p["numero"], p.get("cliente"), p.get("area"), p.get("sistema"),
                 p.get("tribunal"), p.get("assunto")))
    if processos:
        limpar()


def salvar_publicacao(pub) -> tuple[str, bool]:
    """Grava a publicação. Devolve (id, eh_nova). Idempotente."""
    pid = _hash(pub["processo"], pub["data_disponibilizacao"], (pub.get("teor") or "")[:200])
    con = conectar()
    existe = con.execute("SELECT 1 FROM publicacoes WHERE id=?", (pid,)).fetchone()
    if not existe:
        con.execute("""INSERT INTO publicacoes
            (id,processo,sistema,data_disponibilizacao,teor,capturada_em,fontes)
            VALUES (?,?,?,?,?,?,?)""",
            (pid, pub["processo"], pub.get("sistema"),
             str(pub["data_disponibilizacao"]), pub.get("teor"),
             datetime.now().isoformat(timespec="seconds"),
             ",".join(pub.get("fontes") or [pub.get("sistema") or "?"])))
        con.commit()
    con.close()
    if not existe:
        limpar()
    return pid, not existe


def criar_prazo(publicacao_id, processo, area, ato, prazo_dias,
                data_fatal, prazo_interno, fonte, trecho="") -> bool:
    """Cria o prazo em 'pendente_revisao'. Nada vale sem o advogado confirmar.

    IDENTIDADE = publicacao_id, e só.

    Antes o id era hash(publicacao_id, ato) e a checagem de existência usava
    esse id. Como o ATO é mutável — o recálculo o reescreve quando uma regra
    melhora —, mudar o ato mudava a identidade, a linha antiga deixava de ser
    encontrada e a captura seguinte criava uma SEGUNDA linha para a mesma
    intimação. O painel passava a mostrar o mesmo prazo duas vezes.

    Uma publicação gera um prazo. É esta a invariante, e ela agora está
    também no banco (índice único em publicacao_id, criado em _migrar), para
    não depender de nenhum caminho de código lembrar dela.
    """
    pid = _hash(publicacao_id)
    con = conectar()
    if con.execute("SELECT 1 FROM prazos WHERE publicacao_id=?",
                   (publicacao_id,)).fetchone():
        con.close(); return False
    con.execute("""INSERT INTO prazos
        (id,publicacao_id,processo,area,ato,prazo_dias,data_fatal,prazo_interno,
         status,fonte,criado_em,trecho) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (pid, publicacao_id, processo, area, ato, prazo_dias,
         str(data_fatal) if data_fatal else None,
         str(prazo_interno) if prazo_interno else None,
         "pendente_revisao", fonte, datetime.now().isoformat(timespec="seconds"),
         trecho))
    con.commit(); con.close()
    registrar("prazo_criado", pid, f"{processo} | {ato} | fatal {data_fatal}")
    limpar()
    return True


@leitura()
def listar_prazos(status=None):
    con = conectar()
    sql = """SELECT p.*, pr.cliente, pr.tribunal, pr.assunto, pu.teor, pu.sistema,
                    pu.data_disponibilizacao
             FROM prazos p
             LEFT JOIN processos pr ON pr.numero = p.processo
             LEFT JOIN publicacoes pu ON pu.id = p.publicacao_id"""
    args = ()
    if status:
        sql += " WHERE p.status IN (%s)" % ",".join("?" * len(status))
        args = tuple(status)
    sql += " ORDER BY p.data_fatal IS NULL, p.data_fatal"
    linhas = [dict(r) for r in con.execute(sql, args).fetchall()]
    con.close()
    return linhas


def confirmar(prazo_id, por, prazo_dias=None, data_fatal=None,
              prazo_interno=None, ato=None, obs=None):
    campos = {"status": "confirmado", "confirmado_por": por,
              "confirmado_em": datetime.now().isoformat(timespec="seconds")}
    if prazo_dias is not None: campos["prazo_dias"] = prazo_dias
    if data_fatal is not None: campos["data_fatal"] = str(data_fatal)
    if prazo_interno is not None: campos["prazo_interno"] = str(prazo_interno)
    if ato is not None: campos["ato"] = ato
    if obs is not None: campos["observacao"] = obs
    with conectar() as con:
        con.execute(
            f"UPDATE prazos SET {','.join(f'{k}=?' for k in campos)} WHERE id=?",
            (*campos.values(), prazo_id))
    registrar("prazo_confirmado", prazo_id, f"por {por} | fatal {data_fatal}")
    limpar()


def marcar_cumprido(prazo_id, por, obs=None):
    with conectar() as con:
        con.execute("""UPDATE prazos SET status='cumprido', cumprido_em=?,
                       observacao=COALESCE(?,observacao) WHERE id=?""",
                    (datetime.now().isoformat(timespec="seconds"), obs, prazo_id))
    registrar("prazo_cumprido", prazo_id, f"por {por}")
    limpar()


def arquivar(prazo_id, por, motivo=""):
    with conectar() as con:
        con.execute("UPDATE prazos SET status='arquivado', observacao=? WHERE id=?",
                    (motivo, prazo_id))
    registrar("prazo_arquivado", prazo_id, f"por {por} | {motivo}")
    limpar()


@leitura(ttl=30)
def ultimos_logs(n=50):
    con = conectar()
    r = [dict(x) for x in con.execute(
        "SELECT * FROM log ORDER BY id DESC LIMIT ?", (n,)).fetchall()]
    con.close(); return r


@leitura(ttl=60)
def ultima_captura():
    """Quando a captura local rodou pela última vez (datetime ou None).

    A captura roda fora do app, no PC do escritório (CAPTURA_LOCAL.md), e
    grava direto no banco — o único jeito do painel saber que ela ainda está
    viva é olhar o log que ela mesma deixa a cada execução. Sem essa
    checagem, uma tarefa agendada que parou de rodar só é percebida quando
    o advogado repara, por conta própria, que faz dias que nada muda — e
    prazo perdido por captura silenciosamente parada é o cenário que este
    sistema existe para evitar.
    """
    con = conectar()
    r = con.execute(
        "SELECT quando FROM log WHERE acao='ingestao' "
        "ORDER BY quando DESC LIMIT 1").fetchone()
    con.close()
    if not r:
        return None
    return datetime.fromisoformat(r["quando"])
