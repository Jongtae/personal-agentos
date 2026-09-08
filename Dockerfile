FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/
COPY personal_agent /app/personal_agent
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 agentos \
    && mkdir -p /state/data \
    && ln -s /state/data /data \
    && chown -R agentos:agentos /state
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AGENTOS_DATA=/state/data
USER agentos
EXPOSE 8787
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/healthz',timeout=3)"
CMD ["agentos", "start", "--host", "0.0.0.0", "--port", "8787", "--data", "/state/data", "--no-browser"]
