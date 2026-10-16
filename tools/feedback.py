"""Copy new TestFlight feedback into GitHub issues before Apple expires the screenshots.

Screenshots are committed under feedback/ (Apple's URLs die after about a week) and linked
from the issue. Already-filed items are found by the tf-feedback marker in issue bodies.
Tester emails are never copied - this repo is public.
"""
import json
import os
import subprocess
import urllib.request

import asc

REPO = os.environ["GITHUB_REPOSITORY"]
LABEL = "testflight"


def gh(*args, input=None):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True, input=input).stdout


def filed():
    out = gh("issue", "list", "-R", REPO, "--label", LABEL, "--state", "all", "--limit", "1000", "--json", "body")
    return {line.split("tf-feedback:")[1].split()[0] for i in json.loads(out)
            for line in i["body"].splitlines() if "tf-feedback:" in line}


def build_of(kind, fid):
    try:
        b = asc.request("/v1/%s/%s/build" % (kind, fid))["data"]["attributes"]["version"]
        return "build " + b
    except Exception:
        return "build ?"


def main():
    seen = filed()
    new = []
    for kind, title in (("betaFeedbackScreenshotSubmissions", "Feedback"), ("betaFeedbackCrashSubmissions", "Crash")):
        for item in asc.request("/v1/apps/%s/%s?limit=200" % (asc.APP_ID, kind))["data"]:
            if item["id"] not in seen:
                new.append((kind, title, item))
    if not new:
        print("no new feedback")
        return

    os.makedirs("feedback", exist_ok=True)
    issues = []
    for kind, title, item in new:
        a = item["attributes"]
        images = []
        for n, shot in enumerate(a.get("screenshots") or []):
            path = "feedback/%s-%d.jpg" % (item["id"], n)
            urllib.request.urlretrieve(shot["url"], path)
            images.append(path)
        comment = (a.get("comment") or "").strip() or "(no comment)"
        body = "\n".join([
            "> " + comment.replace("\n", "\n> "),
            "",
            "%s · %s · iOS %s · %s" % (build_of(kind, item["id"]), a.get("deviceModel"), a.get("osVersion"), a.get("createdDate", "")[:16].replace("T", " ")),
            "",
            *["![screenshot](https://raw.githubusercontent.com/%s/main/%s)" % (REPO, p) for p in images],
            "",
            "<!-- tf-feedback:%s -->" % item["id"],
        ])
        issues.append(("%s: %s" % (title, comment.splitlines()[0][:70]), body))

    if any(os.listdir("feedback")):
        subprocess.run(["git", "add", "feedback"], check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode:
            subprocess.run(["git", "commit", "-qm", "Save TestFlight feedback screenshots"], check=True)
            subprocess.run(["git", "push", "-q"], check=True)
    for title, body in issues:
        print(gh("issue", "create", "-R", REPO, "--label", LABEL, "--title", title, "--body-file", "-", input=body).strip())


if __name__ == "__main__":
    main()
