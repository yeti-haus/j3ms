FROM python:3

WORKDIR /app

COPY requirements.txt /app
COPY .env /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . /app

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8080", "--debug"]