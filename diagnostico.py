"""
DIAGNÓSTICO DE FONTES — rode isto ANTES de escrever mais qualquer código.

    python diagnostico.py

Testa, uma a uma, todas as formas de capturar as publicações do advogado e
diz qual responde de verdade. É a resposta para a pergunta que está travando
o projeto: "o criminal do Projudi aparece, e por onde?"

Nada aqui altera o banco. É só leitura e relatório.

CONFIGURAÇÃO (variáveis de ambiente, nunca no código):
    OAB_NUMERO=61423
    OAB_UF=GO
    MNI_USUARIO=<CPF do advogado, sem pontuação>   # opcional
    MNI_SENHA=<senha dele no sistema>              # opcional

Windows (PowerShell):
    $env:OAB_NUMERO="61423"; $env:OAB_UF="GO"; python diagnostico.py
"""

import os
import sys
from datetime import date, timedelta

OAB = os.environ.get("OAB_NUMERO", "61423")
UF = os.environ.get("OAB_UF", "GO")
DESDE = date.today() - timedelta(days=int(os.environ.get("DIAS", "60")))

LARG = 74
resultados = []


def titulo(t):
    print(f"\n{'─' * LARG}\n{t}\n{'─' * LARG}")


def ok(msg):
    print(f"  [OK]    {msg}")


def falha(msg):
    print(f"  [FALHA] {msg}")


def info(msg):
    print(f"          {msg}")


# ══════════════════════════════════════════════════════════════
# 1. DJEN — publicações por número de OAB, SEM certificado
# ══════════════════════════════════════════════════════════════
def testar_djen():
    titulo("1. DJEN — Diário de Justiça Eletrônico Nacional (sem certificado)")
    try:
        import requests
    except ImportError:
        falha("pip install requests")
        return
    url = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
    params = {
        "numeroOab": OAB, "ufOab": UF,
        "dataDisponibilizacaoInicio": DESDE.isoformat(),
        "dataDisponibilizacaoFim": date.today().isoformat(),
        "itensPorPagina": 100, "pagina": 1,
    }
    try:
        r = requests.get(url, params=params, timeout=45)
        info(f"HTTP {r.status_code}  ({r.url[:90]}...)")
        if r.status_code != 200:
            falha(f"resposta {r.status_code} — confira os nomes dos parâmetros no Swagger")
            info(f"corpo: {r.text[:200]}")
            resultados.append(("DJEN", "falhou", r.status_code))
            return
        dados = r.json()
        itens = dados.get("items") or dados.get("content") or dados.get("data") or []
        if isinstance(dados, list):
            itens = dados
        ok(f"{len(itens)} publicações nos últimos {(date.today()-DESDE).days} dias")
        if itens:
            info(f"campos do 1º item: {sorted(itens[0].keys())}")
            sistemas = sorted({str(i.get("siglaTribunal") or i.get("tribunal") or "?")
                               for i in itens})
            print(f"\n  >>> TRIBUNAIS/SISTEMAS QUE APARECERAM: {sistemas}")
            print("  >>> O Projudi/criminal está nessa lista? Essa é A pergunta.\n")
        resultados.append(("DJEN", "funciona", len(itens)))
    except Exception as e:
        falha(f"{type(e).__name__}: {str(e)[:150]}")
        resultados.append(("DJEN", "erro", str(e)[:60]))


# ══════════════════════════════════════════════════════════════
# 2. MNI — webservice oficial do CNJ (usuário/senha, sem token)
# ══════════════════════════════════════════════════════════════
def testar_mni():
    titulo("2. MNI — webservice oficial (usuário/senha, dispensa token A3)")
    usuario = os.environ.get("MNI_USUARIO", "")
    senha = os.environ.get("MNI_SENHA", "")
    if not (usuario and senha):
        info("MNI_USUARIO / MNI_SENHA não definidos — pulando.")
        info("No TJGO o usuário costuma ser o CPF do advogado sem pontuação.")
        resultados.append(("MNI", "não testado", "faltam credenciais"))
        return
    try:
        import mni
    except Exception as e:
        falha(f"não consegui importar mni.py: {e}")
        return
    for chave in ("TJGO_PROJUDI", "TJGO_PJD"):
        try:
            avisos = mni.consultar_avisos_pendentes(chave)
            ok(f"{chave}: {len(avisos)} avisos pendentes")
            if avisos:
                info(f"exemplo: proc {avisos[0]['processo']} "
                     f"em {avisos[0]['data_disponibilizacao']}")
            resultados.append((f"MNI {chave}", "funciona", len(avisos)))
        except Exception as e:
            falha(f"{chave}: {type(e).__name__}: {str(e)[:120]}")
            resultados.append((f"MNI {chave}", "erro", str(e)[:50]))


# ══════════════════════════════════════════════════════════════
# 3. Projudi TJGO — webservice público de acesso automatizado
# ══════════════════════════════════════════════════════════════
def testar_projudi_tjgo():
    titulo("3. Projudi TJGO — ServicosPublicos (acesso automatizado oficial)")
    info("O TJGO publica endpoints de acesso automatizado por sistemas externos.")
    info("Página: transparencia.tjgo.jus.br/ti-comunicacoes/acesso-automatizado")
    try:
        import requests
        r = requests.get("https://projudi.tjgo.jus.br/ServicosPublicos",
                         timeout=30)
        info(f"HTTP {r.status_code}")
        info(f"início da resposta: {r.text[:180]}")
        if r.status_code == 200:
            ok("endpoint respondeu — veja na página oficial os parâmetros de "
               "cada operação")
            resultados.append(("Projudi TJGO", "funciona", r.status_code))
        else:
            falha(f"resposta {r.status_code} — não conclua que funciona")
            resultados.append(("Projudi TJGO", "falhou", r.status_code))
    except Exception as e:
        falha(f"{type(e).__name__}: {str(e)[:150]}")
        resultados.append(("Projudi TJGO", "erro", str(e)[:60]))


# ══════════════════════════════════════════════════════════════
def main():
    print("=" * LARG)
    print(f"DIAGNÓSTICO DE FONTES — OAB {OAB}/{UF}")
    print(f"janela: {DESDE.isoformat()} até {date.today().isoformat()}")
    print("=" * LARG)

    testar_djen()
    testar_mni()
    testar_projudi_tjgo()

    titulo("RESUMO")
    for nome, status, detalhe in resultados:
        print(f"  {nome:22} {status:14} {detalhe}")

    print(f"\n{'=' * LARG}")
    print("COMO LER ESTE RESULTADO")
    print("=" * LARG)
    print("""
  DJEN funcionou e trouxe TODOS os tribunais (inclusive o criminal)
      -> pronto. Use só o DJEN. Nada de token, nada de MNI. Ligue
         captura_djen.py no pipeline e o piloto está de pé.

  DJEN funcionou mas FALTOU o criminal/Projudi
      -> use DJEN para o que ele cobre e MNI (usuário/senha) para o resto.
         Foi para isso que o mni.py existe.

  Nada funcionou
      -> não invente scraping. Ligue para a Diretoria de Informática do TJGO
         e pergunte qual o caminho oficial para consulta automatizada por
         advogado. Eles publicam isso; é conversa de 10 minutos.
""")


if __name__ == "__main__":
    sys.exit(main())
