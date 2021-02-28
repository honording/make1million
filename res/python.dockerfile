FROM  python:3.8

WORKDIR /code

COPY ./res/requirements.txt .

RUN pip install -r /code/requirements.txt

CMD [ "python", "./src/main.py" ] 
