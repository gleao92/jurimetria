"""
Cache das leituras do painel.

POR QUE EXISTE
O Streamlit roda o app.py inteiro a cada clique de menu. Isso significa que
`db.listar_prazos()`, `tarefas.listar()`, `financeiro.resumo()` e afins são
refeitos a cada troca de tela, mesmo quando o dado não mudou — cada uma
dessas consultas é um ida-e-volta com o banco (Postgres na nuvem), o que
soma segundos perceptíveis na navegação.

Este módulo devolve um decorador único (`leitura`) que embrulha as funções
de LEITURA com o cache de sessão do Streamlit (`st.cache_data`) e um TTL
curto — dado antigo mostra por até 15s, tempo em que ninguém repara.

INVALIDAR APÓS ESCRITA
Cache de leitura sem invalidação é o pior tipo de bug: o usuário confirma
um prazo, muda de tela, e o prazo confirmado ainda aparece como pendente.
Toda função que ESCREVE (confirmar, marcar pago, criar honorário, salvar
documento) chama `limpar()` no fim — invalida tudo, na dúvida. Sledgehammer
funciona porque o cache é reconstruído no próximo acesso, e essas escritas
não acontecem em rajada.
"""

import streamlit as st


def leitura(ttl: int = 15):
    """Decorador. Cacheia o resultado da função por `ttl` segundos.

    `show_spinner=False` porque o cache é justamente pra fingir que a
    consulta é instantânea — mostrar spinner "carregando" toda vez destruiria
    a percepção de velocidade que o cache existe pra criar.
    """
    return st.cache_data(ttl=ttl, show_spinner=False)


def limpar() -> None:
    """Invalida todo o cache de leitura. Chamar após qualquer escrita.

    Ignora falha silenciosamente porque `st.cache_data.clear()` pode ser
    chamado fora do runtime do Streamlit (por exemplo, dos scripts de
    teste em `test_*.py`) — nesses contextos o clear não faz sentido e a
    exceção travaria o teste sem motivo.
    """
    try:
        st.cache_data.clear()
    except Exception:
        pass
