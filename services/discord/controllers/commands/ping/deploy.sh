#!/usr/bin/env bash

# THIS SCRIPT IS MADE TO BE CALLED FROM THE MAIN DIRECTORY
docker build --file ./services/discord/controllers/commands/ping/main.dockerfile . --tag gcr.io/silical/wikia-discord-commands-ping
docker push gcr.io/silical/wikia-discord-commands-ping
gcloud run deploy wikia-discord-commands-ping  \
  --execution-environment gen2 \
  --image gcr.io/silical/wikia-discord-commands-ping \
  --region europe-west1 \
  --memory 512Mi \
  --max-instances 1
