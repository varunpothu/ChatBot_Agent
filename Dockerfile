FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY agents ./agents
COPY ai_controls ./ai_controls
COPY apps ./apps
COPY dashboard ./dashboard
COPY evaluation ./evaluation
COPY governance ./governance
COPY infra ./infra
COPY knowledge ./knowledge
COPY language ./language
COPY monitoring ./monitoring
COPY ops ./ops
COPY rag ./rag
COPY scripts ./scripts
COPY security ./security
COPY storage ./storage
COPY tests ./tests
COPY translation ./translation
COPY voice ./voice
COPY workers ./workers
COPY web ./web

RUN pip install --no-cache-dir -e . && python -m compileall agents apps evaluation governance infra knowledge rag storage voice workers

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
