#!/usr/bin/env sh
# Provenance: the github and kraken specs are copied from the toolchain repository's
# examples, which are the working projects (core, generated client, tests) behind them.
# Run from a checkout of truewire-dev/truewire next to this one to refresh both.
set -e
TRUEWIRE_REPO="${TRUEWIRE_REPO:-../truewire}"
for name in github kraken; do
  rm -rf "specs/$name/spec"
  cp -r "$TRUEWIRE_REPO/examples/$name/spec" "specs/$name/spec"
  # Keep [project], [spec] and [cores.*]; the [python] sections belong to the source project.
  awk '/^\[python/{skip=1} /^\[/{if($0 !~ /^\[python/) skip=0} !skip' "$TRUEWIRE_REPO/examples/$name/truewire.toml" \
    | sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' > "specs/$name/truewire.toml"
  find "specs/$name" -name __pycache__ -prune -exec rm -rf {} +
done
