"""Short VM-only end-to-end HomePodCast test using an explicit receiver address."""
import asyncio
import json
from pathlib import Path
import sys
import time
import traceback

import numpy as np
import soundcard as sc
import pyatv
from pyatv.const import Protocol
# SoundCard initializes this thread as MTA. Match it before importing comtypes.
sys.coinit_flags = 0
from pycaw.utils import AudioUtilities
from engine import Engine


async def find_receiver(address):
    devices = await pyatv.scan(asyncio.get_running_loop(), timeout=6, hosts=[address])
    candidates = [item for item in devices if item.get_service(Protocol.RAOP)]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one RAOP receiver at {address}; found {len(candidates)}")
    return candidates[0]


def main():
    report_path = Path(sys.argv[1])
    report = {'stages': [], 'passed': False}
    engine = volume = None
    original = None
    try:
        address = Path(__file__).with_name('receiver-address.txt').read_text(encoding='utf-8').strip()
        if not address:
            raise RuntimeError('Rebuild the test media with --receiver-address <HomePod IP> for the audible test.')
        candidates = [s for s in sc.all_speakers() if 'homepodcast audio' in s.name.casefold()]
        if len(candidates) != 1:
            raise RuntimeError(f'Expected one virtual speaker; found {len(candidates)}')
        speaker = candidates[0]
        receiver = asyncio.run(find_receiver(address))
        report['receiver_found'] = True
        enumerator = AudioUtilities.GetDeviceEnumerator()
        volume = AudioUtilities.CreateDevice(enumerator.GetDevice(speaker.id)).EndpointVolume
        original = (volume.GetMasterVolumeLevelScalar(), volume.GetMute())
        volume.SetMasterVolumeLevelScalar(1.0, None)
        volume.SetMute(0, None)
        engine = Engine()
        engine.start([receiver], 'mono', speaker.id, 2, reconnect=False,
                     respect_endpoint_mute=True).result(timeout=30)
        time.sleep(2)
        signal = np.stack([np.sin(2 * np.pi * 700 * np.arange(44100 * 2) / 44100)] * 2, axis=1)
        signal = (signal * .01).astype(np.float32)
        for label, muted in [('first_sound', False), ('muted', True), ('second_sound', False)]:
            volume.SetMute(int(muted), None)
            time.sleep(.5)
            print(f'STAGE: {label}', flush=True)
            speaker.play(signal, samplerate=44100)
            status = engine.status()
            report['stages'].append({'name': label, 'requested_mute': muted,
                                     'reported_mute': bool(volume.GetMute()),
                                     'state': status['state'], 'level': status['level'],
                                     'outputs': status['outputs'], 'error': status['error']})
            time.sleep(1)
        time.sleep(2)
        report['passed'] = all(s['state'] == 'streaming' and not s['error'] and
                               s['requested_mute'] == s['reported_mute'] and
                               s['outputs'] and all(o['online'] and o['timing'] > 0 for o in s['outputs'])
                               for s in report['stages'])
        report['audible_result'] = 'Requires user confirmation: hear first and second tone, silence in the middle.'
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
        report['traceback'] = traceback.format_exc()
    finally:
        if engine:
            try:
                engine.stop().result(timeout=15)
            except Exception as error:
                report['cleanup_error'] = str(error)
                report['passed'] = False
            engine.loop.call_soon_threadsafe(engine.loop.stop)
        if volume is not None and original is not None:
            try:
                volume.SetMasterVolumeLevelScalar(original[0], None)
                volume.SetMute(original[1], None)
                report['volume_restored'] = (abs(volume.GetMasterVolumeLevelScalar() - original[0]) < .0001
                                             and volume.GetMute() == original[1])
                report['passed'] &= report['volume_restored']
            except Exception as error:
                report['restore_error'] = str(error)
                report['passed'] = False
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
