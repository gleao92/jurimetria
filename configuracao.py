"""
Configuração da captura — lida/gravada pela tela de Configuração do painel.

PRECEDÊNCIA: variável de ambiente > arquivo configuracao.json > padrão.
Assim o mesmo código serve para instalação local (arquivo, editável pela tela)
e para nuvem (variáveis de ambiente / secrets, sem arquivo nenhum).

>>> SOBRE A SENHA <<<
Se gravada pela tela, fica em configuracao.json EM TEXTO, neste computador.
É proporcional para instalação local na máquina do advogado — quem tem acesso
à máquina já tem acesso ao sistema inteiro. NÃO é aceitável em servidor
compartilhado: lá, use variáveis de ambiente e não grave o arquivo.
O .gitignore já bloqueia configuracao.json.
"""

import json
import os
from pathlib import Path

_DIR = Path(os.environ.get("DB_DIR") or Path(__file__).parent)
ARQUIVO = _DIR / "configuracao.json"

PADRAO = {
    "oab_numero": "",
    "oab_uf": "GO",
    "fonte": "djen",          # "djen" | "mni" | "ambas"
    "mni_usuario": "",        # no TJGO: CPF do advogado sem pontuação
    "mni_senha": "",
    "mni_wsdl": "",           # URL do WSDL — pegue no portal do tribunal
    "conectada": False,       # vire True só depois do teste passar
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


def carregar() -> dict:
    cfg = dict(PADRAO)
    if ARQUIVO.exists():
        try:
            cfg.update(json.loads(ARQUIVO.read_text(encoding="utf-8")))
        except Exception:
            pass                      # arquivo corrompido não derruba o painel
    for chave, env in _ENV.items():   # ambiente tem precedência
        if os.environ.get(env):
            cfg[chave] = os.environ[env]
    if os.environ.get("CAPTURA_CONECTADA", "").lower() in ("1", "true", "sim"):
        cfg["conectada"] = True
    return cfg


def salvar(cfg: dict) -> None:
    atual = dict(PADRAO)
    if ARQUIVO.exists():
        try:
            atual.update(json.loads(ARQUIVO.read_text(encoding="utf-8")))
        except Exception:
            pass
    atual.update({k: v for k, v in cfg.items() if k in PADRAO})
    _DIR.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(json.dumps(atual, indent=2, ensure_ascii=False),
                       encoding="utf-8")
    try:
        os.chmod(ARQUIVO, 0o600)      # sem efeito prático no Windows
    except Exception:
        pass


def fonte_conectada() -> bool:
    return bool(carregar().get("conectada"))


def vindo_do_ambiente(chave: str) -> bool:
    """True se o valor veio de variável de ambiente (a tela não deve editar)."""
    return bool(os.environ.get(_ENV.get(chave, "")))
