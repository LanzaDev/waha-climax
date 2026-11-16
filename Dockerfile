# Imagem oficial da Microsoft: Python + Chromium + libs de sistema prontas
# (evita compilar navegador na hora de buildar)
FROM mcr.microsoft.com/playwright/python:v1.65.1-noble

WORKDIR /app

# Instala dependências Python (playwright==1.65.1 casa com a versão da imagem,
# então o Chromium já presente é aproveitado sem baixar de novo)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Só o que a API precisa rodar
COPY config.py print.py api.py ./

# Pasta de saída (no compose é sobrescrita por volume na máquina)
RUN mkdir -p /app/prints_windy

EXPOSE 8000

# -u = saída sem buffer (para "docker compose logs -f" mostrar em tempo real)
# O .env NÃO é copiado (ver .dockerignore) — ele entra como env_file no compose
CMD ["python", "-u", "api.py"]
