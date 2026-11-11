FROM python:3.12-slim
WORKDIR /app
RUN useradd --system --uid 10001 lcp
COPY backend/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
USER lcp
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
