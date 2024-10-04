FROM python:3.12.6-slim-bullseye

# https://stackoverflow.com/questions/59812009/what-is-the-use-of-pythonunbuffered-in-docker-file
ENV PYTHONUNBUFFERED 1

WORKDIR /app_django

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app_django/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app_django/

# Disabled those as during deployment its redundant
# RUN chmod +x /app_django/docker_entrypoint.sh
# ENTRYPOINT ["/app_django/docker_entrypoint.sh"]

EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]
