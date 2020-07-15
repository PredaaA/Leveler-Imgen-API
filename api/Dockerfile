FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
COPY ./app /app/app
ENV PYTHONPATH=/app/

RUN pip install --upgrade pip && \
    pip install --no-cache-dir pillow fastapi[all] pymongo motor aiohttp