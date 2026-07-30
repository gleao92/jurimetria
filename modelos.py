"""
Modelos tipados que trafegam entre as camadas.

POR QUE ISTO EXISTE
Publicação e classificação circulavam como dicionário solto. Dicionário não
valida nada: um campo com nome errado vira `None` silencioso, e num sistema de
prazo campo vazio não dá erro — dá data errada. Este projeto já teve esse
problema com os nomes de campo do DJEN, que variam entre tribunais.

COMPATIBILIDADE
As classes aceitam acesso por chave (`p["processo"]`) e `.get()`, então o
código existente continua funcionando sem alteração. A vantagem é o ponto de
CONSTRUÇÃO: só se cria um objeto com os campos certos, com tipo certo, e a
normalização de data acontece num lugar só.
"""

from dataclasses import dataclass, field, asdict, fields
from datetime import date, datetime
from typing import Any, Optional


class _ComoDicionario:
    """Leitura por chave, para conviver com o código que espera dicionário."""

    def __getitem__(self, chave: str) -> Any:
        try:
            return getattr(self, chave)
        except AttributeError as e:
            raise KeyError(chave) from e

    def __setitem__(self, chave: str, valor: Any) -> None:
        if chave not in {f.name for f in fields(self)}:
            raise KeyError(f"campo desconhecido: {chave}")
        setattr(self, chave, valor)

    def __contains__(self, chave: str) -> bool:
        return chave in {f.name for f in fields(self)}

    def get(self, chave: str, padrao: Any = None) -> Any:
        return getattr(self, chave, padrao)

    def keys(self):
        return [f.name for f in fields(self)]

    def to_dict(self) -> dict:
        return asdict(self)


def para_data(v) -> Optional[date]:
    """Aceita date, datetime, ISO ou AAAAMMDD. Devolve None se não der."""
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    try:
        if len(s) >= 8 and s[:8].isdigit() and "-" not in s[:8]:
            return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


@dataclass
class Publicacao(_ComoDicionario):
    """Uma publicação capturada, já normalizada."""

    processo: str = ""
    sistema: str = ""
    data_disponibilizacao: Optional[date] = None
    teor: str = ""
    tipo: str = ""            # tipoComunicacao do DJEN, quando vem
    orgao: str = ""           # nome da vara — usado para deduzir a área
    tipo_data: str = ""       # "publicacao" quando a fonte já entrega a publicação
    id_aviso: str = ""        # identificador do MNI, quando aplicável
    fontes: list = field(default_factory=list)

    def __post_init__(self):
        self.processo = str(self.processo or "")
        self.sistema = str(self.sistema or "")
        self.teor = str(self.teor or "")
        self.tipo = str(self.tipo or "")
        self.orgao = str(self.orgao or "")
        self.data_disponibilizacao = para_data(self.data_disponibilizacao)
        if not self.fontes and self.sistema:
            self.fontes = [self.sistema]

    @property
    def completa(self) -> bool:
        """Falta de processo, teor ou data impede calcular prazo confiável."""
        return bool(self.processo and self.teor and self.data_disponibilizacao)

    def faltando(self) -> list[str]:
        ausentes = []
        if not self.processo:
            ausentes.append("processo")
        if not self.teor:
            ausentes.append("teor")
        if not self.data_disponibilizacao:
            ausentes.append("data_disponibilizacao")
        return ausentes


@dataclass
class Classificacao(_ComoDicionario):
    """Resultado da leitura de uma publicação: qual ato e quantos dias."""

    ato: str = ""
    prazo_dias: Optional[int] = None
    fonte: str = ""                  # "declarado" | "presumido" | ""
    contagem_declarada: str = ""     # "uteis" | "corridos" | ""
    conflito: Optional[str] = None
    revisar: bool = True
    trecho: str = ""

    @property
    def confiavel(self) -> bool:
        """Só o prazo escrito na publicação dispensa desconfiança."""
        return self.fonte == "declarado" and not self.conflito
