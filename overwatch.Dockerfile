FROM python:3.7

WORKDIR /opt

COPY overwatch_requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY overwatch.py .

CMD [ "python3", "./overwatch.py" ]
