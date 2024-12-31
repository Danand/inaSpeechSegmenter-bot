FROM python:3.12-bullseye

WORKDIR /app

COPY requirements.txt .

RUN pip install \
      --no-cache-dir \
      -r requirements.txt

COPY src .

CMD [ "python", "bot.py" ]
