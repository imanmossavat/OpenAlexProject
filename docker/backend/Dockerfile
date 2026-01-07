FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ARTICLECRAWLER_PATH=/app/fakenewscitationnetwork

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libmagic1 \
        libmagic-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY install.py package.json ./ 
COPY fakenewscitationnetwork ./fakenewscitationnetwork
COPY article-crawler-backend ./article-crawler-backend
COPY frontend ./frontend

RUN pip install --upgrade pip \
    && pip install -e fakenewscitationnetwork[cli] \
    && pip install -r article-crawler-backend/requirements.txt

COPY docker/backend/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
