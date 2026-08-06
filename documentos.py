"""
Documentos — contratos, procurações, petições e outros arquivos do processo.

ONDE O ARQUIVO FICA
Sem disco persistente garantido (ver db.py: Railway apaga o disco a cada
deploy), o único lugar seguro para o conteúdo é o mesmo banco onde já vive
tudo o mais — Postgres na nuvem, SQLite local. Grava-se em base64 numa coluna
de texto: funciona igual nos dois bancos, sem depender de tipo BLOB/bytea
específico. O custo é ~33% a mais de espaço por arquivo — aceitável para
contrato/procuração/petição (raramente grandes); por isso o limite de
tamanho abaixo.

LIMITE DE TAMANHO
20 MB por arquivo. Não é capricho: o banco existe para os DADOS do escritório
(prazos, financeiro, tarefas), não para virar repositório de vídeo de
audiência. Se precisar de arquivo maior, guarde fora e cole o link.
"""

import base64
import hashlib
from datetime import datetime

import db

LIMITE_BYTES = 20 * 1024 * 1024  # 20 MB

CATEGORIAS = {"contrato": "Contrato", "procuracao": "Procuração",
              "peticao": "Petição", "documento": "Documento do processo",
              "outro": "Outro"}


def init():
    with db.conectar() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS documentos (
            id TEXT PRIMARY KEY, nome_arquivo TEXT, categoria TEXT,
            cliente TEXT, processo TEXT, tamanho INTEGER, conteudo_b64 TEXT,
            enviado_por TEXT, enviado_em TEXT)""")


def _novo_id(*partes) -> str:
    base = "|".join(str(p) for p in partes) + datetime.now().isoformat()
    return "d" + hashlib.sha1(base.encode()).hexdigest()[:14]


def salvar(nome_arquivo: str, conteudo: bytes, categoria: str = "outro",
          cliente: str = "", processo: str = "", autor: str = "") -> str:
    if len(conteudo) > LIMITE_BYTES:
        raise ValueError(
            f"Arquivo tem {len(conteudo) / 1024 / 1024:.1f} MB — "
            f"o limite é {LIMITE_BYTES // 1024 // 1024} MB.")
    did = _novo_id(nome_arquivo, cliente, processo)
    with db.conectar() as con:
        con.execute("""INSERT INTO documentos
            (id,nome_arquivo,categoria,cliente,processo,tamanho,conteudo_b64,
             enviado_por,enviado_em) VALUES (?,?,?,?,?,?,?,?,?)""",
            (did, nome_arquivo.strip(),
             categoria if categoria in CATEGORIAS else "outro",
             cliente.strip(), processo.strip(), len(conteudo),
             base64.b64encode(conteudo).decode("ascii"), autor,
             datetime.now().isoformat(timespec="seconds")))
    db.registrar("documento_enviado", did,
                 f"{nome_arquivo} · {cliente or processo or '—'} · "
                 f"{len(conteudo)/1024:.0f} KB")
    return did


def excluir(did: str, autor: str) -> None:
    with db.conectar() as con:
        con.execute("DELETE FROM documentos WHERE id=?", (did,))
    db.registrar("documento_excluido", did, f"por {autor}")


def listar(cliente: str = None, processo: str = None) -> list[dict]:
    """Lista SEM o conteúdo — só metadados, para não carregar todos os
    arquivos na memória só para montar uma tabela."""
    con = db.conectar()
    sql = """SELECT id,nome_arquivo,categoria,cliente,processo,tamanho,
                    enviado_por,enviado_em FROM documentos"""
    cond, args = [], []
    if cliente:
        cond.append("cliente = ?"); args.append(cliente)
    if processo:
        cond.append("processo = ?"); args.append(processo)
    if cond:
        sql += " WHERE " + " AND ".join(cond)
    sql += " ORDER BY enviado_em DESC"
    r = [dict(x) for x in con.execute(sql, tuple(args)).fetchall()]
    con.close()
    return r


def obter_conteudo(did: str) -> bytes | None:
    con = db.conectar()
    r = con.execute("SELECT conteudo_b64 FROM documentos WHERE id=?", (did,)).fetchone()
    con.close()
    if not r:
        return None
    valor = r["conteudo_b64"] if hasattr(r, "keys") else r[0]
    return base64.b64decode(valor)
