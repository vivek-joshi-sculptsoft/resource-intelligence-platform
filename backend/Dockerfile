FROM python:3.12-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY startup.sh .
RUN chmod +x startup.sh

EXPOSE 8000
ENTRYPOINT ["./startup.sh"]
CMD ["api"]
