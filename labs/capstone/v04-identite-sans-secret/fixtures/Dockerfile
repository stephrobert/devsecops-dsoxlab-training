FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install flask==3.1.3 werkzeug==3.1.9 cryptography==50.0.2
ENV PYTHONPATH=/app/src
EXPOSE 5000
CMD ["flask", "--app", "notes_api.app:create_app", "run", "--host", "0.0.0.0"]
