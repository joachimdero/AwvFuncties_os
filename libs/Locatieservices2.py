import json
import sys

import Feedback

F_TYPE = {
    'refpunt_wegnr': ["TEXT", 10, "rfpntWnr"],
    'refpunt_opschrift': ["DOUBLE", 0, "rfpntOpsch"],
    'refpunt_afstand': ["LONG", 0, "rfpntAfst"],
    'proj_x': ["DOUBLE", 0],
    'proj_y': ["DOUBLE", 0],
    'wsoidn': ["LONG", 0],
    'Wsoidn': ["LONG", 0],
    'wsoidn_m': ["DOUBLE", 0],
    'begin_refpunt_wegnr': ["TEXT", 10, "bRpntWnr"],
    'begin_refpunt_opschrift': ["DOUBLE", 0, "bRpntOpsch"],
    'begin_refpunt_afstand': ["LONG", 0, "bRpntAfst"],
    'begin_proj_x': ["DOUBLE", 0, "bProjX"],
    'begin_proj_y': ["DOUBLE", 0, "bProjY"],
    'begin_wsoidn': ["LONG", 0, "bWsoidn"],
    'begin_wsoidn_m': ["DOUBLE", 0, "bWsoidnM"],
    'VanM': ["DOUBLE", 0, "VanM"],
    'eind_refpunt_wegnr': ["TEXT", 10, "eRpntWnr"],
    'eind_refpunt_opschrift': ["DOUBLE", 0, "eRpntOpsch"],
    'eind_refpunt_afstand': ["LONG", 0, "eRpntAfst"],
    'eind_proj_x': ["DOUBLE", 0, "eProjX"],
    'eind_proj_y': ["DOUBLE", 0, "eProjY"],
    'eind_wsoidn': ["LONG", 0, "eWsoidn"],
    'eind_wsoidn_m': ["DOUBLE", 0, "eWsoidnM"],
    'TotM': ["DOUBLE", 0, "TotM"],
    'wegnummer': ["TEXT", 10],
}

def request_ls2_puntlocatie(locaties, omgeving="apps", zoekafstand=2, crs=31370, session=None, gebruik_kant_van_de_weg='false', feedback=None):
    URL = f'https://{omgeving}.mow.vlaanderen.be/locatieservices2/rest/puntlocatie/batch?crs={crs}&zoekafstand={zoekafstand}&gebruikKantVanDeWeg={gebruik_kant_van_de_weg}'
    jsonArgs = json.dumps(locaties).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})
    response = session.post(URL, jsonArgs)

    for i in range(4): # retry mechanisme bij timeouts of server errors
        if response.status_code == 200:
            Feedback.feedback_fn("authorisatie gelukt", feedback)
            response_json = response.json()
            return response_json
        elif response.status_code == 401:
            Feedback.feedback_fn(f"status_code: {response.status_code}", feedback)
            raise Exception("Autorisatie mislukt (401). Controleer je cookie.")
        else:
            Feedback.feedback_fn(f"probleem bij opvragen: status {response.status_code}", feedback)
            Feedback.feedback_fn(f'response:{str(response)[:200]}', feedback)
            Feedback.feedback_fn(f'jsonArgs:{jsonArgs[:200]}', feedback)
            raise Exception(f"Fout bij opvragen van locatieservices2 puntlocatie: {response.status_code} {response.reason} {response.text}")

