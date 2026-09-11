from contextlib import closing
from urllib.request import urlopen
import json
from time import sleep, time
import argparse
import unicornhat as uh
from dessinmeteo2 import *
import datetime
#from terminal_manager import *

uh.set_layout(uh.PHAT)
uh.brightness(0.5)

md = Meteo_draw()

parser = argparse.ArgumentParser()
parser.add_argument("--token", required=True, help="Token API Meteo-Concept")
parser.add_argument("--insee", default="69043", help="Code INSEE de la ville")
args = parser.parse_args()

TOKEN = args.token
INSEE = args.insee


weather_codes = {
    # 0–9 : ciel / visibilité
    0: "Ciel clair",
    1: "Peu nuageux",
    2: "Variable",
    3: "Nuageux",
    4: "Très nuageux",
    5: "Brume sèche",
    6: "Brouillard",
    7: "Fumée / poussière",
    8: "Tourbillon de poussière",
    9: "Tempête de poussière",

    # 10–19 : phénomènes proches
    10: "Bruine",
    11: "Bancs de brouillard",
    12: "Brouillard continu",
    13: "Éclairs visibles",
    14: "Précipitations n’atteignant pas le sol",
    15: "Précipitations lointaines",
    16: "Précipitations proches",
    17: "Orage sans pluie",
    18: "Rafales",
    19: "Trombe / tornade",

    # 20–29 : précipitations continues
    20: "Bruine",
    21: "Pluie faible",
    22: "Neige faible",
    23: "Pluie + neige / grésil",
    24: "Pluie verglaçante",
    25: "Averses de pluie",
    26: "Averses de neige",
    27: "Averses de grêle",
    28: "Brouillard",
    29: "Orage",

    # 30–35 : tempêtes de poussière
    30: "Tempête de poussière (faible)",
    31: "Tempête de poussière",
    32: "Tempête de poussière (forte)",
    33: "Tempête sévère (faible)",
    34: "Tempête sévère",
    35: "Tempête sévère (forte)",

    # 36–39 : neige / orages
    36: "Neige soufflée faible",
    37: "Neige soufflée forte",
    38: "Orage faible",
    39: "Orage fort",

    # 40–49 : pluie / neige / orages
    40: "Pluie forte",
    41: "Averses de neige",
    42: "Neige forte",
    43: "Blizzard",
    44: "Non disponible",
    45: "Averses de pluie (nuit)",
    46: "Averses de neige (nuit)",
    47: "Orages dispersés (nuit)",
    48: "Pluie verglaçante",
    49: "Bruine verglaçante",

    # 50–59 : bruine
    **{i: "Bruine" for i in range(50, 60)},  # 50–59

    # 60–69 : pluie
    **{i: "Pluie" for i in range(60, 70)},   # 60–69

    # 70–79 : neige
    **{i: "Neige" for i in range(70, 80)},   # 70–79

    # 80–99 : averses / orages
    80: "Averses de pluie",
    81: "Averses de pluie",
    82: "Averses de pluie forte",
    83: "Averses de pluie forte",
    84: "Averses de pluie violente",
    85: "Averses de neige",
    86: "Averses de neige forte",
    90: "Orage",
    91: "Orage avec pluie",
    92: "Orage fort",
    93: "Orage avec neige",
    94: "Orage violent",
    95: "Orage violent",
    96: "Orage avec grêle",
    97: "Orage violent avec grêle",
    98: "Orage extrême",
    99: "Orage supercellulaire"
}

def decode_period(p):
    mapping = {
        0: "Nuit (02h)",
        1: "Matin (08h)",
        2: "Après midi (14h)",
        3: "Soir (20h)"
    }
    return mapping.get(p, f"Période inconnue ({p})")


def choose_draw(w):
    # --- Interprétation textuelle ---
    if w < 2:
        desc = "Ciel clair / peu nuageux"
        icon = ""
    elif 2 <= w <= 4:
        desc = "Nuageux"
        icon = "cl"
    elif (7 <= w <= 20) or (30 <= w <= 60):
        desc = "Pluie"
        icon = "rain"
    elif (20 <= w <= 40) or (60 <= w <= 100):
        desc = "Neige"
        icon = "snow"
    elif w == 40:
        desc = "Pluie forte"
        icon = "rain"
    elif 40 <= w <= 49:
        desc = "Phénomènes intenses"
        icon = "storm"
    elif 90 <= w <= 99:
        desc = "Orages violents"
        icon = "storm"
    else:
        desc = f"Code météo inconnu ({w})"
        icon = "cl"

    # --- Affichage terminal ---
    print(f"[Météo] Code {w} → {desc}")

    # --- Affichage Unicorn HAT ---
    if icon == "":
        md.show_weather()
    else:
        md.show_weather(icon)


def date_complete_fr(dt_string):
    """
    Convertit '2026-08-31T03:00:00+0200' en :
    'lundi 31 août 2026'
    """

    # On enlève le fuseau horaire (+0200)
    dt_string = dt_string.split("+")[0]

    # Conversion en datetime
    dt = datetime.datetime.fromisoformat(dt_string)

    jours = [
        "lundi", "mardi", "mercredi", "jeudi",
        "vendredi", "samedi", "dimanche"
    ]

    mois = [
        "janvier", "février", "mars", "avril",
        "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"
    ]

    nom_jour = jours[dt.weekday()]
    nom_mois = mois[dt.month - 1]

    return f"{nom_jour} {dt.day} {nom_mois} {dt.year}"



def decode_weather(w):
    if w in weather_codes:
        return weather_codes[w]
    return f"Code météo inconnu ({w})"

# --- Fonction utilitaire pour éviter les KeyError ---
def safe_get(d, key, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return default

while True:
    print("réactualisation des données...")

    # Choix du jour (toujours periods)
    if 13 < int(datetime.datetime.now().strftime('%H')):
        day = 0
    else:
        day = 1

    url = (
        "https://api.meteo-concept.com/api/forecast/daily/"
        + str(day)
        + "/periods"
        + "?token=<TOKEN>"
        + "&insee=69043"
    )
    url = (f"https://api.meteo-concept.com/api/forecast/daily/{day}/periods?token={TOKEN}&insee={INSEE}")


    print(f"Calling url {url}")

    # --- Récupération des données ---
    try:
        with urlopen(url) as f:
            decoded = json.loads(f.read())
    except Exception as e:
        print("Erreur réseau ou JSON :", e)
        continue
    
    city = decoded.get("city", {})
    city_name = city.get("name", "Ville inconnue")
    city_insee = city.get("insee", "?????")

    print(f"Ville : {city_name} ({city_insee})")

    # periods = liste des périodes
    periods = decoded.get("forecast", [])

    print("TYPE periods =", type(periods))
    print("CONTENU periods =", periods)

    if not isinstance(periods, list):
        print("ERREUR : forecast n'est pas une liste :", periods)
        continue
    
            # --- Date complète depuis le premier bloc ---
    dt_string = periods[0].get("datetime", None)

    if dt_string:
        date_complete = date_complete_fr(dt_string)
    else:
        date_complete = "Date inconnue"

    print(f"Prévisions pour le {date_complete}")

    # --- Affichage de chaque période ---
    print("Prévisions par période :")

    for p in periods:
        if not isinstance(p, dict):
            print("Élément ignoré (pas un dict) :", p)
            continue


        period = safe_get(p, "period", "?")
        temp = safe_get(p, "temp2m", "?")
        rain = safe_get(p, "probarain", "?")      
        weather = safe_get(p, "weather", "?")
        hour = safe_get(p, "datetime", "??:??")

        print(f"Période {period} ({decode_period(period)} :")
        print(f"   Température : {temp}°C")
        print(f"   Probabilité Pluie : {rain} %")
        print(f"   Code météo : {weather} → {decode_weather(weather)}")


  # --- Extraction des données pour les 4 périodes ---
    try:
        blocs = [periods[i] for i in range(4)]
    except Exception as e:
        print("Impossible de récupérer les 4 périodes :", e)
        continue

    def extract(bloc):
        return (
            bloc["temp2m"],
            bloc["probarain"],
            bloc["weather"]
        )

    # On prépare une liste structurée : [(period, temp, rain, weather), ...]
    periodes = []
    for i, bloc in enumerate(blocs):
        temp, rain, weather = extract(bloc)
        periodes.append((i, temp, rain, weather))

    # --- Affichage des 4 périodes ---
    tstart = time()

    while time() - tstart < 174:

        for period, temp, rain, weather in periodes:

            print(f"Unicorn affiche période {decode_period(period)}")
            uh.clear()
            # Affichage période (2 LEDs vertes)
            md.show_periods(period)

            # Affichage température
            md.show_temp_columns(temp)
            uh.show()
            sleep(5)
            
            uh.clear()
            # Affichage météo
            choose_draw(weather)

            # Affichage pluie
            md.show_probarain(rain)
            uh.show()
            sleep(5)
           
