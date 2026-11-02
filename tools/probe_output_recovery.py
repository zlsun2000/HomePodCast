"""Exercise persisted recovery after a child exits without routing cleanup."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio_session import OutputRouting, RoutingJournal
from windows_audio import WindowsAudio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    backend = WindowsAudio()
    route = OutputRouting(backend, RoutingJournal(args.journal))
    if args.worker:
        route.prepare(args.source_id)
        route.activate()
        os._exit(0)  # Simulates abrupt termination; deliberately bypasses cleanup.
    before = {r: backend.default(r) for r in (0, 1, 2)}
    if args.journal.exists():
        raise RuntimeError("Refusing to overwrite an existing recovery journal")
    try:
        subprocess.run([sys.executable, __file__, "--worker", "--source-id", args.source_id,
                        "--journal", str(args.journal), "--output", str(args.output)],
                       timeout=15, check=True)
        during = {r: backend.default(r) for r in (0, 1, 2)}
    finally:
        try:
            if args.journal.exists():
                route.load_recovery()
                failures = route.restore()
                if failures:
                    raise RuntimeError("; ".join(failures))
            after = {r: backend.default(r) for r in (0, 1, 2)}
        finally:
            backend.close()
    assert during[0] == during[1] == args.source_id
    assert during[2] == before[2]
    assert before == after
    assert not args.journal.exists()
    report = dict(before=before, after_abrupt_exit=during, after_recovery=after,
                  restored=before == after, journal_removed=not args.journal.exists())
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
