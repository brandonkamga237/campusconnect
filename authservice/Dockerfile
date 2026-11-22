FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FACE_MODEL_DIR=/app/models
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Modèles de visage téléchargés au build (couche mise en cache tant que le script ne change pas).
COPY scripts/download_models.py scripts/
RUN python scripts/download_models.py /app/models

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app

RUN useradd --system --uid 10001 app && chown -R app /app
USER app

EXPOSE 8081
HEALTHCHECK --interval=10s --timeout=3s --retries=12 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/actuator/health', timeout=2)"
# Applique les migrations puis démarre le service.
CMD ["sh", "-c", "alembic upgrade head && exec python -m app.main"]
