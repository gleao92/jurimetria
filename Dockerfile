FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sanidade: se o motor de prazos estiver quebrado, a imagem nem constrói.
RUN python test_prazos.py && python test_app.py

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit","run","app.py","--server.port=8501","--server.address=0.0.0.0","--server.headless=true"]
