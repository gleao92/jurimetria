"""Configurações gerais. Mude o nome do sistema aqui, num lugar só."""

NOME_SISTEMA = "Tempestivo"
SUBTITULO = "Controladoria de prazos"

# Papéis:
#   advogado -> pode CONFIRMAR prazos (responsabilidade é dele)
#   apoio    -> vê tudo, captura, marca cumprido, mas NÃO confirma classificação
PAPEIS = ["advogado", "apoio"]

# ══════════════════ página pública de captação ══════════════════
# TROQUE ANTES DE DIVULGAR O LINK. Acessível em /?pagina=contato, sem login —
# é a porta de entrada de quem ainda não é cliente (ver pagina_publica.py).
NOME_ESCRITORIO = "Escritório de Advocacia"       # TROQUE AQUI
WHATSAPP_NUMERO = "5562900000000"                 # TROQUE AQUI — só dígitos, com DDI+DDD
AREAS_ATUACAO = ["Cível", "Criminal", "Trabalhista"]  # TROQUE conforme o escritório
CIDADE_REGIAO = "Goiânia e região"                # TROQUE AQUI
