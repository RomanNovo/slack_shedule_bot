# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9

EXPOSE 8000


# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

RUN apt-get update -y

RUN apt-get install -y cron htop vim

RUN touch /var/log/cron.log

RUN chmod +x worker_entrypoint.sh

VOLUME [ "/app/data" ]

CMD ["uvicorn", "main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000"]
