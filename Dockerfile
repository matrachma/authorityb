FROM jfloff/alpine-python:3.7-onbuild

RUN mkdir /home/code
WORKDIR /home/code
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "run.py"]