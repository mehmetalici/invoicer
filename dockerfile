FROM python:3.10.7
COPY . /app
WORKDIR /app
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV poetry=/root/.local/bin/poetry
RUN $poetry config virtualenvs.create false \
  && $poetry install --no-interaction --no-ansi
CMD $poetry run python3 app.py

