#!/bin/bash
# O Railway injeta a porta na variável PORT. O $PORT em startCommand nem sempre
# é expandido pelo shell — este script garante a expansão. Se PORT não vier,
# usa 8501 (padrão do Streamlit) para não quebrar em execução local.
PORTA="${PORT:-8501}"
exec streamlit run app.py \
  --server.port="$PORTA" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=true
