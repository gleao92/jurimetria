"""
Pipeline de ingestão: publicação -> classificação -> prazo -> banco.

É esta função que o n8n (ou um cron) chama de manhã. Idempotente: rodar duas
vezes no mesmo dia não duplica prazo nem alerta repetido.
"""

from datetime import date
import db
from prazos import calcular_prazo
from classificacao import classificar

# Fontes cuja data já vem como PUBLICAÇÃO (não disponibilização).
# O DJEN entrega a data em que a comunicação se considera publicada — que é o
# primeiro dia útil após a disponibilização (art. 224 §2º do CPC). Alimentar
# essa data no cálculo como se fosse disponibilização faz o motor avançar mais
# um dia útil e a data fatal sai um dia depois do PJe. Confirmado contra o PJe:
# Diário 03/07 (sexta), publicação/ciência 06/07 (segunda), fatal correto 27/07.
FONTES_DATA_PUBLICACAO = {"PJe", "DJEN", "comunica", "eproc", "eSAJ", "PROJUDI"}

# Rótulo para publicação cujo TEOR não veio no diário.
# Não é falha de leitura: o DJEN entrega um texto-carimbo no lugar do conteúdo
# (segredo de justiça, ou anexo não público). O prazo está correndo e não há
# como saber do quê — só abrindo o processo no tribunal. Misturar isso com
# "A IDENTIFICAR" esconde do advogado a única situação em que ele PRECISA
# entrar no sistema do tribunal.
ATO_TEOR_INDISPONIVEL = "TEOR INDISPONÍVEL — ABRIR NO TRIBUNAL"

_CARIMBOS_SEM_TEOR = (
    "ARQUIVOS DIGITAIS INDISPONÍVEIS",
    "NÃO FORAM PUBLICADOS",
    "NAO FORAM PUBLICADOS",
)


def _sem_teor(pub) -> bool:
    texto = (pub.get("teor") or "").strip().upper()
    if not texto:
        return True
    return any(c in texto for c in _CARIMBOS_SEM_TEOR)


def _tipo_data(pub) -> str:
    """"publicacao" se a fonte já entrega a data de publicação; senão
    "disponibilizacao" (comportamento padrão do motor).

    Primeiro respeita o que a própria captura marcou (campo tipo_data) — o
    DJEN, por exemplo, sempre entrega data de publicação. Só se a publicação
    não disser nada é que se tenta deduzir pelo sistema/tribunal.
    """
    marcado = str(pub.get("tipo_data") or "").strip()
    if marcado in ("publicacao", "disponibilizacao"):
        return marcado
    sistema = str(pub.get("sistema") or "").strip()
    for f in FONTES_DATA_PUBLICACAO:
        if f.lower() in sistema.lower():
            return "publicacao"
    return "disponibilizacao"


def processar_publicacoes(publicacoes, processos=None) -> dict:
    """Ingere publicações e devolve um resumo do que entrou."""
    db.init()
    if processos:
        db.salvar_processos(processos)

    por_numero = {}
    con = db.conectar()
    for r in con.execute("SELECT * FROM processos"):
        por_numero[r["numero"]] = dict(r)
    con.close()

    novas = prazos_criados = sem_ato = sem_area = sem_teor = 0
    import carteira as _cart
    for pub in publicacoes:
        pub["processo"] = _cart.formatar_numero(pub.get("processo", ""))
        pub_id, eh_nova = db.salvar_publicacao(pub)
        if eh_nova:
            novas += 1
        proc = por_numero.get(pub["processo"], {})
        area = proc.get("area") or ""
        if area in ("", "a_confirmar"):
            # Assunto primeiro (auxílio-doença é cível em qualquer vara),
            # nome do órgão depois. Vara cumulativa — "Juizado Especial Cível
            # e Criminal" — só se resolve pelo assunto.
            import carteira
            area = carteira.deduzir_area(pub.get("orgao", ""),
                                         pub.get("teor", "")) or ""
        area_desconhecida = not area
        if area_desconhecida:
            # Processo fora da carteira: NÃO assuma cível.
            # Cível conta em dias ÚTEIS, criminal em CORRIDOS — o cível dá uma
            # data MAIS TARDE. Se o processo for criminal e for tratado como
            # cível, o prazo sai depois do real e PERDE-SE o prazo.
            # Na dúvida, use a contagem que dá a data mais CEDO (segura) e
            # marque para o advogado confirmar a área.
            area = ""     # marcado; o cálculo usa area_para_calculo()
        cls = classificar(pub.get("teor", ""), pub.get("tipo", ""))

        # Processo visto numa publicação entra na carteira automaticamente.
        # Antes só entrava por importação manual — a aba Processos ficava
        # vazia mesmo com dezenas de prazos ativos, o que não faz sentido:
        # se chegou intimação, o processo existe e é dele.
        if pub["processo"] and pub["processo"] not in por_numero:
            novo = {"numero": pub["processo"], "cliente": "",
                    "area": area or "a_confirmar",
                    "sistema": pub.get("sistema", ""),
                    "tribunal": pub.get("orgao") or pub.get("sistema", ""),
                    "assunto": ""}
            db.salvar_processos([novo])
            por_numero[pub["processo"]] = novo
        elif area and por_numero.get(pub["processo"], {}).get("area") in ("", "a_confirmar", None):
            # área descoberta agora: grava no processo para não rededuzir
            con2 = db.conectar()
            con2.execute("UPDATE processos SET area=? WHERE numero=?",
                         (area, pub["processo"]))
            con2.commit(); con2.close()
            por_numero[pub["processo"]]["area"] = area

        area_gravar = "a_confirmar" if area_desconhecida else area

        # Teor não publicado: não há o que classificar. Rotula como tal para
        # o advogado ver que precisa abrir o processo, em vez de deixar a
        # publicação parecendo um ato que o sistema não soube ler.
        if _sem_teor(pub):
            sem_teor += 1
            if db.criar_prazo(pub_id, pub["processo"], area_gravar,
                              ATO_TEOR_INDISPONIVEL,
                              None, None, None, "teor não publicado"):
                prazos_criados += 1
            continue

        if cls["prazo_dias"] is None:
            # Ato não reconhecido: cria mesmo assim, SEM data, para o advogado
            # revisar. Publicação silenciosamente ignorada = prazo perdido.
            #
            # Mas se a classificação RECONHECEU o ato e apenas não há prazo em
            # dias (regra com dias nulo: audiência, perícia, juntada, ato
            # ordinatório), preserva o rótulo. Descartá-lo aqui — como se
            # fazia — apagava o trabalho das regras e mandava para "A
            # IDENTIFICAR" tudo que era corretamente identificado.
            ato_pendente = (cls["ato"] or "").strip()
            if not ato_pendente or ato_pendente.lower() == "a identificar":
                ato_pendente = "A IDENTIFICAR"
                sem_ato += 1
            if db.criar_prazo(pub_id, pub["processo"], area_gravar,
                              ato_pendente,
                              None, None, None, cls["fonte"]):
                prazos_criados += 1
            continue

        d = pub["data_disponibilizacao"]
        if isinstance(d, str):
            d = date.fromisoformat(d[:10])
        from prazos import area_para_calculo
        calc = calcular_prazo(d, cls["prazo_dias"], area_para_calculo(area),
                              contagem_forcada=cls.get("contagem_declarada", ""),
                              tipo_data=_tipo_data(pub))
        ato = cls["ato"]
        if area_desconhecida:
            # A marcação vai no CAMPO area, não colada no nome do ato:
            # poluía a tela inteira e o ato deixava de ser legível.
            sem_area += 1
        # A fonte do prazo (declarado x presumido) é gravada: é ela que diz
        # ao advogado quanto pode confiar na data antes de conferir.
        fonte = cls.get("fonte") or "sem prazo"
        if cls.get("conflito"):
            fonte += f" · {cls['conflito']}"
        if db.criar_prazo(pub_id, pub["processo"], area_gravar, ato,
                          cls["prazo_dias"], calc["data_fatal"],
                          calc["prazo_interno"], fonte,
                          cls.get("trecho", "")):
            prazos_criados += 1

    resumo = {"publicacoes_novas": novas, "prazos_criados": prazos_criados,
              "a_identificar": sem_ato, "area_a_confirmar": sem_area,
              "teor_indisponivel": sem_teor}
    db.registrar("ingestao", "", str(resumo))
    return resumo


def carregar_exemplo():
    """Popula o banco com a carteira fictícia (para testar o fluxo)."""
    import dados_exemplo as ex
    return processar_publicacoes(ex.PUBLICACOES, ex.PROCESSOS)


def recalcular_pendentes(apenas_pendentes: bool = True) -> dict:
    """Reprocessa os prazos JÁ gravados com as regras atuais.

    Necessário porque as regras melhoram com o uso: uma dedução de área nova,
    um padrão de contagem diferente, um feriado que faltava. Sem isto, o que
    já está no banco continua com a data antiga e o painel passa a mentir.

    Por padrão mexe só no que ainda está PENDENTE DE REVISÃO. Prazo já
    confirmado carrega a decisão do advogado — não se sobrescreve isso por
    conta própria. Para incluí-los, passe apenas_pendentes=False, ciente de
    que a confirmação dele será recalculada.
    """
    from prazos import area_para_calculo
    import carteira

    db.init()
    con = db.conectar()
    prazos = [dict(r) for r in con.execute(
        "SELECT * FROM prazos WHERE status = 'pendente_revisao'"
        if apenas_pendentes else "SELECT * FROM prazos")]
    pubs = {r["id"]: dict(r) for r in con.execute("SELECT * FROM publicacoes")}
    procs = {r["numero"]: dict(r) for r in con.execute("SELECT * FROM processos")}

    mudou = area_mudou = 0
    for p in prazos:
        pub = pubs.get(p["publicacao_id"], {})
        teor = pub.get("teor", "")

        # Publicação sem teor publicado: rotula e segue. Não há classificação
        # possível e nunca haverá — reprocessar todo dia não muda isso.
        if _sem_teor(pub):
            if p["ato"] != ATO_TEOR_INDISPONIVEL:
                con.execute("UPDATE prazos SET ato=?, fonte=? WHERE id=?",
                            (ATO_TEOR_INDISPONIVEL, "teor não publicado", p["id"]))
                mudou += 1
            continue

        cls = classificar(teor, "")

        area = (procs.get(p["processo"], {}) or {}).get("area") or ""
        if area in ("", "a_confirmar"):
            area = carteira.deduzir_area("", teor) or ""
        area_final = area or "a_confirmar"

        dias = cls["prazo_dias"] if cls["prazo_dias"] is not None else p["prazo_dias"]

        # Sem prazo em dias, o cálculo não se aplica — mas o ATO pode ter sido
        # reconhecido agora por uma regra nova. Antes este caminho fazia
        # `continue` seco, e nada do que já estava no banco como
        # "A IDENTIFICAR" era jamais promovido, por melhores que ficassem as
        # regras. É o que tornava o recálculo inútil justamente para os casos
        # que mais precisavam dele.
        if not dias:
            novo_ato = (cls["ato"] or "").strip()
            if (novo_ato
                    and novo_ato.lower() != "a identificar"
                    and novo_ato != p["ato"]):
                con.execute("UPDATE prazos SET ato=?, fonte=?, trecho=? WHERE id=?",
                            (novo_ato, cls.get("fonte") or p["fonte"],
                             cls.get("trecho", ""), p["id"]))
                mudou += 1
            continue

        if not pub.get("data_disponibilizacao"):
            continue

        base = date.fromisoformat(str(pub["data_disponibilizacao"])[:10])
        calc = calcular_prazo(base, int(dias), area_para_calculo(area_final),
                              contagem_forcada=cls.get("contagem_declarada", ""),
                              tipo_data=_tipo_data(pub))

        novo_fatal = str(calc["data_fatal"])
        if novo_fatal != str(p["data_fatal"]) or area_final != p["area"]:
            mudou += 1
            if area_final != p["area"]:
                area_mudou += 1
            con.execute("""UPDATE prazos SET area=?, ato=?, prazo_dias=?,
                           data_fatal=?, prazo_interno=?, fonte=?, trecho=?
                           WHERE id=?""",
                        (area_final, cls["ato"] or p["ato"], int(dias),
                         novo_fatal, str(calc["prazo_interno"]),
                         cls.get("fonte") or p["fonte"],
                         cls.get("trecho", ""), p["id"]))
    con.commit(); con.close()
    resumo = {"analisados": len(prazos), "atualizados": mudou,
              "area_corrigida": area_mudou}
    db.registrar("recalculo", "", str(resumo))
    return resumo
