#!/bin/bash

# Run Django development server
daphne src.asgi:application --port 8000 --bind 0.0.0.0
