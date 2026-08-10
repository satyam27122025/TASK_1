FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir django==6.1 djangorestframework==3.18.0 djangorestframework-simplejwt==5.5.1 nats-py==2.15.0 python-dotenv==1.2.2 django-cors-headers==4.9.0 PyJWT==2.13.0 sqlparse asgiref tzdata
COPY . .
EXPOSE 8001
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
