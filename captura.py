"""
Captura de publicações — roteador entre as fontes. Configurado pela tela de
Configuração do painel (ou por variáveis de ambiente, na nuvem).

FONTES — nenhuma delas usa o token A3:

  "djen"    DJEN, por número de OAB, sem autenticação nenhuma. Mais simples,
            cobre a maior parte. Ver captura_djen.py.
  "mni"     Webservice oficial do CNJ. Usa usuário/senha do advogado
            (idConsultante/senhaConsultante), alternativa que o próprio padrão
            admite no lugar do certificado. Ver mni.py.
  "ambas"   DJEN + MNI. Duplicata não é problema: o banco é idempotente por
            hash da publicação.

>>> POR QUE O TOKEN A3 NÃO ENTRA AQUI <<<
A chave privada do A3 não sai do hardware. Exige PKCS#11, token plugado e PIN
por operação — automação desacompanhada é inviável por projeto do dispositivo,
não por falta de código. O token continua servindo para o advogado assinar e
protocolar no navegador dele. A captura não precisa dele. Ver certificado.py.
"""

from datetime import date, timedelta
import configuracao


def fonte_conectada() -> bool:
    return configuracao.fonte_conectada()


# Compatibilidade com código antigo que importava a constante.
FONTE_CONECTADA = configuracao.fonte_conectada()


def capturar_publicacoes(oab: str = None, uf: str = None,
                         desde: date = None, dias: int = 7) -> list[dict]:
    """Devolve publicações no formato que pipeline.py consome:
        {"processo", "sistema", "data_disponibilizacao", "teor"}
    """
    cfg = configuracao.carregar()
    if not cfg.get("conectada"):
        raise NotImplementedError(
            "Nenhuma fonte conectada. Abra a aba Configuração no painel, "
            "preencha a OAB, teste a conexão e marque como conectada. "
            "Ou rode `python diagnostico.py` no terminal."
        )
    oab = oab or cfg.get("oab_numero")
    uf = uf or cfg.get("oab_uf")
    desde = desde or (date.today() - timedelta(days=dias))
    fonte = cfg.get("fonte", "djen")

    pubs, erros = [], []
    if fonte in ("djen", "ambas"):
        try:
            import captura_djen
            pubs += captura_djen.capturar_publicacoes(oab, uf, desde)
        except Exception as e:
            erros.append(f"DJEN: {type(e).__name__}: {e}")

    if fonte in ("mni", "ambas"):
        import mni
        for chave in ("TJGO_PROJUDI", "TJGO_PJD"):
            try:
                pubs += mni.consultar_avisos_pendentes(chave)
            except Exception as e:
                erros.append(f"MNI {chave}: {type(e).__name__}: {e}")

    # De-para: só no modo "ambas", onde a mesma intimação chega pelas duas
    # fontes com textos diferentes. Conservador de propósito — ver
    # reconciliacao.py.
    if fonte == "ambas" and pubs:
        import reconciliacao, db as _db
        r = reconciliacao.reconciliar(pubs)
        if r["unioes"] or r["suspeitas"]:
            _db.registrar("de_para",
                          f"{r['entrada']}->{r['saida']}",
                          f"{len(r['unioes'])} unidas, "
                          f"{len(r['suspeitas'])} suspeitas mantidas separadas")
        pubs = r["unificadas"]

    if erros:
        # Fonte fora do ar não pode derrubar a captura inteira, MAS não pode
        # falhar em silêncio — silêncio aqui vira prazo perdido.
        import db
        db.registrar("captura_falha_parcial", fonte, " | ".join(erros)[:500])
        if not pubs:
            raise RuntimeError("Nenhuma fonte respondeu: " + " | ".join(erros))
    return pubs


def testar(oab: str, uf: str) -> dict:
    """Teste rápido do DJEN para a tela de Configuração."""
    from datetime import timedelta
    try:
        import captura_djen
        pubs = captura_djen.capturar_publicacoes(
            oab, uf, date.today() - timedelta(days=60))
        return {"ok": True, "total": len(pubs),
                "sistemas": sorted({p.get("sistema") or "?" for p in pubs})}
    except Exception as e:
        return {"ok": False, "erro": f"{type(e).__name__}: {e}"}
