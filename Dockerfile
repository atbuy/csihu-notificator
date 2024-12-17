FROM python:3.12-alpine AS python

# Python cofigurations
ENV PYTHONBUFFERED=true
WORKDIR /app

# Install binaries and headers needed at runtime
RUN apk update && \
  apk add --no-cache g++


# Install dependencies in the second stage
FROM python AS build

# Install needed binaries and headers
RUN apk add --no-cache gcc musl-dev curl curl-dev libffi-dev libssl3 libcrypto3

# Copy source
COPY . /app
WORKDIR /app

# Poetry configuration
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:${PATH}"

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools wheel && \
  # Install poetry
  curl -sSL https://install.python-poetry.org | python3 - && \
  # Install dependencies from poetry lock file
  poetry install --only main --no-interaction --no-ansi


# Run app in third stage
FROM python AS runtime

# Add poetry virtual environment to PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Copy source
COPY --from=build /app /app
WORKDIR /app

ENTRYPOINT [ "python", "csihu/main.py" ]
