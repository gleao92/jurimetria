"""
FERIADOS FORENSES LOCAIS — ESTE ARQUIVO VOCÊ PRECISA PREENCHER.

Os feriados NACIONAIS e os MÓVEIS (Carnaval, Sexta Santa, Corpus Christi) já
são calculados sozinhos em prazos.py. O que falta são os feriados FORENSES do
TJGO / TRF1 / comarcas — publicados todo ano em PORTARIA do tribunal.

>>> POR QUE ESTÁ VAZIO DE PROPÓSITO <<<
Um feriado errado A MAIS empurra a data fatal para DEPOIS da real — o advogado
protocola confiante e PERDE O PRAZO. Um feriado A MENOS só faz protocolar
adiantado. Como as duas direções não são igualmente ruins, o padrão é vazio:
melhor faltar do que sobrar. NÃO preencha de memória nem por palpite — pegue a
portaria oficial do ano no site do TJGO e transcreva.

O QUE PROCURAR (nomes usuais nas portarias):
  - suspensão de expediente forense / feriados forenses do ano
  - dias de ponto facultativo com expediente suspenso
  - datas locais da comarca onde ele atua (aniversário da cidade etc.)
  - Goiás tem feriados estaduais e cada comarca pode ter os seus

FORMATO: date(ano, mes, dia): "nome"
"""

from datetime import date

FERIADOS_FORENSES_LOCAIS = {
    # EXEMPLOS COMENTADOS — descomente/edite SÓ depois de confirmar na portaria:
    # date(2026, 8, 11): "Dia do Advogado",
    # date(2026, 10, 28): "Dia do Servidor Público",
    # date(2026, 12, 8): "Dia da Justiça",
}

# Quarta-feira de Cinzas: em muitos foros é meio expediente, não feriado cheio.
# Deixe False (conservador) a menos que a portaria diga que não há expediente.
INCLUIR_QUARTA_CINZAS = False
