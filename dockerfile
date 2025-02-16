# Basis-Image mit Python
FROM python:3.9

RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Kopiere die Abhängigkeiten und installiere sie
COPY --chown=user ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Kopiere den gesamten Code ins Docker-Image
COPY --chown=user . /app

# Starte die FastAPI-App
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
