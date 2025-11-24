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
import importlib
import json
import subprocess
import sys
import uuid
from functools import lru_cache

import requests
"""
Prepareert een sessie (authenticatie)

Geef ofwel een cookie op, ofwel de een tuple van (key-file-path, cert-file-path).
OpM: Proxies moeten met environment variables gezet worden

"""
from qgis.core import (
    QgsProcessingFeedback,)

def ensure_module(package_name, import_name=None):
    feedback.pushInfo("ensure_module")
    if import_name is None:
        import_name = package_name
    try:
        return importlib.import_module(import_name)
    except ModuleNotFoundError:
        try:

            feedback.pushInfo(f"try install pip {package_name}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return importlib.import_module(import_name)
        except Exception as e:
            feedback.pushInfo(f"Kan module {import_name} niet installeren." )
            feedback.pushInfo(f"e {e} " )
            raise RuntimeError(
                f"Kan module {import_name} niet installeren. "

                f"Installeer handmatig via: pip install {package_name}\n"
                f"Fout: {e}"
            )


jwt = ensure_module("PyJWT", "jwt")

def prepareSession(cookie=None, cert=None):
    session = requests.Session()
    if cookie is not None:
        session.headers.update({'Cookie': 'acm-awv={}'.format(cookie),
                                ##                  'Content-type': 'application/json',
                                })
        print(("authenticatie met cookie : %s" % cookie))
        return session

    if cert is not None:
        session.cert = cert
        print(("authenticatie met cert : %s" % str(cert)))
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
