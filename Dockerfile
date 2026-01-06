FROM python:3.14-alpine AS python

# Python cofigurations
ENV PYTHONUNBUFFERED=true
WORKDIR /app


# Install dependencies in the second stage
FROM python AS build

# Copy source
COPY . /app
WORKDIR /app

# Poetry configuration
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:${PATH}"

# Install needed binaries and headers
RUN apk add --no-cache gcc g++ musl-dev libffi-dev libssl3 libcrypto3 && \
  # Upgrade pip and setuptools
  pip install --no-cache-dir --upgrade pip setuptools && \
  # Install poetry
  pip install --no-cache-dir poetry==2.1.2 && \
  # Install dependencies from poetry lock file
  poetry install --no-cache --only main --no-interaction --no-ansi && \
  pip uninstall --no-cache-dir --yes pip setuptools wheel


# Run app in third stage
FROM python AS runtime

# Add poetry virtual environment to PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Copy source
COPY --from=build /app /app
WORKDIR /app

RUN apk add --no-cache libstdc++

ENTRYPOINT [ "python", "csihu/main.py" ]
