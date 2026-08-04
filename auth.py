"""
Autenticação — usuários, senhas e papéis.

Senhas nunca são guardadas em texto: PBKDF2-HMAC-SHA256 com salt por usuário
e 200.000 iterações. Comparação em tempo constante.

PAPÉIS (não é firula — é o desenho jurídico do sistema):
  advogado -> único que pode CONFIRMAR a classificação de um prazo. A
              responsabilidade pela peça é dele (art. 34 do EOAB), então a
              confirmação tem que carregar o nome dele.
  apoio    -> secretária/estagiário: vê tudo, roda captura, marca cumprido,
              mas não confirma. O log registra quem fez o quê.

LIMITE IMPORTANTE: isto protege o acesso ao painel, não transforma o Streamlit
num sistema exposto à internet com segurança de banco. Rode em máquina local,
na rede do escritório, ou atrás de HTTPS com proxy reverso. E lembre que o
banco guarda dados cobertos por sigilo profissional (LGPD + EOAB): disco
criptografado e backup protegido não são opcionais.
"""

import hashlib
import secrets
from datetime import datetime

import db

# PBKDF2 continua aqui só para VERIFICAR senhas antigas. Nada novo é criado
# com ele. Hash novo usa Argon2id, que é resistente a ataque com GPU/ASIC —
# recomendação atual da OWASP. A migração é transparente: no primeiro login
# bem-sucedido, a senha antiga é reconvertida para Argon2id.
ITERACOES = 200_000

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
    _ph = PasswordHasher()          # parâmetros padrão da biblioteca
    ARGON2 = True
except ImportError:                  # sem a biblioteca, segue com PBKDF2
    _ph = None
    ARGON2 = False


def init():
    con = db.conectar()
    con.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, nome TEXT, papel TEXT,
        salt TEXT, senha_hash TEXT, ativo INTEGER DEFAULT 1,
        criado_em TEXT, ultimo_acesso TEXT)""")
    con.commit(); con.close()


def _derivar(senha: str, salt_hex: str) -> str:
    """PBKDF2 — apenas para verificar hashes legados."""
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"),
                               bytes.fromhex(salt_hex), ITERACOES).hex()


def _gerar_hash(senha: str) -> tuple[str, str]:
    """Devolve (salt, hash) para armazenar. Argon2id quando disponível."""
    if ARGON2:
        return "", _ph.hash(senha)   # o salt já vem embutido no hash
    salt = secrets.token_hex(16)
    return salt, _derivar(senha, salt)


def _conferir(senha: str, salt: str, guardado: str) -> tuple[bool, bool]:
    """Devolve (senha_correta, precisa_reconverter)."""
    if guardado.startswith("$argon2"):
        if not ARGON2:
            return False, False      # hash Argon2 sem a biblioteca instalada
        try:
            _ph.verify(guardado, senha)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False, False
        return True, _ph.check_needs_rehash(guardado)
    # legado PBKDF2
    ok = secrets.compare_digest(_derivar(senha or "", salt), guardado)
    return ok, ok and ARGON2         # correta e há Argon2 -> reconverter


def existe_algum_usuario() -> bool:
    con = db.conectar()
    r = con.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"]
    con.close()
    return r > 0


def criar_usuario(usuario: str, nome: str, senha: str, papel: str = "advogado") -> tuple[bool, str]:
    usuario = (usuario or "").strip().lower()
    if len(usuario) < 3:
        return False, "Usuário precisa de ao menos 3 caracteres."
    if len(senha or "") < 8:
        return False, "Senha precisa de ao menos 8 caracteres."
    salt, hash_novo = _gerar_hash(senha)
    con = db.conectar()
    try:
        con.execute("""INSERT INTO usuarios
            (usuario,nome,papel,salt,senha_hash,ativo,criado_em)
            VALUES (?,?,?,?,?,1,?)""",
            (usuario, nome.strip(), papel, salt, hash_novo,
             datetime.now().isoformat(timespec="seconds")))
        con.commit()
    except Exception:
        con.rollback()          # Postgres aborta a transação no erro
        con.close()
        return False, "Esse usuário já existe."
    con.close()
    db.registrar("usuario_criado", usuario, f"{nome} ({papel})")
    return True, "Usuário criado."


def verificar(usuario: str, senha: str):
    """Devolve dict do usuário se as credenciais baterem, senão None."""
    con = db.conectar()
    r = con.execute("SELECT * FROM usuarios WHERE usuario=? AND ativo=1",
                    ((usuario or "").strip().lower(),)).fetchone()
    if not r:
        con.close()
        # Gasta o mesmo tempo mesmo sem o usuário existir, para o tempo de
        # resposta não revelar quais logins existem.
        _gerar_hash(senha or "x")
        return None
    ok, reconverter = _conferir(senha or "", r["salt"] or "", r["senha_hash"])
    if ok:
        con.execute("UPDATE usuarios SET ultimo_acesso=? WHERE usuario=?",
                    (datetime.now().isoformat(timespec="seconds"), r["usuario"]))
        if reconverter:
            novo_salt, novo_hash = _gerar_hash(senha)
            con.execute("UPDATE usuarios SET salt=?, senha_hash=? WHERE usuario=?",
                        (novo_salt, novo_hash, r["usuario"]))
        con.commit()
    con.close()
    # Só depois de FECHAR: registrar() abre outra conexão e, com a de escrita
    # ainda aberta, o SQLite trava o banco ("database is locked").
    if ok and reconverter:
        db.registrar("senha_reconvertida", r["usuario"], "PBKDF2 -> Argon2id")
    if not ok:
        db.registrar("login_falhou", usuario or "", "")
        return None
    db.registrar("login", r["usuario"], r["nome"])
    return {"usuario": r["usuario"], "nome": r["nome"], "papel": r["papel"]}


def trocar_senha(usuario: str, senha_atual: str, senha_nova: str) -> tuple[bool, str]:
    if not verificar(usuario, senha_atual):
        return False, "Senha atual incorreta."
    if len(senha_nova or "") < 8:
        return False, "A nova senha precisa de ao menos 8 caracteres."
    salt, novo = _gerar_hash(senha_nova)
    with db.conectar() as con:
        con.execute("UPDATE usuarios SET salt=?, senha_hash=? WHERE usuario=?",
                    (salt, novo, usuario))
    db.registrar("senha_alterada", usuario, "")
    return True, "Senha alterada."


def listar_usuarios():
    con = db.conectar()
    r = [dict(x) for x in con.execute(
        "SELECT usuario,nome,papel,ativo,criado_em,ultimo_acesso FROM usuarios")]
    con.close(); return r


def pode_confirmar(user: dict) -> bool:
    """Só o advogado confirma classificação de prazo."""
    return bool(user) and user.get("papel") == "advogado"
