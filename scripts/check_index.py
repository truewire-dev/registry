"""registry.json names every spec directory and nothing else, with current counts.

Counts come from the tree, never from prose:

- `endpoints` is one per `endpoint.json`.
- `endpoints_with_examples` counts endpoints holding a *recorded pair* -- a
  `<id>.request.json` beside its `<id>.response.json`, or a WebSocket `<id>.parameters.json`
  beside its `<id>.reply.json`/`<id>.messages.json`. A request half on its own is an
  instruction for the Record workflow, not evidence, so it does not count.
- `endpoints_unverified` counts endpoints declaring `unverified`. Those are the ones
  `truewire examples --require-verified` excuses, so
  `endpoints_with_examples + endpoints_unverified == endpoints` is the index restating
  the CI gate.
- `status` is derived: `recorded` (every endpoint recorded), `unrecorded` (something is
  waiting for a recording run, reason `not_captured`), `partial` (the rest are declared
  unverified for a reason recording cannot fix -- credentials, state, safety).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ('recorded', 'partial', 'unrecorded')


def paired(endpoint: Path) -> bool:
  """Whether this endpoint holds at least one complete recorded example pair."""
  examples = endpoint.parent / 'examples'
  if not examples.is_dir():
    return False
  names = {path.name for path in examples.iterdir()}
  http = (name.removesuffix('.request.json') for name in names if name.endswith('.request.json'))
  ws = (name.removesuffix('.parameters.json') for name in names if name.endswith('.parameters.json'))
  return any(f'{i}.response.json' in names for i in http) or any(
    f'{i}.reply.json' in names or f'{i}.messages.json' in names for i in ws
  )


def survey(name: str) -> dict:
  """Everything the index claims about one spec, read off the tree."""
  endpoints = sorted((ROOT / 'specs' / name / 'spec' / 'endpoints').rglob('endpoint.json'))
  documents = [json.loads(path.read_text()) for path in endpoints]
  recorded = [path for path in endpoints if paired(path)]
  unverified = [doc['unverified'] for doc in documents if doc.get('unverified')]
  not_captured = [block for block in unverified if block.get('reason') == 'not_captured']
  status = 'recorded' if len(recorded) == len(endpoints) else 'unrecorded' if not_captured else 'partial'
  return {
    'endpoints': len(endpoints),
    'endpoints_with_examples': len(recorded),
    'endpoints_unverified': len(unverified),
    'status': status,
  }


def main() -> int:
  """Report every disagreement between registry.json, README.md and the tree."""
  index = json.loads((ROOT / 'registry.json').read_text())
  on_disk = sorted(p.name for p in (ROOT / 'specs').iterdir() if p.is_dir())
  listed = sorted(index['specs'])
  problems = []
  if on_disk != listed:
    problems.append(f'index lists {listed}, tree has {on_disk}')
  for name, entry in index['specs'].items():
    if name not in on_disk:
      continue
    for key, value in survey(name).items():
      if entry.get(key) != value:
        problems.append(f'{name}: index says {key}={entry.get(key)!r}, tree has {value!r}')
    for key in ('description', 'upstream', 'license', 'path', 'source'):
      if not entry.get(key):
        problems.append(f'{name}: missing {key}')
    if entry.get('status') not in STATUSES:
      problems.append(f'{name}: status must be one of {STATUSES}')
    if entry['endpoints_with_examples'] + entry['endpoints_unverified'] != entry['endpoints']:
      problems.append(
        f'{name}: {entry["endpoints"]} endpoints, {entry["endpoints_with_examples"]} recorded '
        f'and {entry["endpoints_unverified"]} declared unverified; the rest would fail '
        '`truewire examples --require-verified`'
      )
    if not (ROOT / 'specs' / name / 'truewire.toml').is_file():
      problems.append(f'{name}: no truewire.toml')

    # How the Record workflow reaches this API, or why it never will.
    recording = entry.get('recording')
    if not isinstance(recording, dict) or 'recordable' not in recording:
      problems.append(f'{name}: missing `recording` with a `recordable` flag')
      continue
    if recording['recordable']:
      hosts = recording.get('hosts')
      if not isinstance(hosts, dict) or not hosts:
        problems.append(f'{name}: recordable, so `recording.hosts` must map endpoint groups to base URLs')
        continue
      for group, base_url in hosts.items():
        if group and not (ROOT / 'specs' / name / 'spec' / 'endpoints' / group).is_dir():
          problems.append(f'{name}: recording.hosts names {group!r}, which is not a group under spec/endpoints')
        if not str(base_url).startswith('https://'):
          problems.append(f'{name}: recording.hosts[{group!r}] is not an https:// base URL')
      if '' not in hosts:
        problems.append(f'{name}: recording.hosts needs a "" entry, the base URL for ungrouped endpoints')
    elif not recording.get('reason'):
      problems.append(f'{name}: not recordable, so `recording.reason` must say why')
    if entry.get('status') == 'unrecorded' and not recording.get('recordable'):
      problems.append(
        f'{name}: endpoints declare `unverified` with reason `not_captured`, which claims a '
        'recording run would fix them, but the spec is not recordable'
      )

  readme = (ROOT / 'README.md').read_text()
  for name, entry in index['specs'].items():
    row = re.search(rf'^\| `{re.escape(name)}` \| (\d+) \| (\d+) \| ([^|]+) \| ([^|]+) \|', readme, re.M)
    if row is None:
      problems.append(f'{name}: no row in README.md')
      continue
    if int(row.group(1)) != entry['endpoints'] or int(row.group(2)) != entry['endpoints_with_examples']:
      problems.append(
        f'{name}: README row says {row.group(1)}/{row.group(2)}, '
        f'index says {entry["endpoints"]}/{entry["endpoints_with_examples"]}'
      )
    if row.group(3).strip() != ', '.join(entry['transports']):
      problems.append(f'{name}: README transports {row.group(3).strip()!r} != {entry["transports"]}')
    if row.group(4).strip() != entry['status']:
      problems.append(f'{name}: README status {row.group(4).strip()!r} != {entry["status"]!r}')
  for problem in problems:
    print(problem)
  return 1 if problems else 0


if __name__ == '__main__':
  sys.exit(main())
