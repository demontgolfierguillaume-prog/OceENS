#!/usr/bin/env bash

cd /home/mde-admin/OceENS
uv sync --frozen --no-dev

if pgrep -f '[o]ceens-server' >/dev/null; then
    echo "Website already launched"
else
    echo "Launching website with screen"
    screen -d -m bash -c 'uv run --no-sync oceens-server 2> >(tee -a app.error) | tee -a app.log'
fi

if pgrep -f '[o]ceens-summaries-daemon' >/dev/null; then
    echo "Summaries generator already launched"
else
    echo "Launching summaries generator with screen"
    screen -d -m bash -c 'uv run --no-sync oceens-summaries-daemon 2> >(tee -a summaries.error) | tee -a summaries.log'
fi
