FROM python:2.7.18-stretch

WORKDIR /app_flask

COPY requirements.txt /app_flask/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app_flask/

EXPOSE 8005

CMD ["python", "app.py"]
