"""
Configuração da captura — lida/gravada pela tela de Configuração do painel.

PRECEDÊNCIA: variável de ambiente > banco/arquivo > padrão.

>>> POR QUE ISTO DEIXOU DE SER SÓ UM ARQUIVO <<<
Em nuvem, o container é recriado a cada deploy e o disco vai junto. O
configuracao.json sumia em silêncio e o painel voltava ao padrão — com
"conectada" em False, o que fazia o sistema exibir dados de exemplo mesmo
com o banco cheio de prazos reais. O advogado religava; o deploy seguinte
desligava de novo.

Agora: se há DATABASE_URL, a configuração vive no Postgres, ao lado dos
dados que ela governa. Sem DATABASE_URL (instalação local), continua no
arquivo, como antes.

Na primeira leitura em nuvem, o que existir no arquivo é importado para o
banco — quem já tinha configurado não perde nada.

>>> SOBRE A SENHA DO MNI <<<
Gravada pela tela, fica em TEXTO — no arquivo (local) ou na tabela (nuvem).
Aceitável na máquina do advogado, onde quem tem acesso já tem o sistema
inteiro. Em servidor, prefira variável de ambiente: além de não gravar,
o ambiente tem precedência e a tela nem oferece o campo para edição.
"""

import json
import os
import time
from pathlib import Path

_DIR = Path(os.environ.get("DB_DIR") or Path(__file__).parent)
ARQUIVO = _DIR / "configuracao.json"

PADRAO = {
    "oab_numero": "61423",
    "oab_uf": "GO",
    "fonte": "djen",          # "djen" | "mni" | "ambas"
    "mni_usuario": "",        # no TJGO: CPF do advogado sem pontuação
    "mni_senha": "",
    "mni_wsdl": "",           # URL do WSDL — pegue no portal do tribunal
    "conectada": True,        # Captura local no PC do escritório ativa por padrão
    # Contagem usada quando NÃO se consegue identificar a área.
    #   "conservadora" -> dias corridos (data mais cedo; protege, mas aperta)
    #   "civel"        -> dias úteis  (carteira predominantemente cível)
    #   "criminal"     -> dias corridos
    "area_padrao": "conservadora",
}

_ENV = {
    "oab_numero": "OAB_NUMERO",
    "oab_uf": "OAB_UF",
    "fonte": "CAPTURA_FONTE",
    "mni_usuario": "MNI_USUARIO",
    "mni_senha": "MNI_SENHA",
    "mni_wsdl": "MNI_WSDL",
    "area_padrao": "AREA_PADRAO",
}

# Cache curto: a tela do Streamlit reexecuta o script inteiro a cada clique,
# e sem isto cada rerun abriria conexão só para reler as mesmas 8 chaves.
# TTL baixo para que alteração feita noutra aba apareça sem precisar recarregar.
_TTL = 5
_cache = {"valor": None, "em": 0.0}


def _usa_banco() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip().startswith(
        ("postgres://", "postgresql://")))


def _garantir_tabela(con) -> None:
    con.execute("""CREATE TABLE IF NOT EXISTS configuracao (
        chave TEXT PRIMARY KEY, valor TEXT)""")
    con.commit()


def _ler_arquivo() -> dict:
    if not ARQUIVO.exists():
        return {}
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except Exception:
        return {}                 # arquivo corrompido não derruba o painel


def _ler_banco() -> dict:
    import db
    con = db.conectar()
    try:
        _garantir_tabela(con)
        linhas = con.execute("SELECT chave, valor FROM configuracao").fetchall()
        guardado = {r["chave"]: r["valor"] for r in linhas}

        # Primeira vez em nuvem: importa o que houver no arquivo, para quem
        # já tinha configurado não recomeçar do zero.
        if not guardado:
            do_arquivo = _ler_arquivo()
            if do_arquivo:
                _gravar_banco(con, do_arquivo)
                guardado = {k: json.dumps(v) for k, v in do_arquivo.items()
                            if k in PADRAO}
    finally:
        con.close()

    saida = {}
    for chave, bruto in guardado.items():
        try:
            saida[chave] = json.loads(bruto)
        except Exception:
            saida[chave] = bruto  # valor gravado antes como texto cru
    return saida


def _gravar_banco(con, cfg: dict) -> None:
    _garantir_tabela(con)
    for chave, valor in cfg.items():
        if chave not in PADRAO:
            continue
        bruto = json.dumps(valor, ensure_ascii=False)
        atualizou = con.execute("UPDATE configuracao SET valor=? WHERE chave=?",
                                (bruto, chave)).rowcount
        if not atualizou:
            con.execute("INSERT INTO configuracao (chave, valor) VALUES (?,?)",
                        (chave, bruto))
    con.commit()


def carregar() -> dict:
    agora = time.time()
    if _cache["valor"] is not None and agora - _cache["em"] < _TTL:
        return dict(_cache["valor"])

    cfg = dict(PADRAO)

    if _usa_banco():
        try:
            cfg.update(_ler_banco())
        except Exception:
            # Banco fora do ar não pode derrubar a tela: cai no arquivo.
            cfg.update(_ler_arquivo())
    else:
        cfg.update(_ler_arquivo())

    for chave, env in _ENV.items():   # ambiente tem precedência
        if os.environ.get(env):
            cfg[chave] = os.environ[env]
    cfg["conectada"] = True  # Captura local no PC do escritório sempre considerada ativa

    _cache["valor"] = dict(cfg)
    _cache["em"] = agora
    return cfg


def salvar(cfg: dict) -> None:
    novo = {k: v for k, v in cfg.items() if k in PADRAO}

    if _usa_banco():
        import db
        con = db.conectar()
        try:
            _gravar_banco(con, novo)
        finally:
            con.close()
    else:
        atual = dict(PADRAO)
        atual.update(_ler_arquivo())
        atual.update(novo)
        _DIR.mkdir(parents=True, exist_ok=True)
        ARQUIVO.write_text(json.dumps(atual, indent=2, ensure_ascii=False),
                           encoding="utf-8")
        try:
            os.chmod(ARQUIVO, 0o600)      # sem efeito prático no Windows
        except Exception:
            pass

    _cache["valor"] = None            # força releitura na próxima chamada


def fonte_conectada() -> bool:
    return True


def vindo_do_ambiente(chave: str) -> bool:
    """True se o valor veio de variável de ambiente (a tela não deve editar)."""
    return bool(os.environ.get(_ENV.get(chave, "")))
