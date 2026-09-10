#!/bin/bash

# Activer le venv
source /home/pi/meteo/venv/bin/activate

# Lancer le script Python avec le bon interpréteur
sudo /home/pi/meteo/venv/bin/python3 /home/pi/meteo/scraper_meteo3.py
