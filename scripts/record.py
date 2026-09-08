"""Record a registry spec's examples against the live API, through a throwaway client.

A registry spec is only a spec: no core, no generated package, and no base URL, so nothing
here can call anything on its own. This script supplies the missing half from
`registry.json`'s `recording` block, in a directory it throws away afterwards:

1. `truewire init` a scratch project, whose default core template is exactly one HTTP
   transport with a base URL, a path-templating `send` and no auth.
2. Copy the registry spec into it and splice the spec's own `[cores.*]` tables over the
   template's, so `meta` validates against the schema the spec was written for.
3. `truewire generate python`.
4. Replay every `examples/<id>.request.json` through that client with `truewire capture`,
   which writes `<id>.response.json` beside it and drops the endpoint's now-false
   `unverified` declaration.
5. Copy the spec tree back over `specs/<name>/spec`, and refresh the counts in
   `registry.json` and the table in `README.md`.

Only a spec whose `recording.recordable` is true is touched: those are the public,
credential-free APIs. Nothing here reads a credential, and `--new` carries only a base URL.

  python scripts/record.py                 # every recordable spec
  python scripts/record.py --spec hacker-news
  python scripts/record.py --spec hacker-news --keep /tmp/scratch   # keep the client
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTEMPTS = 3
TRUEWIRE = str(Path(sys.executable).with_name('truewire'))


def run(*command: str, cwd: Path | None = None) -> None:
  """Run one truewire command, failing loudly."""
  print('$', ' '.join(command), flush=True)
  subprocess.run(command, cwd=cwd, check=True)


def tables(text: str) -> list[tuple[str, str]]:
  """Split a TOML document into (table name, text) pairs; the preamble is named ''."""
  out: list[tuple[str, list[str]]] = [('', [])]
  for line in text.splitlines(keepends=True):
    header = re.match(r'\[+([^\]]+)\]+', line)
    if header:
      out.append((header.group(1).strip(), []))
    out[-1][1].append(line)
  return [(name, ''.join(lines)) for name, lines in out]


def scratch_config(template: str, spec: str) -> str:
  """The scratch project's `truewire.toml`: its own `[python]`, the spec's `[cores]`.

  The template's `[project]`, `[spec]` and `[python*]` tables say where the package goes;
  every other table comes from the registry spec, because `[cores.<name>]` is the schema
  the spec's own `meta` blocks were written against. Each core the spec names also needs a
  `[python.cores.<name>]` base class, which the template only wrote for its own two.
  """
  kept = [text for name, text in tables(template) if name in ('', 'project', 'spec') or name.startswith('python')]
  carried = [text for name, text in tables(spec) if name not in ('', 'project', 'spec')]
  return ''.join(kept + carried)


def cores(spec_dir: Path) -> set[str]:
  """Every symbolic core name the spec's routers declare."""
  named = {json.loads(path.read_text()).get('core') for path in spec_dir.rglob('router.json')}
  return {name for name in named if name}


def endpoints(project: Path) -> list[tuple[str, Path]]:
  """`(function, endpoint.json path)` for every endpoint in a scratch project."""
  from truewire.cli.common import resolve_project
  from truewire.spec.repo import endpoint_records

  loaded = resolve_project(str(project))
  return [
    (record.endpoint.resolved_function(record.path, loaded.spec_dir), record.path)
    for record in endpoint_records(loaded)
  ]


def base_url(function: str, hosts: dict[str, str]) -> str:
  """The host for one endpoint: the longest declared group prefix that matches it."""
  group = max(
    (name for name in hosts if not name or function.startswith(name.replace('/', '.') + '.')),
    key=len,
  )
  return hosts[group]


def record_spec(name: str, entry: dict, keep: Path | None, pause: float) -> int:
  """Record every example of one spec. Returns the number of endpoints that failed."""
  recording = entry['recording']
  if not recording.get('recordable'):
    print(f'{name}: not recordable ({recording.get("reason", "no reason given")}); skipped')
    return 0
  hosts = recording['hosts']
  package = name.replace('-', '_')
  workdir = Path(keep) if keep else Path(tempfile.mkdtemp(prefix=f'record-{name}-'))
  project = workdir / package
  shutil.rmtree(project, ignore_errors=True)

  run(TRUEWIRE, 'init', package, '--dir', str(project), '--base-url', hosts[''])
  registry_spec = ROOT / entry['path'] / 'spec'
  shutil.rmtree(project / 'spec')
  shutil.copytree(registry_spec, project / 'spec')
  config = scratch_config(
    (project / 'truewire.toml').read_text(),
    (ROOT / entry['path'] / 'truewire.toml').read_text(),
  )
  extra = ''.join(
    f'\n[python.cores.{core}]\nbase = "{package}.core:Endpoint"\n'
    for core in sorted(cores(project / 'spec'))
    if f'[python.cores.{core}]' not in config
  )
  (project / 'truewire.toml').write_text(config + extra)
  run(TRUEWIRE, 'generate', 'python', '--project', str(project))

  failures = 0
  for function, path in sorted(endpoints(project)):
    examples = path.parent / 'examples'
    requests = sorted(examples.glob('*.request.json')) if examples.is_dir() else []
    for frame in sorted(examples.glob('*.parameters.json')) if examples.is_dir() else []:
      print(f'{function}: {frame.name} is a WebSocket example; `truewire capture` records HTTP pairs only')
    if not requests:
      print(f'{function}: no request half to replay; nothing to record')
      continue
    for request in requests:
      example = json.loads(request.read_text())
      command = [
        TRUEWIRE, 'capture', function,
        '--project', str(project),
        '--new', f'base_url={base_url(function, hosts)}',
        '--id', request.name.removesuffix('.request.json'),
        '--request', json.dumps(example['request']),
      ]
      if example.get('description'):
        command += ['--description', example['description']]
      print('$', ' '.join(command), flush=True)
      for attempt in range(1, ATTEMPTS + 1):
        if subprocess.run(command).returncode == 0:
          break
        # A public API answering from CI drops a connection now and then; a 4xx never
        # heals, but `capture` prints the status and the body, so a real refusal is
        # readable in the log above whether or not the retries follow it.
        print(f'  attempt {attempt}/{ATTEMPTS} failed', flush=True)
        time.sleep(pause + attempt * 2)
      else:
        failures += 1
      time.sleep(pause)

  shutil.rmtree(ROOT / entry['path'] / 'spec')
  shutil.copytree(project / 'spec', ROOT / entry['path'] / 'spec')
  if keep is None:
    shutil.rmtree(workdir, ignore_errors=True)
  return failures


def refresh_index(names: list[str]) -> None:
  """Bring `registry.json`'s counts and `README.md`'s table back in step with the tree."""
  sys.path.insert(0, str(ROOT / 'scripts'))
  from check_index import survey

  index_file = ROOT / 'registry.json'
  index = json.loads(index_file.read_text())
  readme_file = ROOT / 'README.md'
  readme = readme_file.read_text()
  for name in names:
    entry = index['specs'][name]
    entry.update(survey(name))
    row = (
      f'| `{name}` | {entry["endpoints"]} | {entry["endpoints_with_examples"]} '
      f'| {", ".join(entry["transports"])} | {entry["status"]} |'
    )
    readme = re.sub(rf'^\| `{re.escape(name)}` \|.*$', row, readme, count=1, flags=re.M)
  index_file.write_text(json.dumps(index, indent=2) + '\n')
  readme_file.write_text(readme)


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--spec', help='One spec name; default is every recordable spec.')
  parser.add_argument('--keep', help='Directory to build the throwaway client in, and leave behind.')
  parser.add_argument('--pause', type=float, default=1.0, help='Seconds between calls (default 1).')
  args = parser.parse_args()

  index = json.loads((ROOT / 'registry.json').read_text())
  if args.spec and args.spec not in index['specs']:
    print(f'no spec named {args.spec!r} in registry.json', file=sys.stderr)
    return 2
  names = [args.spec] if args.spec else [
    name for name, entry in index['specs'].items() if entry['recording'].get('recordable')
  ]
  failures = sum(record_spec(name, index['specs'][name], args.keep and Path(args.keep), args.pause) for name in names)
  refresh_index(names)
  if failures:
    print(f'{failures} example(s) did not record', file=sys.stderr)
  return 1 if failures else 0


if __name__ == '__main__':
  sys.exit(main())
