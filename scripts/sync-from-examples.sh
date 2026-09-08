#!/usr/bin/env sh
# Provenance: every spec here is copied from the working project behind it -- the one with
# the hand-written core, the generated client and the tests. Run this from a checkout of
# each source repository next to this one to refresh the copies.
#
#   github, kraken: truewire-dev/truewire, under examples/<name>/
#   open-meteo:     truewire-dev/open-meteo, at its root
#
# Specs authored in this repository (no source project) are not listed here; they have
# nothing to sync from.
set -e
TRUEWIRE_REPO="${TRUEWIRE_REPO:-../truewire}"
OPEN_METEO_REPO="${OPEN_METEO_REPO:-../open-meteo}"

# Keep [project], [spec], [secrets] and [cores.*]; the [python] sections belong to the
# source project, which is the only place a package gets generated.
strip_python() {
  awk '/^\[python/{skip=1} /^\[/{if($0 !~ /^\[python/) skip=0} !skip' "$1" \
    | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}'
}

sync() {
  name="$1"
  source_dir="$2"
  rm -rf "specs/$name/spec"
  cp -r "$source_dir/spec" "specs/$name/spec"
  strip_python "$source_dir/truewire.toml" > "specs/$name/truewire.toml"
  find "specs/$name" -name __pycache__ -prune -exec rm -rf {} +
}

for name in github kraken; do
  sync "$name" "$TRUEWIRE_REPO/examples/$name"
done
sync open-meteo "$OPEN_METEO_REPO"

# The comments in specs/open-meteo/truewire.toml are re-worded for a spec with no core;
# `git diff` after a sync shows them coming back. Keep the registry's wording.
echo "Synced. Re-run: python scripts/check_index.py"
