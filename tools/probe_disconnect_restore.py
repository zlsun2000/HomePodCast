"""Controlled all-offline fault injection; does not disable network or devices."""

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Engine
from windows_audio import WindowsAudio


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--receiver-address", required=True, help="Exact HomePod IP to test")
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.journal.exists():
        raise RuntimeError("Refusing to overwrite an existing routing journal")
    backend = WindowsAudio()
    before = {r: backend.default(r) for r in (0, 1, 2)}
    engine = Engine()
    try:
        devices = engine.scan(4).result(12)
        devices = [device for device in devices if str(device.address) == args.receiver_address]
        if len(devices) != 1:
            raise RuntimeError("Expected exactly one discovered receiver at the requested address")
        engine.start([devices[0]], "mono", args.source_id, 2, route_options={
            "journal_path": str(args.journal.resolve()), "restore_on_disconnect": True}).result(25)
        async def mark_offline():
            for output in engine.outputs:
                output.online = False
        engine._submit(mark_offline()).result(2)
        started = time.monotonic()
        early_state = None
        while time.monotonic() - started < 16:
            elapsed = time.monotonic() - started
            state = engine.status()
            if elapsed >= 3 and early_state is None:
                early_state = state["state"]
            if state["state"] == "idle":
                break
            time.sleep(.1)
        elapsed = time.monotonic() - started
        state = engine.status()
        assert early_state == "streaming", "Stopped before the grace period"
        assert state["state"] == "idle", "Did not stop after the grace period"
        assert state["error"] == ("disconnected", "All receivers"), state["error"]
        assert elapsed >= 10
    finally:
        engine.stop().result(8)
        after = {r: backend.default(r) for r in (0, 1, 2)}
        backend.close()
    assert before == after, "Outputs were not restored"
    assert not args.journal.exists()
    report = dict(fault_model="force receiver online flag false; real network remains connected",
                  elapsed_until_idle_seconds=elapsed, early_state=early_state, final_state=state,
                  before=before, after=after, restored=before == after)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
