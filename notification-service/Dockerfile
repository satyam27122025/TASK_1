FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir django==6.1 djangorestframework==3.18.0 nats-py==2.15.0 python-dotenv==1.2.2 sqlparse asgiref tzdata
COPY . .
EXPOSE 8002
CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8002 & python manage.py consume_notifications"]
