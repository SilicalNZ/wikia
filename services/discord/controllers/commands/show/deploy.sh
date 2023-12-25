#!/usr/bin/env bash

# THIS SCRIPT IS MADE TO BE CALLED FROM THE MAIN DIRECTORY
docker build --file ./services/discord/controllers/commands/show/main.dockerfile . --tag gcr.io/silical/wikia-discord-commands-show
docker push gcr.io/silical/wikia-discord-commands-show
gcloud run deploy wikia-discord-commands-show  \
  --execution-environment gen2 \
  --image gcr.io/silical/wikia-discord-commands-show \
  --region europe-west1 \
  --memory 512Mi \
  --max-instances 1
