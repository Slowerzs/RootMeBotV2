FROM python:3.9.6

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY ./RootMeBot /opt

ENTRYPOINT ["python3", "/opt/main.py"]
