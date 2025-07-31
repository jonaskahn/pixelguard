FROM python:3.12-bookworm

SHELL [ "/bin/bash", "-c" ]

ENV SHELL=/bin/bash
ENV POETRY_HOME=/etc/poetry
ENV PATH="$POETRY_HOME/venv/bin:$PATH"

RUN apt update && apt upgrade -y

RUN apt install -y g++ gcc cmake curl libssl-dev bash build-essential
RUN apt install -y libpng-dev libjpeg-dev libopenexr-dev libtiff-dev libwebp-dev
RUN apt install -y libsm6 libxext6 ffmpeg libfontconfig1 libxrender1 libgl1-mesa-glx

RUN apt install python3-pip pipx -y
RUN apt install -y python3-opencv

# Install supervisor
RUN apt install -y supervisor

RUN apt autoremove -y
RUN apt autoclean -y

# INSTALL POETRY
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/etc/poetry python3 -

WORKDIR /app

# Copy dependency files first for better layer caching
COPY pyproject.toml poetry.lock* ./
RUN poetry env use $(which python3)
RUN poetry install --only main --no-root

# Copy source code
COPY . .

# Install the project itself
RUN poetry install --only-root

# Create supervisor configuration
RUN mkdir -p /var/log/supervisor
COPY supervisor.conf /etc/supervisor/conf.d/pixelguard.conf

EXPOSE 8000 8501

# Start supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/pixelguard.conf"]