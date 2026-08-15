# صورة خدمات AMOS-Federation
# الهدف: بناء صورة موحدة قابلة لتشغيل أي خدمة FastAPI
# النطاق: federal/executive/services
# المالك: federal/executive/services
# تاريخ الإنشاء: 2026-08-15
FROM python:3.12-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings structlog pyjwt

FROM base AS runtime
ARG SERVICE_NAME=api_gateway
ARG SERVICE_PORT=8000
ENV SERVICE_NAME=${SERVICE_NAME} SERVICE_PORT=${SERVICE_PORT} PYTHONPATH=/app/src
EXPOSE ${SERVICE_PORT}
CMD ["sh", "-c", "uvicorn amos_federation.services.${SERVICE_NAME}.main:app --host 0.0.0.0 --port ${SERVICE_PORT}"]
