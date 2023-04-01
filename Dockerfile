FROM python:3.10-alpine3.17 as python

# Python cofigurations
ENV PYTHONBUFFERED=true
WORKDIR /app

# Install binaries and headers needed at runtime

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" > /etc/apk/repositories && \
    echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    apk update && \
    apk add --no-cache g++ chromium chromium-chromedriver


# Install dependencies in the second stage
FROM python as build

# Install needed binaries and headers
RUN apk add --no-cache gcc musl-dev curl libffi-dev

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
    poetry install --no-dev --no-interaction --no-ansi -vvv


# Run app in third stage
FROM python as runtime

# Add poetry virtual environment to PATH
ENV PATH="/app/.venv/bin:${PATH}"

# Copy source
COPY --from=build /app /app
WORKDIR /app

ENTRYPOINT [ "python", "csihu/main.py" ]
