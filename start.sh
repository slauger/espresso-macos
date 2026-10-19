#!/bin/bash

# Activate virtual environment and start espresso-gui
cd "$(dirname "$0")"
source venv/bin/activate
espresso-gui
