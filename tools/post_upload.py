"""After an upload: wait for processing, set What to Test, hand the build to the
Community group and submit it for beta review.
Usage: post_upload.py <version> <build> <upstream version> <upstream sha>"""
import sys
import time

import asc

WHAT_TO_TEST = ("Everything. Run the whole loop - camp, delve, fight, and extract at the floor 5 campfire "
                "after Goo (or die trying). Tell me about crashes, anything that looks wrong on your screen, "
                "and anything that feels unfair.")


def find_build(version, build):
    path = "/v1/builds?filter[app]=%s&filter[version]=%s&filter[preReleaseVersion.version]=%s" % (asc.APP_ID, build, version)
    for _ in range(60):  # processing usually takes 5-15 minutes
        data = asc.request(path)["data"]
        if data:
            state = data[0]["attributes"]["processingState"]
            print("build %s: %s" % (build, state))
            if state == "VALID":
                return data[0]["id"]
            if state in ("FAILED", "INVALID"):
                sys.exit("processing failed")
        time.sleep(30)
    sys.exit("timed out waiting for processing")


def main(version, build, upstream_version, sha):
    bid = find_build(version, build)
    notes = "SPD Tactics %s (%s)\n\n%s" % (upstream_version, sha[:7], WHAT_TO_TEST)
    for loc in asc.request("/v1/builds/%s/betaBuildLocalizations" % bid)["data"]:
        asc.request("/v1/betaBuildLocalizations/" + loc["id"], "PATCH",
                    {"data": {"type": "betaBuildLocalizations", "id": loc["id"], "attributes": {"whatsNew": notes}}})
    asc.request("/v1/betaGroups/%s/relationships/builds" % asc.COMMUNITY_GROUP, "POST",
                {"data": [{"type": "builds", "id": bid}]})
    try:
        asc.request("/v1/betaAppReviewSubmissions", "POST",
                    {"data": {"type": "betaAppReviewSubmissions", "relationships": {"build": {"data": {"type": "builds", "id": bid}}}}})
        print("build %s attached to Community and submitted for beta review" % build)
    except RuntimeError as e:
        # Later builds of an already-approved version are often let through without a submission.
        state = asc.request("/v1/builds/%s/buildBetaDetail" % bid)["data"]["attributes"]["externalBuildState"]
        print("build %s attached to Community; review submission refused (%s), build is %s" % (build, str(e)[:200], state))
        if state not in ("BETA_APPROVED", "IN_BETA_TESTING", "WAITING_FOR_BETA_REVIEW", "IN_BETA_REVIEW"):
            raise


if __name__ == "__main__":
    main(*sys.argv[1:5])
