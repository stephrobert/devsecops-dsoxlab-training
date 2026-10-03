FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install flask==3.0.3 werkzeug==3.0.3 ecdsa==0.19.1
ENV PYTHONPATH=/app/src
EXPOSE 5000
CMD ["flask", "--app", "notes_api.app:create_app", "run", "--host", "0.0.0.0"]
