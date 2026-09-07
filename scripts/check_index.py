"""registry.json names every spec directory and nothing else, with current counts."""
import json
import re
import sys
from pathlib import Path

index = json.loads(Path('registry.json').read_text())
on_disk = sorted(p.name for p in Path('specs').iterdir() if p.is_dir())
listed = sorted(index['specs'])
problems = []
if on_disk != listed:
  problems.append(f'index lists {listed}, tree has {on_disk}')
for name, entry in index['specs'].items():
  endpoints = list(Path(f'specs/{name}/spec/endpoints').rglob('endpoint.json'))
  with_examples = sum(
    1 for e in endpoints if (e.parent / 'examples').is_dir() and any((e.parent / 'examples').iterdir())
  )
  if entry.get('endpoints') != len(endpoints):
    problems.append(f'{name}: index says {entry.get("endpoints")} endpoints, tree has {len(endpoints)}')
  if entry.get('endpoints_with_examples') != with_examples:
    problems.append(f'{name}: index says {entry.get("endpoints_with_examples")} with examples, tree has {with_examples}')
  for key in ('description', 'upstream', 'license', 'path', 'source'):
    if not entry.get(key):
      problems.append(f'{name}: missing {key}')
  if not Path(f'specs/{name}/truewire.toml').is_file():
    problems.append(f'{name}: no truewire.toml')
readme = Path('README.md').read_text()
for name, entry in index['specs'].items():
  row = re.search(rf'^\| `{name}` \| (\d+) \| (\d+) \| ([^|]+) \|', readme, re.M)
  if row is None:
    problems.append(f'{name}: no row in README.md')
    continue
  if int(row.group(1)) != entry['endpoints'] or int(row.group(2)) != entry['endpoints_with_examples']:
    problems.append(f'{name}: README row says {row.group(1)}/{row.group(2)}, index says {entry["endpoints"]}/{entry["endpoints_with_examples"]}')
  if row.group(3).strip() != ', '.join(entry['transports']):
    problems.append(f'{name}: README transports {row.group(3).strip()!r} != {entry["transports"]}')
for problem in problems:
  print(problem)
sys.exit(1 if problems else 0)
