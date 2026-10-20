FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ARTICLECRAWLER_PATH=/app/fakenewscitationnetwork \
    PYTHONPATH=/app/article-crawler-backend

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libmagic1 \
        libmagic-dev \
        git \
        tk \
        python3-tk \
    && rm -rf /var/lib/apt/lists/*

COPY install.py package.json ./ 
COPY fakenewscitationnetwork ./fakenewscitationnetwork
COPY article-crawler-backend ./article-crawler-backend
COPY frontend ./frontend

# Set INSTALL_ML=true to also install torch + sentence-transformers (several GB).
# They are only needed for the recommender / title-similarity features, not for the API or UI.
ARG INSTALL_ML=false

RUN pip install --upgrade pip \
    && pip install -e fakenewscitationnetwork[cli] \
    && if [ "$INSTALL_ML" = "true" ]; then pip install -e "fakenewscitationnetwork[ml]"; fi

RUN python - <<'PY'
import nltk
for pkg in ('stopwords', 'punkt', 'wordnet', 'omw-1.4'):
    nltk.download(pkg)
PY

RUN python - <<'PY'
from pathlib import Path
source = Path("article-crawler-backend/requirements.txt")
target = Path("/tmp/backend-requirements.txt")
lines = []
with source.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip().startswith("-e"):
            continue
        lines.append(line)
with target.open("w", encoding="utf-8") as f:
    f.writelines(lines)
print(f"Wrote filtered requirements to {target}")
PY

RUN pip install -r /tmp/backend-requirements.txt

COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
