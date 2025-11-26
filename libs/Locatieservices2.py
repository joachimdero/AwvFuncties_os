import json
import sys

import Feedback

Feedback.feedback_fn('test')

def requestLs2Puntlocatie(locaties, omgeving, zoekafstand=2, crs=31370, session=None, gebruik_kant_van_de_weg='false', feedback=None):
    Feedback.feedback_fn('testbericht', feedback)
    response_json = None
    url = f'https://apps.mow.vlaanderen.be/locatieservices2/rest/puntlocatie/batch?crs={crs}&zoekafstand={zoekafstand}&gebruikKantVanDeWeg={gebruik_kant_van_de_weg}'

    jsonArgs = json.dumps(locaties).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})
    response = session.post(url, jsonArgs)

    i = 0
    while i < 4:
        i += 1
        if response.status_code == 401:
            Feedback.feedback_fn("authorisatie mislukt: is cookie nog geldig?")
            sys.exit()
        elif response.status_code == 200:
            Feedback.feedback_fn("authorisatie gelukt")
            response_json = response.json()
            i = 4
        else:
            Feedback.feedback_fn(f"probleem bij opvragen: status {response.status_code}")
            Feedback.feedback_fn(f'response:{response[:2]}')
            Feedback.feedback_fn(f'jsonArgs:{jsonArgs[:2]}')

        return response_json