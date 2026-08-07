"""Configurações gerais. Mude o nome do sistema aqui, num lugar só."""

NOME_SISTEMA = "Tempestivo"
SUBTITULO = "Controladoria de prazos"

# Papéis:
#   advogado -> pode CONFIRMAR prazos (responsabilidade é dele)
#   apoio    -> vê tudo, captura, marca cumprido, mas NÃO confirma classificação
PAPEIS = ["advogado", "apoio"]

# ══════════════════ página pública de captação ══════════════════
# Acessível em /?pagina=contato, sem login — é a porta de entrada de quem
# ainda não é cliente (ver pagina_publica.py). Texto voltado a Direito
# Previdenciário — troque se o foco mudar.
NOME_ESCRITORIO = "Mychelle Xavier"
SUBTITULO_ESCRITORIO = "Advocacia e Consultoria Jurídica"
WHATSAPP_NUMERO = "5562981186562"
CIDADE_REGIAO = "Goiânia e região"                # TROQUE AQUI

HERO_TITULO = "O INSS negou ou atrasou seu benefício?"
HERO_SUBTITULO = (
    "Advogado especialista em Direito Previdenciário. Análise gratuita do "
    "seu caso — descubra em minutos se você tem direito a receber."
)
AREAS_ATUACAO = [
    "Aposentadoria por idade ou tempo de contribuição",
    "Aposentadoria por invalidez",
    "Auxílio-doença (incapacidade temporária)",
    "BPC/LOAS (idoso ou pessoa com deficiência)",
    "Pensão por morte",
    "Revisão de benefício (buscar aumentar o valor)",
]
MENSAGEM_WHATSAPP_PADRAO = (
    "Olá! Quero saber se tenho direito a um benefício do INSS."
)
