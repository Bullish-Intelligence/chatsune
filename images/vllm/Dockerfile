FROM vllm/vllm-openai:v0.10.2

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src/chatsune /app/src/chatsune

RUN pip install --no-cache-dir "PyYAML>=6.0"

ENV PYTHONPATH=/app/src
ENTRYPOINT ["python", "-m", "chatsune.bootstrap"]
