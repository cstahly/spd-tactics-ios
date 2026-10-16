#!/usr/bin/env bash
# Export Dalton's tagged release as an iOS app, sign it with our distribution cert and upload it.
# Usage: build_ios.sh <upstream checkout> <version> <build number>
# Expects GODOT, ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_PATH, and the cert + profile already installed.
set -euo pipefail
SRC="$1" VERSION="$2" BUILD="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"
TEAM=634QAM3ZHG
BUNDLE=com.sadbabyrabbit.spdtactics
PROFILE="SPD Tactics App Store"

cd "$SRC"
# Upstream's iOS preset carries Dalton's bundle id and no team; ours ship under sadbabyrabbit.
sed -i '' -E \
  -e "s|^application/app_store_team_id=.*|application/app_store_team_id=\"$TEAM\"|" \
  -e "s|^application/bundle_identifier=\"com\.daltongoesfast\.spdtactics\"|application/bundle_identifier=\"$BUNDLE\"|" \
  -e "s|^application/short_version=.*|application/short_version=\"$VERSION\"|" \
  -e "s|^application/version=.*|application/version=\"$BUILD\"|" \
  export_presets.cfg
grep -E '^application/(bundle_identifier|app_store_team_id|short_version|version)=' export_presets.cfg

rm -rf builds/ios && mkdir -p builds/ios
"$GODOT" --headless --path . --import >/dev/null 2>&1 || true
"$GODOT" --headless --path . --export-release "iOS" builds/ios/spd-tactics.xcodeproj

xcodebuild -project builds/ios/spd-tactics.xcodeproj -scheme spd-tactics -configuration Release \
  -destination 'generic/platform=iOS' -archivePath builds/ios/SPDTactics.xcarchive \
  CODE_SIGN_STYLE=Manual DEVELOPMENT_TEAM=$TEAM CODE_SIGN_IDENTITY="Apple Distribution" \
  PROVISIONING_PROFILE_SPECIFIER="$PROFILE" archive | tail -5
[ -d builds/ios/SPDTactics.xcarchive ] || { echo "archive failed"; exit 1; }
[ "${DRY_RUN:-}" = true ] && { echo "dry run: signed archive built, skipping upload"; exit 0; }

xcodebuild -exportArchive -archivePath builds/ios/SPDTactics.xcarchive \
  -exportOptionsPlist "$HERE/UploadOptions.plist" -exportPath builds/ios/export \
  -authenticationKeyPath "$ASC_KEY_PATH" -authenticationKeyID "$ASC_KEY_ID" \
  -authenticationKeyIssuerID "$ASC_ISSUER_ID" 2>&1 | grep -vE 'DVTDeveloperAccount|^\s*$' | tail -8
