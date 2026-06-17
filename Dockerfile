FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY core/ core/
COPY scripts/ scripts/
COPY static/ static/
COPY templates/ templates/
COPY server.py webui.py migrate.py ./
COPY docs/ docs/

RUN mkdir -p /app/data

EXPOSE 5100 5000

ENV CONTEXTKEEP_DB_PATH=/app/data/contextkeep.db

CMD ["python", "scripts/start_services.py"]
