"""
Dados de exemplo — substituídos pela captura real (captura.py) quando conectada.
Simula a carteira de um advogado que atua em cível, criminal e rural, em
tribunais diferentes (PJe, eSAJ, eproc). As datas são relativas a HOJE para o
painel sempre mostrar uma mistura realista de urgências.
"""

from datetime import date, timedelta

HOJE = date.today()

PROCESSOS = [
    {"numero": "1002345-67.2026.8.09.0051", "cliente": "Fazenda Boa Vista Ltda.",
     "area": "civel", "sistema": "PJe", "tribunal": "TJGO", "assunto": "Ação de cobrança"},
    {"numero": "5001234-12.2026.4.01.3500", "cliente": "João Pereira da Silva",
     "area": "civel", "sistema": "eproc", "tribunal": "TRF1", "assunto": "Usucapião rural"},
    {"numero": "0007654-32.2026.8.09.0100", "cliente": "Marcos A. de Souza",
     "area": "criminal", "sistema": "PJe", "tribunal": "TJGO", "assunto": "Ação penal"},
    {"numero": "1005678-90.2026.8.26.0053", "cliente": "Agropecuária Rio Verde S/A",
     "area": "civel", "sistema": "eSAJ", "tribunal": "TJSP", "assunto": "Servidão de passagem"},
    {"numero": "0003210-45.2026.8.09.0175", "cliente": "Antônio C. Ferreira",
     "area": "criminal", "sistema": "eproc", "tribunal": "TJGO", "assunto": "Queixa-crime"},
    {"numero": "1009876-54.2026.8.09.0051", "cliente": "Sítio Três Marias",
     "area": "civel", "sistema": "PJe", "tribunal": "TJGO", "assunto": "Reintegração de posse"},
]

PUBLICACOES = [
    # Textos no formato REAL do DJEN: declaram o prazo por extenso, citam o
    # órgão e trazem fundamentação junto. A versão anterior usava frases
    # curtas inventadas ("no prazo legal") que davam ao sistema uma facilidade
    # que a publicação de verdade não dá.
    {"processo": "0007654-32.2026.8.09.0100", "sistema": "PJe",
     "orgao": "2ª Vara Criminal de Goiânia",
     "data_disponibilizacao": HOJE - timedelta(days=7),
     "teor": "PODER JUDICIÁRIO DO ESTADO DE GOIÁS 2ª Vara Criminal de Goiânia. "
             "Autos nº 0007654-32.2026.8.09.0100. Recebida a denúncia oferecida "
             "pelo Ministério Público, cite-se o acusado para apresentar "
             "RESPOSTA À ACUSAÇÃO, por escrito, no prazo de 10 (dez) dias, nos "
             "termos do art. 396 do Código de Processo Penal, podendo arguir "
             "preliminares e alegar tudo o que interesse à sua defesa."},

    {"processo": "1002345-67.2026.8.09.0051", "sistema": "PJe",
     "orgao": "Goiânia - 3ª UPJ Varas Cíveis: 6ª Vara Cível",
     "data_disponibilizacao": HOJE - timedelta(days=1),
     "teor": "Trata-se de ação de cobrança. Cite-se a parte requerida para, "
             "querendo, apresentar contestação no prazo de 15 (quinze) dias "
             "úteis, sob pena de revelia e confissão quanto à matéria de fato, "
             "nos termos dos arts. 335 e 344 do CPC."},

    {"processo": "1005678-90.2026.8.26.0053", "sistema": "eSAJ",
     "orgao": "Vara da Fazenda Pública",
     "data_disponibilizacao": HOJE - timedelta(days=6),
     "teor": "Vistos. Manifeste-se a parte autora, no prazo de 15 (quinze) "
             "dias, sobre a contestação e os documentos que a acompanham, "
             "especificando as provas que pretende produzir, justificando a "
             "pertinência de cada uma."},

    {"processo": "5001234-12.2026.4.01.3500", "sistema": "eproc",
     "orgao": "15ª Vara Federal de Juizado Especial Cível",
     "data_disponibilizacao": HOJE - timedelta(days=3),
     "teor": "ATO ORDINATÓRIO (art. 203, § 4º do CPC). Trata-se de ação em que "
             "a parte autora pretende a concessão de benefício por incapacidade "
             "temporária em face do INSS – Instituto Nacional do Seguro Social. "
             "Fica a parte autora intimada para juntar aos autos, no prazo de "
             "15 (quinze) dias, sob pena de indeferimento da petição inicial, "
             "os documentos necessários à propositura da demanda."},

    {"processo": "0003210-45.2026.8.09.0175", "sistema": "eproc",
     "orgao": "Vara Criminal de Aparecida de Goiânia",
     "data_disponibilizacao": HOJE - timedelta(days=2),
     "teor": "Encerrada a instrução processual, intimem-se as partes para "
             "apresentação de ALEGAÇÕES FINAIS por memoriais, no prazo "
             "sucessivo de 5 (cinco) dias, iniciando-se pela acusação."},

    {"processo": "1009876-54.2026.8.09.0051", "sistema": "PJe",
     "orgao": "Goiânia - 3ª UPJ Varas Cíveis: 6ª Vara Cível",
     "data_disponibilizacao": HOJE - timedelta(days=1),
     "teor": "Sentença publicada em audiência. Julgo procedente o pedido "
             "inicial. Ficam as partes intimadas do teor da sentença, correndo "
             "o prazo de 15 (quinze) dias para eventual recurso de apelação, "
             "na forma do art. 1.003 do CPC."},

    # Sem prazo declarado nem ato reconhecível: tem que cair em revisão,
    # nunca receber uma data chutada.
    {"processo": "1002345-67.2026.8.09.0051", "sistema": "PJe",
     "orgao": "Goiânia - 3ª UPJ Varas Cíveis: 6ª Vara Cível",
     "data_disponibilizacao": HOJE - timedelta(days=4),
     "teor": "Certifico que os autos foram remetidos à contadoria judicial "
             "para elaboração dos cálculos. Nada mais."},
]
