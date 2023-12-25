#-- Build base image ---------------------------------------------------------------------------------------------------
FROM python:3.10-slim AS dependency_solving_environment

# Install tools
RUN apt-get update
RUN apt-get install git -y

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

# Workdir
ARG WORKING_DIRECTORY=/opt/src/project
WORKDIR ${WORKING_DIRECTORY}

# Copy project code
COPY ./services/discord/controllers/commands/ping ./services/discord/controllers/commands/ping
COPY ./services/discord/shared ./services/discord/shared
COPY ./shared ./shared

# Env
ENV is_prod false

# Download python modules
RUN pip install --no-cache-dir -r ./services/discord/controllers/commands/ping/requirements.txt -U

# Run
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --worker-class aiohttp.worker.GunicornWebWorker --chdir ./services/discord/controllers/commands/ping/ main:app
