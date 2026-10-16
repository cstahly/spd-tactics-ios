"""Decide whether Dalton's latest release should go to TestFlight.

Ships when the latest upstream release has no matching version in App Store
Connect yet and has been out for QUIET_HOURS, so a burst of releases goes out
as one build. Writes tag/version/build to $GITHUB_OUTPUT.
"""
import datetime
import json
import os
import subprocess
import sys

import asc

UPSTREAM = "DaltonGoesFast/spd-tactics-builds"
QUIET_HOURS = float(os.environ.get("QUIET_HOURS", "2"))


def gh(*args):
    return json.loads(subprocess.check_output(["gh", "api", *args]))


def main():
    force = os.environ.get("FORCE_TAG", "").strip()
    rel = gh("repos/%s/releases/%s" % (UPSTREAM, "tags/" + force if force else "latest"))
    tag = rel["tag_name"]
    version = tag.lstrip("v")
    published = datetime.datetime.fromisoformat(rel["published_at"].replace("Z", "+00:00"))
    age = (datetime.datetime.now(datetime.timezone.utc) - published).total_seconds() / 3600

    shipped = asc.request("/v1/preReleaseVersions?filter[app]=%s&filter[version]=%s" % (asc.APP_ID, version))["data"]
    latest = asc.request("/v1/builds?filter[app]=%s&sort=-uploadedDate&limit=20" % asc.APP_ID)["data"]
    next_build = max([int(b["attributes"]["version"]) for b in latest] or [0]) + 1

    ship = False
    if shipped and not force:
        print("%s is already in TestFlight" % tag)
    elif age < QUIET_HOURS and not force:
        print("%s is %.1fh old; waiting for %gh of quiet" % (tag, age, QUIET_HOURS))
    else:
        ship = True
        print("shipping %s as build %d" % (tag, next_build))

    with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a") as out:
        out.write("ship=%s\ntag=%s\nversion=%s\nbuild=%d\n" % (str(ship).lower(), tag, version, next_build))


if __name__ == "__main__":
    sys.exit(main())
