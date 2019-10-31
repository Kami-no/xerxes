FROM python:3.7

WORKDIR /opt

COPY leeroy_requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY leeroy.py .
COPY leeroy_config.py config.py

CMD [ "python3", "./leeroy.py" ]
