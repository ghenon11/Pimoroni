#!/bin/bash

# Activer le venv
source /home/pi/meteo/venv/bin/activate

# Lancer le script Python avec le bon interpréteur
sudo /home/pi/meteo/venv/bin/python3 /home/pi/meteo/scraper_meteo3.py --token= 343a923df2c3fb907e20dcc06d67f8d3d886f7f5803edd99d9377f15c26e8953 --insee 69043
