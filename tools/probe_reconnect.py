"""Close this sender's RTSP transport and verify automatic reconnection."""

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
        raise RuntimeError("Existing journal must be recovered first")
    backend = WindowsAudio()
    before = {r: backend.default(r) for r in (0, 1, 2)}
    engine = Engine()
    try:
        devices = engine.scan(4).result(12)
        devices = [device for device in devices if str(device.address) == args.receiver_address]
        if len(devices) != 1:
            raise RuntimeError("Expected exactly one discovered receiver at the requested address")
        engine.start([devices[0]], "mono", args.source_id, 2, route_options={
            "journal_path": str(args.journal.resolve()), "restore_on_disconnect": False}).result(25)
        old = engine.outputs[0]
        engine.loop.call_soon_threadsafe(old.conn.close)
        started = time.monotonic()
        observed_offline = False
        while time.monotonic() - started < 30:
            state = engine.status()
            if state["state"] != "streaming":
                raise RuntimeError(f"Stream stopped unexpectedly: {state}")
            observed_offline |= not state["outputs"][0]["online"]
            if (engine.outputs[0] is not old and state["outputs"][0]["online"]
                    and state["outputs"][0]["timing"] > 0):
                break
            time.sleep(.1)
        else:
            raise RuntimeError("Receiver did not rejoin within 30 seconds")
        assert observed_offline
        assert backend.default(0) == backend.default(1) == args.source_id
        elapsed = time.monotonic() - started
    finally:
        engine.stop().result(8)
        after = {r: backend.default(r) for r in (0, 1, 2)}
        backend.close()
    assert before == after
    report = dict(fault_model="close sender RTSP transport; no network configuration change",
                  observed_offline=observed_offline, reconnect_seconds=elapsed,
                  state_after_rejoin=state, outputs_restored=before == after)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
