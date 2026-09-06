FROM python:3.12-slim

WORKDIR /code

RUN useradd -m -u 1000 user

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN chown -R user:user /code

USER user

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]