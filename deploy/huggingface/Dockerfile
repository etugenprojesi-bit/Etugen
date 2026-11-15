# Hosted demo of Etügen on a Hugging Face Docker Space.
# Upload this file and README.md (same folder) to the Space. The build clones the public
# GitHub repository below, builds the PWA and serves it together with the API on port 7860.
# Secrets (Space settings, never in this file): EE_PROJECT, EE_SERVICE_ACCOUNT_JSON.
# Without them everything works except the satellite layers outside the three demo fields.

# >>> The only line to edit: your public GitHub repository <<<
ARG REPO=https://github.com/YOUR-USER/YOUR-REPO.git

FROM node:24-slim AS web
ARG REPO
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 "$REPO" /src
WORKDIR /src/frontend
RUN npm ci && npm run build

FROM python:3.14-slim
WORKDIR /app
COPY --from=web /src /app
RUN pip install --no-cache-dir -r backend/requirements.txt
# Hugging Face runs the container as user 1000: keep the response cache in a writable place.
ENV CACHE_PATH=/tmp/etugen-cache.sqlite \
    DEMO_CACHE_FIRST=1 \
    PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "7860"]
