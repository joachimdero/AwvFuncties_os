# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      derojp
#
# Created:     22/02/2023
# Copyright:   (c) derojp 2023
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import datetime
import json
import uuid
from functools import lru_cache

import requests
"""
Prepareert een sessie (authenticatie)

Geef ofwel een cookie op, ofwel de een tuple van (key-file-path, cert-file-path).
OpM: Proxies moeten met environment variables gezet worden

"""



# utils_feedback.py
def feedback_fn(bericht, feedback=None):
    if feedback:  # QGIS feedback object
        try:
            feedback.pushInfo(bericht)
            return
        except AttributeError:
            pass
    try:
        from arcpy import AddMessage  # ArcGIS
        AddMessage(bericht)
    except ImportError:
        print(bericht)  # Standalone



def prepareSession(cookie=None, cert=None, feedback=None):
    session = requests.Session()
    if cookie is not None:
        session.headers.update({'Cookie': 'acm-awv={}'.format(cookie),
                                ##                  'Content-type': 'application/json',
                                })
        feedback_fn(f"Authenticatie met cookie: {cookie}", feedback)
        return session

    if cert is not None:
        session.cert = cert
        feedback_fn(f"Authenticatie met cert: {cert}", feedback)
        return session


@lru_cache(maxsize=1)
def get_access_token(awv_key):
    import jwt
    with open(awv_key, 'r') as file:
        config = json.load(file)
    client_id = config.get('clientid')
    jwk_private = config.get('jwk_private')

    authentication_url = "https://authenticatie.vlaanderen.be/op"
    authentication_url_token = "https://authenticatie.vlaanderen.be/op/v1/token"
    due_date = datetime.datetime.now() + datetime.timedelta(minutes=5)
    expiry = int(due_date.timestamp())

    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": authentication_url,
        "exp": expiry, "jti": uuid.uuid4().hex
    }
    private_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk_private))
    jwt_token = jwt.encode(payload, private_key, algorithm="RS256")
    access_token_data = {"grant_type": "client_credentials", "scope": "awv_toep_services",
                         "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                         "client_id": client_id, "client_assertion": jwt_token}
    r = requests.post(url=authentication_url_token, data=access_token_data,
                      headers={"content-type": "application/x-www-form-urlencoded"})
    print(f"r.json(): {r.json()}")
    access_token = r.json()["access_token"]
    print(r.status_code, r.reason, r.content)
    return access_token, expiry


def get_valid_token(awv_key):
    token, expiry = get_access_token(awv_key)
    current_time = datetime.datetime.now().timestamp()
    print(f"🕒 Huidige tijd: {datetime.datetime.fromtimestamp(current_time)} ({current_time})")
    print(
        f"🔄 Vernieuwing nodig? {current_time >= expiry - 300} (Expiry: {expiry},{datetime.datetime.fromtimestamp(expiry)})")

    if current_time >= expiry - 300:  # Vernieuw token als het binnen 5 minuten verloopt
        print("vernieuwing token")
        get_access_token.cache_clear()
        token, _ = get_access_token(awv_key)
        print(f"✅ Nieuw token geldig tot: {datetime.datetime.fromtimestamp(expiry)} ({expiry})")
    return token


def proxieHandler(session):
    try:
        proxy = {'https': 'http://proxy.vlaanderen.be:8080/proxy.pac'}
        session.proxies.update(proxy)
        session.get("https://www.google.com")
        print('met proxy')

    except:
        proxy = {'https': None}
        session.proxies.update(proxy)
        session.get("https://www.google.com")
        print('zonder proxy')

    return session
