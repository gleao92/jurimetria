"""
Teste de fumaça do painel. Uso:  python test_app.py

Executa o app.py de verdade (todas as abas) e falha se qualquer uma levantar
exceção. Subir o servidor e checar a porta NÃO testa nada: o Streamlit só roda
o script quando um cliente conecta. Este teste conecta.
"""
import os, sys, tempfile

DIR_COM_DADOS = tempfile.mkdtemp()          # banco descartável
os.environ["DB_DIR"] = DIR_COM_DADOS
from streamlit.testing.v1 import AppTest
import db, auth, pipeline

db.init(); auth.init()
auth.criar_usuario("teste", "Dr. Teste", "senhaforte1", "advogado")
auth.criar_usuario("apoio1", "Secretária", "senhaforte1", "apoio")
pipeline.carregar_exemplo()

falhas = 0

def cenario(nome, session=None):
    global falhas
    at = AppTest.from_file("app.py", default_timeout=60)
    if session:
        for k, v in session.items():
            at.session_state[k] = v
    at.run()
    if at.exception:
        falhas += 1
        print(f"  FALHA  {nome}")
        for e in at.exception:
            print(f"         {str(e.message)[:160]}")
    else:
        print(f"  PASS   {nome}")
    return at

print("\nTeste de fumaça do painel")

# Primeiro acesso: banco VAZIO, tem que mostrar a tela de criar usuário
import tempfile as _tf, importlib
os.environ["DB_DIR"] = _tf.mkdtemp()
importlib.reload(db); importlib.reload(auth)
db.init(); auth.init()
cenario("primeiro acesso (banco vazio)")

# Volta para o banco com dados
os.environ["DB_DIR"] = DIR_COM_DADOS
importlib.reload(db); importlib.reload(auth)

at = cenario("tela de login (sem sessão)")
cenario("logado como ADVOGADO",
        {"user": {"usuario": "teste", "nome": "Dr. Teste", "papel": "advogado"}})
at3 = cenario("logado como APOIO",
        {"user": {"usuario": "apoio1", "nome": "Secretária", "papel": "apoio"}})

# Permissão: apoio NÃO pode ver a aba de Configuração (credenciais do advogado)
if not at3.exception:
    n_apoio = len(at3.tabs)
    if n_apoio != 4:
        falhas += 1
        print(f"  FALHA  apoio deveria ver 4 abas, viu {n_apoio}")
    else:
        print("  PASS   apoio vê as 4 telas de trabalho")

    # Apoio NÃO pode alcançar Ajustes nem forçando o estado
    at3b = AppTest.from_file("app.py", default_timeout=60)
    at3b.session_state["user"] = {"usuario": "apoio1", "nome": "Secretária",
                                  "papel": "apoio"}
    at3b.session_state["tela"] = "ajustes"
    at3b.run()
    if at3b.exception:
        falhas += 1
        print("  FALHA  apoio forçando tela de ajustes derrubou o app")
    elif len(at3b.tabs) == 4:
        print("  PASS   apoio não alcança Ajustes nem forçando o estado")
    else:
        falhas += 1
        print("  FALHA  apoio conseguiu abrir Ajustes")

# Conteúdo mínimo esperado quando logado
at2 = AppTest.from_file("app.py", default_timeout=60)
at2.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste", "papel": "advogado"}
at2.run()
if not at2.exception:
    n_abas = len(at2.tabs)
    marcado = "".join(str(m.value) for m in at2.markdown)
    print(f"  info   {n_abas} abas renderizadas")
    # Ajustes saiu das abas: agora são 4 telas de trabalho para todo mundo,
    # e a configuração é destino próprio pelo menu do usuário.
    if n_abas != 4:
        falhas += 1
        print(f"  FALHA  esperava 4 abas de trabalho, viu {n_abas}")
    if "situacao" not in marcado:
        falhas += 1
        print("  FALHA  linha de situação não renderizou")
    else:
        print("  PASS   cabeçalho e linha de situação renderizados")

# Painel de detalhe: clicar numa marca do calendário
import db as _db
_ps = _db.listar_prazos()
if _ps:
    at5 = AppTest.from_file("app.py", default_timeout=60)
    at5.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste", "papel": "advogado"}
    at5.session_state["sel_prazo"] = _ps[0]["id"]
    at5.run()
    if at5.exception:
        falhas += 1
        print("  FALHA  painel de detalhe do prazo")
        for e in at5.exception:
            print(f"         {str(e.message)[:160]}")
    else:
        html = "".join(str(m.value) for m in at5.markdown)
        if "a_confirmar\":" in html or ".get(" in html:
            falhas += 1
            print("  FALHA  código Python vazando para a tela")
        elif "detalhe" in html:
            print("  PASS   painel de detalhe renderiza")
        else:
            falhas += 1
            print("  FALHA  painel de detalhe não apareceu")

    at6 = AppTest.from_file("app.py", default_timeout=60)
    at6.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste", "papel": "advogado"}
    at6.session_state["sel_prazo"] = None
    at6.run()
    if at6.exception:
        falhas += 1
        print("  FALHA  agenda sem seleção")
    else:
        print("  PASS   agenda sem seleção renderiza")

    at7 = AppTest.from_file("app.py", default_timeout=60)
    at7.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste", "papel": "advogado"}
    at7.session_state["sel_prazo"] = "id-que-nao-existe"
    at7.run()
    if at7.exception:
        falhas += 1
        print("  FALHA  prazo inexistente derrubou a tela")
    else:
        print("  PASS   prazo inexistente tratado")

    # O clique NÃO pode derrubar o login (bug dos links HTML)
    at8 = AppTest.from_file("app.py", default_timeout=60)
    at8.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste", "papel": "advogado"}
    at8.session_state["sel_prazo"] = _ps[0]["id"]
    at8.run()
    if at8.exception:
        falhas += 1
        print("  FALHA  seleção derrubou a tela")
    elif "user" not in at8.session_state or not at8.session_state["user"]:
        falhas += 1
        print("  FALHA  LOGIN PERDIDO ao selecionar um prazo")
    else:
        textos = "".join(str(m.value) for m in at8.markdown)
        if "Entrar" in textos:
            falhas += 1
            print("  FALHA  voltou para a tela de login")
        else:
            print("  PASS   login preservado ao clicar no prazo")

    # PAINEL DE REVISÃO aberto — é onde estava o ícone inválido que quebrou a
    # tela. O teste anterior nunca abria este painel.
    _pend = [p for p in _ps if p["status"] == "pendente_revisao"]
    if _pend:
        at9 = AppTest.from_file("app.py", default_timeout=60)
        at9.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste",
                                     "papel": "advogado"}
        at9.session_state["abrir"] = _pend[0]["id"]
        at9.run()
        if at9.exception:
            falhas += 1
            print("  FALHA  painel de revisão")
            for e in at9.exception:
                print(f"         {str(e.message)[:170]}")
        else:
            marcado = "".join(str(m.value) for m in at9.markdown)
            faltando = []
            if "class=\"trecho\"" not in marcado and "Onde está o prazo" not in marcado:
                faltando.append("trecho do prazo")
            if "cab-rev" not in marcado:
                faltando.append("número do processo")
            if faltando:
                falhas += 1
                print(f"  FALHA  painel sem: {faltando}")
            else:
                print("  PASS   painel mostra processo e trecho do prazo")

        # O MESMO prazo, aberto pela AGENDA, tem que mostrar o painel de
        # revisão ali mesmo — não um botão que manda para outra aba.
        at10 = AppTest.from_file("app.py", default_timeout=60)
        at10.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste",
                                      "papel": "advogado"}
        at10.session_state["sel_prazo"] = _pend[0]["id"]
        at10.run()
        if at10.exception:
            falhas += 1
            print("  FALHA  painel de revisão pela Agenda")
            for e in at10.exception:
                print(f"         {str(e.message)[:170]}")
        else:
            rotulos = [b.label for b in at10.button]
            if "Confirmar prazo" in rotulos:
                print("  PASS   Agenda revisa no lugar (sem trocar de aba)")
            else:
                falhas += 1
                print(f"  FALHA  Agenda não mostra o painel. Botões: {rotulos[:8]}")
            if "Revisar em Hoje" in rotulos:
                falhas += 1
                print("  FALHA  ainda existe botão que manda para outra aba")

    # A aba Processos precisa OFERECER a correção, não só apontar o problema
    import db as _d
    _con = _d.conectar()
    _con.execute("UPDATE processos SET area='a_confirmar'")
    _con.commit(); _con.close()
    at11 = AppTest.from_file("app.py", default_timeout=60)
    at11.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste",
                                  "papel": "advogado"}
    at11.run()
    if at11.exception:
        falhas += 1
        print("  FALHA  aba Processos com área pendente")
        for e in at11.exception:
            print(f"         {str(e.message)[:170]}")
    else:
        rot = " ".join(b.label for b in at11.button)
        if "como cível" in rot and "Salvar alterações" in rot:
            print("  PASS   Processos oferece correção (lote + edição)")
        else:
            falhas += 1
            print(f"  FALHA  sem ação para corrigir área. Botões: {rot[:120]}")

    # LISTA e PAINEL têm que mostrar a MESMA data fatal. O recálculo aqui usa
    # a MESMA semântica de fonte que o pipeline (_tipo_data): sem isso, o teste
    # compararia maçã com laranja — o pipeline grava tratando a data do DJEN
    # como publicação, e recalcular como disponibilização daria outro dia.
    from datetime import date as _date
    from prazos import calcular_prazo as _cp, area_para_calculo as _apc
    from pipeline import _tipo_data as _td
    divergentes = []
    for p in _ps:
        if not p.get("data_fatal") or not p.get("prazo_dias"):
            continue
        base = _date.fromisoformat(str(p["data_disponibilizacao"])[:10])
        rc = _cp(base, int(p["prazo_dias"]), _apc(p.get("area")),
                 tipo_data=_td(p))
        if str(rc["data_fatal"]) != str(p["data_fatal"]):
            divergentes.append((p["ato"], p["data_fatal"], str(rc["data_fatal"])))
    if divergentes:
        falhas += 1
        print(f"  FALHA  {len(divergentes)} prazos divergem entre lista e painel")
        for a, b, c in divergentes[:3]:
            print(f"         {a}: gravado {b} · recalculado {c}")
    else:
        print("  PASS   lista e painel calculam a mesma data")

    # Tela de Ajustes como destino próprio
    at12 = AppTest.from_file("app.py", default_timeout=60)
    at12.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste",
                                  "papel": "advogado"}
    at12.session_state["tela"] = "ajustes"
    at12.run()
    if at12.exception:
        falhas += 1
        print("  FALHA  tela de Ajustes")
        for e in at12.exception:
            print(f"         {str(e.message)[:170]}")
    else:
        rot = " ".join(b.label for b in at12.button)
        if "← Voltar ao painel" in rot and len(at12.tabs) == 0:
            print("  PASS   Ajustes é tela própria, com volta")
        else:
            falhas += 1
            print(f"  FALHA  Ajustes sem volta ou ainda em aba ({len(at12.tabs)} abas)")

    # Compromisso aparece no calendário e abre para edição
    import compromissos as _comp
    from datetime import date as _dt
    _cid = _comp.criar("audiencia", "Audiência de instrução", _dt.today(),
                       "14:30", 90, "", "Cliente Teste", "Fórum", "", "Dr. Teste")
    at13 = AppTest.from_file("app.py", default_timeout=60)
    at13.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste",
                                  "papel": "advogado"}
    at13.session_state["sel_compromisso"] = _cid
    at13.run()
    if at13.exception:
        falhas += 1
        print("  FALHA  painel de compromisso")
        for e in at13.exception:
            print(f"         {str(e.message)[:170]}")
    else:
        rot = " ".join(b.label for b in at13.button)
        if "Cancelar compromisso" in rot:
            print("  PASS   compromisso abre para edição")
        else:
            falhas += 1
            print(f"  FALHA  compromisso não abriu. Botões: {rot[:110]}")

    at14 = AppTest.from_file("app.py", default_timeout=60)
    at14.session_state["user"] = {"usuario": "teste", "nome": "Dr. Teste",
                                  "papel": "advogado"}
    at14.session_state["novo_comp"] = True
    at14.run()
    if at14.exception:
        falhas += 1
        print("  FALHA  formulário de novo compromisso")
    else:
        rot = " ".join(b.label for b in at14.button)
        print("  PASS   formulário de novo compromisso abre"
              if "Salvar compromisso" in rot else "  FALHA  sem formulário")
        if "Salvar compromisso" not in rot:
            falhas += 1

print(f"\n{'='*46}\n{'TUDO OK' if not falhas else str(falhas)+' CENÁRIO(S) COM ERRO'}\n{'='*46}")
sys.exit(1 if falhas else 0)
