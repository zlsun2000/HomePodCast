import asyncio
import unittest
from unittest.mock import AsyncMock, Mock, patch

from engine import Engine


class LifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def test_muted_virtual_output_rejects_test_tone_before_connecting(self):
        engine = Engine.__new__(Engine)
        backend = Mock()
        backend.muted.return_value = True
        with patch("windows_audio.WindowsAudio", return_value=backend):
            with self.assertRaisesRegex(RuntimeError, "muted"):
                await engine._identify(None, "virtual")
        backend.close.assert_called_once()

    async def test_stop_cancels_pending_start_before_cleanup(self):
        engine = Engine.__new__(Engine)
        engine.state = "idle"
        engine._starting = None
        opened = asyncio.Event()

        async def connect(*args):
            engine.state = "connecting"
            opened.set()
            await asyncio.Future()

        async def cleanup():
            engine.state = "idle"

        engine._start_stream = connect
        engine._stop = AsyncMock(side_effect=cleanup)
        start = asyncio.create_task(engine._start([], "mono", "virtual", 2, None, True))
        await opened.wait()
        await engine._request_stop()
        self.assertTrue(start.cancelled())
        self.assertIsNone(engine._starting)
        self.assertEqual(engine.state, "idle")

    async def test_duplicate_start_does_not_replace_pending_task(self):
        engine = Engine.__new__(Engine)
        engine.state = "idle"
        pending = object()
        engine._starting = pending
        with self.assertRaisesRegex(RuntimeError, "already running"):
            await engine._start([], "mono", "virtual", 2, None, True)
        self.assertIs(engine._starting, pending)
