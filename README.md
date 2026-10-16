# spd-tactics-ios

A supporting utility for [SPD Tactics](https://github.com/DaltonGoesFast/spd-tactics-builds) - it ships the game's releases to TestFlight and copies tester feedback back here as issues. The game itself lives in [DaltonGoesFast/spd-tactics-builds](https://github.com/DaltonGoesFast/spd-tactics-builds); this repo is only the iOS pipeline.

Join the beta: https://testflight.apple.com/join/nVbkc9dX

## What runs

- **Ship to TestFlight** (every 6 hours): if upstream `main` has moved since the last shipped commit (`state/last-shipped`) and has been quiet for 2 hours, build it on a macOS runner, upload it, and submit it for beta review for the Community group. The 2-hour wait means a burst of merged PRs ships once. Run it by hand to ship `main` (or any ref) right away.
- **Collect TestFlight feedback** (every 3 hours): new screenshot feedback and crash reports become issues labelled `testflight`. Screenshots are saved in `feedback/` because Apple deletes them after about a week. Tester emails are never copied.

## Secrets

| Name | What |
| --- | --- |
| `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_P8` | App Store Connect API key |
| `DIST_CERT_P12`, `DIST_CERT_PASSWORD` | Apple Distribution cert, base64 .p12 |
| `PROVISIONING_PROFILE` | "SPD Tactics App Store" profile, base64 (expires 2027-06-09) |

Signing is manual on purpose - the API key isn't Admin, so it can't use cloud-managed signing.
