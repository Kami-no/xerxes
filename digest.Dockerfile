FROM python:3.7

WORKDIR /opt

COPY digest_requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY digest_config.py config.py
COPY digest.py .

CMD [ "python3", "./digest.py" ]
