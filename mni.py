"""
MNI — Modelo Nacional de Interoperabilidade. O caminho OFICIAL para integrar
com os sistemas do Judiciário.

═══════════════════════════════════════════════════════════════════
POR QUE MNI E NÃO "LOGAR COM O TOKEN"
═══════════════════════════════════════════════════════════════════
O MNI é o padrão do CNJ (Termo de Cooperação 58/2009) para troca de dados
processuais entre sistemas. É SOAP/XML, e as três operações que o CNJ define
como mínimo são exatamente o que uma controladoria precisa:

    consultarAvisosPendentes   -> intimações pendentes do advogado
    consultarTeorComunicacao   -> o teor da intimação
    consultarProcesso          -> dados e movimentos do processo

>>> O PONTO QUE MUDA TUDO PARA O SEU CASO <<<
O MNI aceita certificado ICP-Brasil COMO MEIO PREFERENCIAL, mas admite
ALTERNATIVAMENTE usuário e senha, desde que sobre HTTPS. Os campos são
`idConsultante` e `senhaConsultante`.

Ou seja: dá para consultar SEM brigar com o token A3. E isso importa porque
automatizar A3 é inviável na prática — a chave privada não sai do hardware,
exige middleware PKCS#11, token plugado e PIN a cada operação. Não existe
automação desacompanhada com A3. Com usuário/senha, existe.

No TJGO o usuário costuma ser o CPF sem pontos nem traço.

═══════════════════════════════════════════════════════════════════
ANTES DE USAR — NÃO É OPCIONAL
═══════════════════════════════════════════════════════════════════
1. As credenciais são DO ADVOGADO. Seu software passa a agir como ele.
   Tenha autorização POR ESCRITO dizendo o que o sistema faz e o que acessa.
2. Guarde a senha em variável de ambiente, NUNCA no código nem no Git.
3. Confirme as condições de uso do acesso automatizado com o tribunal. O TJGO
   publica uma página de "Acesso Automatizado por Sistemas Externos", o que
   indica que consulta programática é prevista — mas confirme limites de
   frequência antes de agendar consultas de hora em hora.
4. Consulte com parcimônia. Robô agressivo derruba acesso — e o prejudicado
   é o advogado, não você.

═══════════════════════════════════════════════════════════════════
ESTE CÓDIGO NÃO FOI TESTADO CONTRA O TRIBUNAL
═══════════════════════════════════════════════════════════════════
Foi escrito num ambiente sem acesso à rede do TJGO. Os endpoints e nomes de
campo precisam ser confirmados no WSDL real. Rode `python diagnostico.py`
para descobrir o que responde de verdade.
"""

import os
from datetime import date, datetime

# Marcador de versão. A tela mostra este número — se não bater com o que eu
# disser, o Streamlit está rodando de outra pasta ou com módulo em cache.
VERSAO = "2026-07-20.c — cliente tolerante + plano B em XML cru"

# Endpoints MNI do TJGO. O padrão do Projudi é /IntercomunicacaoService?WSDL
# (NÃO é o /mni/servico-intercomunicacao-... que eu havia chutado antes).
# Confirme abrindo a URL no navegador: tem que vir XML, não página do portal.
ENDPOINTS = {
    "TJGO_PROJUDI": "https://projudi.tjgo.jus.br/IntercomunicacaoService?WSDL",
    "TJGO_PJD": "https://pjd.tjgo.jus.br/IntercomunicacaoService?WSDL",
    # PJe de outros tribunais costuma ser:
    # https://pje.<tribunal>.jus.br/pje/intercomunicacao?wsdl
}

def _cfg():
    import configuracao
    return configuracao.carregar()


def _credenciais():
    c = _cfg()
    return c.get("mni_usuario", ""), c.get("mni_senha", "")


def _wsdl(chave: str = None) -> str:
    """WSDL configurado tem prioridade. As URLs em ENDPOINTS são PALPITE —
    pegue a real no portal do tribunal (o Projudi/TJGO publica links
    'MNI CNJ' e 'MNI TJGO' no rodapé)."""
    c = _cfg()
    if c.get("mni_wsdl"):
        return c["mni_wsdl"]
    if chave and chave in ENDPOINTS:
        return ENDPOINTS[chave]
    raise RuntimeError(
        "URL do WSDL do MNI não configurada. Pegue no portal do TJGO "
        "(rodapé do Projudi: links 'MNI CNJ' / 'MNI TJGO') e cole no campo "
        "'WSDL do MNI' na aba Configuração."
    )


class MNIRecusado(Exception):
    """O serviço respondeu, mas recusou a requisição (sucesso=false)."""


def _checar_resposta(resp):
    """O MNI NÃO devolve erro HTTP quando recusa: responde 200 com
    sucesso=false e uma mensagem dentro do XML. Ignorar isso transforma
    'credencial inválida' em '0 avisos pendentes' — ou seja, o sistema diz
    que não há prazo quando na verdade nem autenticou. Num controle de
    prazos, esse é o pior defeito possível."""
    sucesso = getattr(resp, "sucesso", None)
    if sucesso is None:
        sucesso = getattr(resp, "success", None)
    mensagem = (getattr(resp, "mensagem", None)
                or getattr(resp, "message", None) or "")
    if sucesso is False or (isinstance(sucesso, str)
                            and sucesso.lower() in ("false", "0", "nao", "não")):
        raise MNIRecusado(str(mensagem) or
                          "serviço retornou sucesso=false, sem detalhar o motivo")
    return sucesso, str(mensagem)


def _cliente(wsdl: str, cru: bool = False):
    """Cliente SOAP tolerante.

    Serviços SOAP de tribunal costumam NÃO respeitar à risca o próprio XSD —
    mandam os elementos fora da ordem declarada no xsd:sequence. Com o zeep
    em modo estrito isso vira XMLParseError ("Unexpected element 'processo',
    expected 'mensagem'") mesmo com a resposta sendo válida na prática.

    strict=False + xsd_ignore_sequence_order=True fazem o parser aceitar a
    ordem que vier. cru=True devolve o XML sem interpretar, para o plano B.
    """
    try:
        from zeep import Client, Settings
        from zeep.transports import Transport
    except ImportError as e:
        raise RuntimeError("pip install zeep") from e
    import requests
    sessao = requests.Session()
    sessao.headers["User-Agent"] = "Tempestivo/1.0 (controladoria de prazos)"
    cfg = Settings(strict=False, xsd_ignore_sequence_order=True,
                   xml_huge_tree=True, raw_response=cru)
    return Client(wsdl, transport=Transport(session=sessao, timeout=60),
                  settings=cfg)


def consultar_avisos_pendentes(endpoint_key: str = "TJGO_PROJUDI") -> list:
    """Intimações pendentes do advogado. É a fonte mais direta de prazos:
    o tribunal entrega o que está pendente, sem precisar varrer diário."""
    usuario, senha = _credenciais()
    if not (usuario and senha):
        raise RuntimeError(
            "Usuário/senha do MNI não preenchidos na aba Configuração. "
            "No TJGO o usuário costuma ser o CPF sem pontos nem traço."
        )
    cli = _cliente(_wsdl(endpoint_key))
    resp = cli.service.consultarAvisosPendentes(
        idConsultante=usuario, senhaConsultante=senha,
    )
    sucesso, msg = _checar_resposta(resp)
    avisos = _normalizar_avisos(resp, endpoint_key)
    if sucesso is None and not avisos:
        # Não deu para confirmar que autenticou E não veio nada. Vazio sem
        # confirmação NÃO é "não há prazos" — é "não sei". Trate como falha.
        raise MNIRecusado(
            "o serviço não confirmou sucesso e não devolveu nenhum aviso — "
            "não dá para afirmar que não há prazos pendentes. "
            + (f"Mensagem do tribunal: {msg}" if msg else ""))
    return avisos


def consultar_teor_comunicacao(id_aviso: str, endpoint_key: str = "TJGO_PROJUDI"):
    """Teor da intimação — o texto que a classificação precisa ler."""
    usuario, senha = _credenciais()
    cli = _cliente(_wsdl(endpoint_key))
    return cli.service.consultarTeorComunicacao(
        idConsultante=usuario, senhaConsultante=senha,
        identificadorAviso=id_aviso,
    )


def consultar_processo(numero: str, endpoint_key: str = "TJGO_PROJUDI",
                       movimentos: bool = True, documentos: bool = False):
    usuario, senha = _credenciais()
    cli = _cliente(_wsdl(endpoint_key))
    return cli.service.consultarProcesso(
        idConsultante=usuario, senhaConsultante=senha,
        numeroProcesso=numero.replace(".", "").replace("-", ""),
        movimentos=movimentos,
        incluirDocumentos=documentos,
    )


def _normalizar_avisos(resp, sistema: str) -> list:
    """Converte a resposta do MNI para o formato que pipeline.py já consome.

    AJUSTE conforme o XML real — os nomes abaixo seguem o schema 2.2.2, mas
    cada tribunal preenche de um jeito. Rode diagnostico.py e olhe o retorno.
    """
    avisos = getattr(resp, "aviso", None) or []
    saida = []
    for a in avisos:
        proc = getattr(a, "processo", None)
        numero = (getattr(proc, "numero", None) if proc else None) or \
                 getattr(a, "numeroProcesso", "")
        d = getattr(a, "dataDisponibilizacao", None) or getattr(a, "dataEnvio", None)
        if isinstance(d, datetime):
            d = d.date()
        elif isinstance(d, str) and d:
            d = _parse_data_mni(d)
        saida.append({
            "processo": str(numero),
            "sistema": sistema,
            "data_disponibilizacao": d or date.today(),
            "teor": getattr(a, "teor", "") or getattr(a, "textoAviso", "") or "",
            "id_aviso": getattr(a, "identificadorAviso", None),
        })
    return saida


def _parse_data_mni(s: str):
    """MNI usa AAAAMMDDHHMMSS. Aceita ISO também, por segurança."""
    s = str(s).strip()
    try:
        if len(s) >= 8 and s[:8].isdigit():
            return date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        return date.fromisoformat(s[:10])
    except Exception:
        return None


def testar() -> dict:
    """Testa a conexão MNI e traduz o erro em algo acionável.
    Devolve {"ok": bool, "msg": str, "dica": str, "total": int|None}."""
    cfg = _cfg()
    usuario, senha = cfg.get("mni_usuario", ""), cfg.get("mni_senha", "")
    wsdl = cfg.get("mni_wsdl", "")

    if not wsdl:
        return {"ok": False, "msg": "URL do WSDL não informada.",
                "dica": "As URLs que deixei no código são PALPITE meu, não "
                        "endereços confirmados. Pegue a real no portal do "
                        "TJGO — o rodapé do Projudi tem links 'MNI CNJ' e "
                        "'MNI TJGO' — e cole no campo WSDL."}
    if not (usuario and senha):
        return {"ok": False, "msg": "Usuário ou senha em branco.",
                "dica": "No TJGO o usuário costuma ser o CPF sem pontuação."}
    try:
        import zeep  # noqa: F401
    except ImportError:
        return {"ok": False, "msg": "Biblioteca zeep não instalada.",
                "dica": "Rode no terminal:  pip install zeep"}

    try:
        avisos = consultar_avisos_pendentes()
    except MNIRecusado as e:
        return {"ok": False, "msg": f"O tribunal RECUSOU: {e}",
                "dica": "O serviço respondeu, mas não aceitou a requisição. "
                        "Normalmente é credencial errada ou acesso "
                        "automatizado ainda não liberado para este usuário."}
    except Exception as e:
        return _diagnosticar(e, wsdl)

    if not avisos:
        return {"ok": True, "total": 0, "vazio": True,
                "msg": "Autenticou, mas vieram 0 avisos pendentes.",
                "dica": "Zero pode ser verdade (nenhuma intimação aguardando "
                        "ciência) ou pode ser falha silenciosa. Rode a "
                        "verificação de autenticação abaixo antes de confiar."}
    return {"ok": True, "total": len(avisos),
            "msg": f"MNI respondeu: {len(avisos)} avisos pendentes.",
            "dica": ""}


def verificar_autenticacao() -> dict:
    """CANÁRIO: manda credencial deliberadamente inválida.

    Se o serviço RECUSAR, a autenticação está sendo checada e um resultado
    vazio com a credencial boa significa mesmo "não há prazos".
    Se o serviço ACEITAR lixo, nenhum resultado deste endpoint é confiável —
    inclusive os zeros.
    """
    cfg = _cfg()
    wsdl = cfg.get("mni_wsdl") or ENDPOINTS["TJGO_PROJUDI"]
    try:
        cli = _cliente(wsdl)
        resp = cli.service.consultarAvisosPendentes(
            idConsultante="00000000000",
            senhaConsultante="senha-invalida-de-proposito-000",
        )
        try:
            _checar_resposta(resp)
        except MNIRecusado as e:
            return {"confiavel": True,
                    "msg": f"O serviço recusou credencial falsa: “{e}”. "
                           "A autenticação está sendo validada."}
        avisos = _normalizar_avisos(resp, "canario")
        if avisos:
            return {"confiavel": False,
                    "msg": f"GRAVE: o serviço DEVOLVEU {len(avisos)} avisos "
                           "para uma credencial inventada. Não use esta fonte."}
        return {"confiavel": False,
                "msg": "O serviço aceitou uma credencial falsa e devolveu "
                       "vazio, sem recusar. Ou seja: um resultado vazio aqui "
                       "NÃO prova que não há prazos. Não confie nesta fonte "
                       "até entender o comportamento."}
    except MNIRecusado as e:
        return {"confiavel": True,
                "msg": f"O serviço recusou credencial falsa: “{e}”. "
                       "A autenticação está sendo validada."}
    except Exception as e:
        return {"confiavel": None,
                "msg": f"Não deu para verificar: {type(e).__name__}: {str(e)[:150]}"}


def _diagnosticar(e: Exception, wsdl: str) -> dict:
    nome, txt = type(e).__name__, str(e).lower()

    if "xmlsyntax" in nome.lower() or "not well-formed" in txt or "<!doctype" in txt:
        return {"ok": False, "msg": "A URL não devolveu um WSDL (veio HTML).",
                "dica": "Quase sempre significa endereço errado: o servidor "
                        "respondeu com uma página (404 ou tela de login) em vez "
                        "do XML do serviço. Confirme a URL no portal do tribunal."}
    if "404" in txt or "not found" in txt:
        return {"ok": False, "msg": "404 — endereço do WSDL não existe.",
                "dica": f"A URL testada foi:\n{wsdl}\nEla é um palpite meu. "
                        "Peça a correta à Diretoria de Informática do TJGO."}
    if "401" in txt or "403" in txt or "unauthorized" in txt or "denied" in txt:
        return {"ok": False, "msg": "Acesso negado pelo tribunal.",
                "dica": "O endereço existe, mas a credencial foi recusada OU o "
                        "acesso automatizado precisa ser liberado previamente. "
                        "Vários tribunais exigem cadastro do sistema externo "
                        "antes de aceitar chamadas — é o caso de perguntar."}
    if "senha" in txt or "usuário" in txt or "usuario" in txt or "invalid" in txt:
        return {"ok": False, "msg": "Credenciais recusadas.",
                "dica": "Confirme com o advogado o usuário (CPF sem pontuação) "
                        "e a senha DO SISTEMA DO TRIBUNAL — que pode ser "
                        "diferente da senha do portal da OAB."}
    if any(k in txt for k in ("timed out", "timeout", "connection", "resolve",
                              "unreachable", "ssl")):
        return {"ok": False, "msg": "Não consegui alcançar o servidor.",
                "dica": "Rede, firewall ou o endereço não existe. Teste abrir a "
                        "URL do WSDL no navegador: se não abrir lá, não é o "
                        "sistema — é o endereço."}
    return {"ok": False, "msg": f"{nome}: {str(e)[:200]}",
            "dica": "Erro não mapeado. Se o WSDL abre no navegador mas falha "
                    "aqui, provavelmente é o formato dos parâmetros — me mande "
                    "esta mensagem que eu ajusto."}


def inspecionar(wsdl: str = None) -> dict:
    """Lê o WSDL e devolve as operações e suas assinaturas REAIS.

    Não precisa de credencial — é só leitura do contrato do serviço. Use isto
    antes de tentar autenticar: em vez de adivinhar os nomes dos parâmetros,
    o próprio tribunal informa quais são.
    """
    wsdl = wsdl or _cfg().get("mni_wsdl") or ENDPOINTS["TJGO_PROJUDI"]
    try:
        from zeep import Client
    except ImportError:
        return {"ok": False, "msg": "Biblioteca zeep não instalada.",
                "dica": "Rode no terminal:  pip install zeep"}
    try:
        cli = Client(wsdl)
    except Exception as e:
        return _diagnosticar(e, wsdl)

    ops = {}
    for servico in cli.wsdl.services.values():
        for porta in servico.ports.values():
            for nome, op in porta.binding._operations.items():
                try:
                    ops[nome] = op.input.signature()
                except Exception:
                    ops[nome] = "(assinatura não legível)"
    return {"ok": True, "wsdl": wsdl, "operacoes": ops,
            "msg": f"{len(ops)} operações publicadas pelo serviço."}


def _cavar(obj, *caminho):
    """Desce por atributos/listas sem explodir se algum nível não existir."""
    for passo in caminho:
        if obj is None:
            return None
        if isinstance(passo, int):
            try:
                obj = list(obj)[passo]
            except Exception:
                return None
        else:
            obj = getattr(obj, passo, None)
    return obj


def _resumo_por_xml_cru(numero: str, endpoint_key: str) -> dict:
    """Plano B: pede a resposta sem interpretar e lê o XML na mão.

    Imune a qualquer divergência entre o XSD publicado e o que o servidor
    realmente devolve. Mais feio, muito mais resistente.
    """
    import re as _re
    import xml.etree.ElementTree as ET

    usuario, senha = _credenciais()
    cli = _cliente(_wsdl(endpoint_key), cru=True)
    resp = cli.service.consultarProcesso(
        idConsultante=usuario, senhaConsultante=senha,
        numeroProcesso=numero.replace(".", "").replace("-", ""),
        movimentos=False, incluirDocumentos=False)
    xml = resp.content if hasattr(resp, "content") else bytes(str(resp), "utf-8")
    raiz = ET.fromstring(xml)

    def sem_ns(tag):
        return tag.split("}")[-1]

    def achar_todos(nome):
        return [e for e in raiz.iter() if sem_ns(e.tag) == nome]

    def primeiro_texto(nome):
        for e in achar_todos(nome):
            if e.text and e.text.strip():
                return e.text.strip()
        for e in achar_todos(nome):           # às vezes vem como atributo
            for v in e.attrib.values():
                if v and v.strip():
                    return v.strip()
        return ""

    partes = []
    for pessoa in achar_todos("pessoa"):
        nome = pessoa.get("nome") or primeiro_texto_em(pessoa, "nome")
        if nome:
            partes.append({"polo": "", "nome": nome})

    orgao = ""
    for e in achar_todos("orgaoJulgador"):
        orgao = e.get("nomeOrgao") or (e.text or "").strip()
        if orgao:
            break

    return {
        "numero": numero,
        "classe": primeiro_texto("classeProcessual") or _atributo(raiz, "classeProcessual"),
        "orgao": orgao,
        "assunto": primeiro_texto("assunto"),
        "partes": partes,
        "provavel_cliente": partes[0]["nome"] if partes else "",
        "modo": "xml cru (plano B)",
    }


def primeiro_texto_em(elem, nome):
    for e in elem.iter():
        if e.tag.split("}")[-1] == nome and e.text and e.text.strip():
            return e.text.strip()
    return ""


def _atributo(raiz, nome):
    for e in raiz.iter():
        v = e.get(nome)
        if v:
            return v
    return ""


def resumo_processo(numero: str, endpoint_key: str = "TJGO_PROJUDI") -> dict:
    """Extrai do MNI o que falta na carteira: partes, classe, assunto, órgão.

    O DJEN entrega a publicação mas não diz de quem é o processo. É esta
    consulta que preenche o nome do cliente no painel.

    NÃO TESTADO contra o retorno real — o schema do MNI é aninhado e cada
    tribunal preenche de um jeito. Extração defensiva: campo ausente vira
    vazio, nunca exceção. Confira com UM processo antes de rodar em lote.
    """
    erros = []

    # Tentativa 1 — zeep em modo tolerante (aceita ordem fora do schema)
    try:
        resp = consultar_processo(numero, endpoint_key, movimentos=False)
        _checar_resposta(resp)
    except MNIRecusado:
        raise                       # recusa do tribunal não é problema técnico
    except Exception as e:
        erros.append(f"[1] zeep tolerante -> {type(e).__name__}: {str(e)[:160]}")
        resp = None

    # Tentativa 2 — XML cru, imune a divergência de schema
    if resp is None:
        try:
            return _resumo_por_xml_cru(numero, endpoint_key)
        except MNIRecusado:
            raise
        except Exception as e:
            erros.append(f"[2] XML cru -> {type(e).__name__}: {str(e)[:160]}")
            raise RuntimeError(
                f"As duas estratégias falharam (mni.py {VERSAO}):\n"
                + "\n".join(erros))

    proc = getattr(resp, "processo", None) or resp
    basicos = getattr(proc, "dadosBasicos", None) or proc

    partes = []
    for polo in (getattr(basicos, "polo", None) or []):
        tipo = str(getattr(polo, "polo", "") or "")
        for parte in (getattr(polo, "parte", None) or []):
            nome = (_cavar(parte, "pessoa", "nome")
                    or getattr(parte, "nome", None) or "")
            if nome:
                partes.append({"polo": tipo, "nome": str(nome)})

    def _txt(*nomes):
        for n in nomes:
            v = getattr(basicos, n, None)
            if v not in (None, ""):
                return str(getattr(v, "_value_1", v))
        return ""

    return {
        "numero": numero,
        "classe": _txt("classeProcessual", "classe"),
        "orgao": str(_cavar(basicos, "orgaoJulgador", "nomeOrgao")
                     or _txt("orgaoJulgador")),
        "assunto": str(_cavar(basicos, "assunto", 0, "codigoNacional")
                       or _txt("assunto")),
        "partes": partes,
        # Heurística: o cliente costuma ser a parte do polo em que o
        # advogado atua. Confirme com ele antes de confiar.
        "provavel_cliente": partes[0]["nome"] if partes else "",
    }
