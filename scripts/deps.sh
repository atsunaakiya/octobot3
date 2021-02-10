#!/usr/bin/env bash
if [ ! -d venv ]; then
  python -m venv venv
fi
pip install -r requirements.txt
