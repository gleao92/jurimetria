"""
Captura das publicações — para rodar NO BRASIL, gravando no banco da nuvem.

POR QUE ESTE ARQUIVO EXISTE
O DJEN recusa (403) consultas vindas de servidor no exterior. O Railway roda
nos EUA, então a captura falha lá — mas a mesma consulta funciona a partir de
uma conexão brasileira.

A saída é separar as duas coisas:
  - CAPTURA  roda no computador do escritório (IP brasileiro), por este script
  - PAINEL   continua na nuvem, lendo o mesmo banco

Como o banco (Supabase) é acessível de qualquer lugar, o que este script grava
aparece no painel web imediatamente. Nada de sincronizar arquivo na mão.

COMO USAR
1. Instale as dependências (uma vez):
       pip install -r requirements.txt

2. Aponte para o banco da nuvem — a MESMA string usada no Railway.
   No PowerShell (Windows), na pasta do projeto:

       $env:DATABASE_URL = "postgresql://postgres.XXXX:SENHA@...pooler.supabase.com:5432/postgres"
       python capturar.py

   Sem a DATABASE_URL, ele grava no SQLite local (útil para testar).

3. Para rodar todo dia sem lembrar: Agendador de Tarefas do Windows,
   apontando para o mesmo comando. Sugestão: uma vez de manhã, dia útil.

O QUE ELE FAZ
Busca as publicações da janela indicada, classifica, calcula os prazos e grava.
É idempotente: rodar duas vezes não duplica nada (o banco ignora publicação
já vista). Então pode agendar sem medo de sobrepor.
"""

import argparse
import os
import sys
from datetime import date, timedelta


def principal():
    p = argparse.ArgumentParser(
        description="Captura publicações do DJEN e grava no banco.")
    p.add_argument("--dias", type=int, default=15,
                   help="quantos dias para trás buscar (padrão: 15)")
    p.add_argument("--oab", default="", help="número da OAB (senão, usa a configurada)")
    p.add_argument("--uf", default="", help="UF da OAB")
    args = p.parse_args()

    import configuracao
    cfg = configuracao.carregar()
    oab = args.oab or cfg.get("oab_numero", "")
    uf = args.uf or cfg.get("oab_uf", "GO")

    if not oab:
        print("ERRO: nenhuma OAB informada.")
        print("Use --oab 61423 --uf GO, ou configure na tela de Ajustes.")
        return 1

    destino = ("banco na nuvem (DATABASE_URL definida)"
               if os.environ.get("DATABASE_URL") else "SQLite local")
    print(f"Tempestivo — captura")
    print(f"  OAB ....... {oab}/{uf}")
    print(f"  Janela .... últimos {args.dias} dias")
    print(f"  Gravando em {destino}")
    print()

    import db
    db.init()

    import captura_djen
    desde = date.today() - timedelta(days=args.dias)

    try:
        print("Consultando o DJEN...")
        pubs = captura_djen.capturar_publicacoes(oab, uf, desde)
    except captura_djen.DJENBloqueado as e:
        print("FALHOU — o DJEN recusou a consulta (403).")
        print()
        print(str(e))
        print()
        print("Se você está rodando isto NO BRASIL e mesmo assim deu 403,")
        print("me avise: aí o bloqueio não é geográfico e é outra coisa.")
        return 2
    except Exception as e:
        print(f"FALHOU — {type(e).__name__}: {e}")
        return 2

    if not pubs:
        print("Nenhuma publicação nova nesse período. Nada a fazer.")
        return 0

    print(f"  {len(pubs)} publicações recebidas.")

    import pipeline
    r = pipeline.processar_publicacoes(pubs)

    print()
    print("Resultado:")
    print(f"  publicações novas ....... {r['publicacoes_novas']}")
    print(f"  prazos criados .......... {r['prazos_criados']}")
    print(f"  sem ato reconhecido ..... {r['a_identificar']}")
    print(f"  área a confirmar ........ {r.get('area_a_confirmar', 0)}")
    print()
    if r["prazos_criados"]:
        print("Os prazos novos já aparecem no painel, aguardando revisão.")
    else:
        print("Nada novo — tudo que veio já estava no sistema.")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
