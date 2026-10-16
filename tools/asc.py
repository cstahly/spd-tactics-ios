"""Tiny App Store Connect API client. Creds come from the environment:
ASC_KEY_ID, ASC_ISSUER_ID and ASC_KEY_PATH (the .p8 file)."""
import json
import os
import time
import urllib.error
import urllib.request

import jwt

APP_ID = "6823358733"
COMMUNITY_GROUP = "738f73c3-0ce4-4e43-9100-17c619927a47"


def _token():
    now = int(time.time())
    with open(os.path.expanduser(os.environ["ASC_KEY_PATH"])) as f:
        key = f.read()
    return jwt.encode(
        {"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1200, "aud": "appstoreconnect-v1"},
        key, algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})


def request(path, method="GET", payload=None):
    req = urllib.request.Request(
        "https://api.appstoreconnect.apple.com" + path,
        data=json.dumps(payload).encode() if payload else None,
        headers={"Authorization": "Bearer " + _token(), "Content-Type": "application/json"},
        method=method)
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError("%s %s -> %s %s" % (method, path, e.code, e.read().decode())) from None
