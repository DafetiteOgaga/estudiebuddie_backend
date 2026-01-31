ARG PYTHON_VERSION=3.10-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

COPY requirements.txt /tmp/requirements.txt
RUN set -ex && \
    pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/
COPY . /code

ENV SECRET_KEY "nSd5Gkv6EKODoqhiRY46NG3S7KmOKPg9CFNf5owODdb5zcm8Sa"
RUN python manage.py collectstatic --noinput

EXPOSE 8080

# CMD ["gunicorn", "estudiebuddie_backend.wsgi:application", "--bind", "0.0.0.0:$PORT"]
# CMD ["gunicorn","--bind",":$PORT","--workers","2","estudiebuddie_backend.wsgi"]
CMD ["gunicorn",
        "estudiebuddie_backend.wsgi:application",
        "--bind",
        "0.0.0.0:8080",
        "--workers", "1",
        "--threads", "2",
        "--timeout", "90",
        "--preload"
    ]
