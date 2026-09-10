#!/bin/bash

# Activer le venv
source /home/pi/sonometre/venv/bin/activate

# Lancer le script Python avec le bon interpréteur
sudo /home/pi/sonometre/venv/bin/python3 /home/pi/sonometre/sonometer3.py
