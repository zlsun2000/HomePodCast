"""Bounded RAOP discovery, isolated from potentially slow network cleanup."""

import asyncio
import json
import subprocess
import sys


async def discover():
    import pyatv
    from pyatv.const import Protocol

    devices = await pyatv.scan(asyncio.get_running_loop(), timeout=4)
    print(json.dumps([{"name": d.name, "address": str(d.address)}
                      for d in devices if d.get_service(Protocol.RAOP)],
                     ensure_ascii=False), flush=True)


if __name__ == "__main__":
    if "--worker" in sys.argv:
        asyncio.run(discover())
    else:
        try:
            result = subprocess.run([sys.executable, __file__, "--worker"],
                                    timeout=15, check=False)
            raise SystemExit(result.returncode)
        except subprocess.TimeoutExpired:
            print("HomePod discovery timed out after 15 seconds", file=sys.stderr)
            raise SystemExit(2)
