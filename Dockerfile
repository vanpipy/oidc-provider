FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml .
COPY app ./app

RUN pip install --no-cache-dir "."

ENV PORT=8000
ENV SECRET_KEY=change-me

EXPOSE 8000

CMD ["sh", "-c", "python -m app.cli seed_demo && serve"]
