"""Decide whether Dalton's main branch should go to TestFlight.

Ships when main has moved past the last shipped commit (state/last-shipped) and
has been quiet for QUIET_HOURS, so a burst of merged PRs goes out as one build.
The TestFlight version is the UTC date (2026.10.17): Apple beta-reviews the first build of
each version, so this caps external review at once a day. Dalton's own version rides along in
the What to Test note and in-game. Writes sha/version/upstream_version/build to $GITHUB_OUTPUT.
"""
import base64
import datetime
import json
import os
import re
import subprocess

import asc

UPSTREAM = "DaltonGoesFast/spd-tactics-builds"
QUIET_HOURS = float(os.environ.get("QUIET_HOURS", "2"))
STATE = os.path.join(os.path.dirname(__file__), "..", "state", "last-shipped")


def gh(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


def main():
    force = os.environ.get("FORCE_REF", "").strip()
    commit = gh("repos/%s/commits/%s" % (UPSTREAM, force or "main"))
    sha = commit["sha"]
    when = datetime.datetime.fromisoformat(commit["commit"]["committer"]["date"].replace("Z", "+00:00"))
    age = (datetime.datetime.now(datetime.timezone.utc) - when).total_seconds() / 3600

    presets = base64.b64decode(gh("repos/%s/contents/export_presets.cfg?ref=%s" % (UPSTREAM, sha))["content"]).decode()
    ios = presets[presets.index('name="iOS"'):]
    upstream_version = re.search(r'^application/short_version="([^"]+)"', ios, re.M).group(1)
    today = datetime.datetime.now(datetime.timezone.utc)
    version = "%d.%d.%d" % (today.year, today.month, today.day)

    last = open(STATE).read().strip() if os.path.exists(STATE) else ""
    builds = asc.request("/v1/builds?filter[app]=%s&sort=-uploadedDate&limit=20" % asc.APP_ID)["data"]
    next_build = max([int(b["attributes"]["version"]) for b in builds] or [0]) + 1

    ship = False
    if force:
        ship = True
    elif sha == last:
        print("main (%s) is already in TestFlight" % sha[:7])
    elif age < QUIET_HOURS:
        print("main (%s) moved %.1fh ago; waiting for %gh of quiet" % (sha[:7], age, QUIET_HOURS))
    else:
        ship = True
    if ship:
        print("shipping %s (%s) as %s (%d)" % (sha[:7], upstream_version, version, next_build))

    with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a") as out:
        out.write("ship=%s\nsha=%s\nversion=%s\nupstream_version=%s\nbuild=%d\n"
                  % (str(ship).lower(), sha, version, upstream_version, next_build))


if __name__ == "__main__":
    main()
