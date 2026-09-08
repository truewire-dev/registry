"""Say out loud which specs have evidence and which only have a declaration.

`truewire examples --require-verified` excuses an endpoint that declares `unverified`, and
that is right: a call needing a credential this repository does not hold will never be
recorded here, and the declaration is the honest record of it. The cost is that a spec can
pass the gate carrying no evidence at all, which is exactly what a freshly authored spec
does until someone runs the Record workflow.

So this reports the split rather than tightening the gate. It fails only on a claim that
turned out to be false -- a spec listed `recorded` whose tree says otherwise -- and warns,
without failing, for every spec still waiting on a recording run.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_index import ROOT, survey  # noqa: E402


def main() -> int:
  index = json.loads((ROOT / 'registry.json').read_text())['specs']
  rows = ['| Spec | Endpoints | Recorded | Declared unverified | Status |', '| --- | --- | ---: | ---: | --- |']
  problems = []
  for name, entry in index.items():
    tree = survey(name)
    rows.append(
      f'| `{name}` | {tree["endpoints"]} | {tree["endpoints_with_examples"]} '
      f'| {tree["endpoints_unverified"]} | {tree["status"]} |'
    )
    if entry['status'] == 'recorded' and tree['status'] != 'recorded':
      missing = tree['endpoints'] - tree['endpoints_with_examples']
      problems.append(f'{name}: listed `recorded`, but {missing} endpoint(s) hold no recorded pair')
    elif tree['status'] == 'unrecorded':
      print(
        f'::warning::{name} is listed but unverified: its endpoints declare `unverified` '
        'with reason `not_captured`, so nothing has been recorded from the live API yet. '
        'Run the Record workflow.'
      )
  print('\n'.join(rows))
  summary = os.environ.get('GITHUB_STEP_SUMMARY')
  if summary:
    Path(summary).write_text('\n'.join(rows) + '\n')
  for problem in problems:
    print(f'::error::{problem}')
  return 1 if problems else 0


if __name__ == '__main__':
  sys.exit(main())
