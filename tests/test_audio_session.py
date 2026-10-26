from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import psutil

from audio_session import OutputRouting, RoutingJournal


class Backend:
    def __init__(self):
        self.defaults = {0: "speakers", 1: "headphones", 2: "communications"}
        self.devices = set(self.defaults.values()) | {"virtual"}
        self.events = []
        self.fail_role = None

    def default(self, role):
        return self.defaults[role]

    def available(self, endpoint):
        return endpoint in self.devices

    def set_default(self, endpoint, role):
        self.defaults[role] = endpoint
        self.events.append((role, endpoint))
        if self.fail_role == role and endpoint == "virtual":
            raise OSError("Partial Windows failure")

    def changes(self):
        events, self.events = self.events, []
        return events


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.backend = Backend()
        self.journal = RoutingJournal(Path(self.temp.name) / "routing-state.json")
        self.route = OutputRouting(self.backend, self.journal)

    def test_roundtrip_preserves_independent_roles(self):
        before = dict(self.backend.defaults)
        self.route.prepare("virtual")
        self.route.activate()
        self.assertEqual(self.backend.defaults, {0: "virtual", 1: "virtual", 2: "communications"})
        self.assertEqual(self.route.restore(), [])
        self.assertEqual(self.backend.defaults, before)
        self.assertFalse(self.journal.path.exists())
        self.assertEqual(self.route.restore(), [])

    def test_partial_switch_failure_rolls_back_changed_roles(self):
        before = dict(self.backend.defaults)
        self.route.prepare("virtual")
        self.backend.fail_role = 1
        with self.assertRaises(OSError):
            self.route.activate()
        self.assertEqual(self.backend.defaults, before)

    def test_user_switch_away_then_back_relinquishes_ownership(self):
        self.route.prepare("virtual")
        self.route.activate()
        self.backend.set_default("headphones", 0)
        self.backend.set_default("virtual", 0)
        self.route.restore()
        self.assertEqual(self.backend.default(0), "virtual")
        self.assertEqual(self.backend.default(1), "headphones")

    def test_change_while_connecting_is_not_overwritten(self):
        self.route.prepare("virtual")
        self.backend.set_default("headphones", 0)
        self.route.activate()
        self.assertEqual(self.backend.default(0), "headphones")
        self.route.restore()
        self.assertEqual(self.backend.default(0), "headphones")

    def test_unplugged_original_retains_recovery_journal(self):
        self.route.prepare("virtual")
        self.route.activate()
        self.backend.devices.remove("speakers")
        self.assertTrue(self.route.restore())
        self.assertTrue(self.journal.path.exists())
        self.assertEqual(self.backend.default(0), "virtual")

    def test_existing_journal_blocks_a_new_transaction(self):
        self.journal.write({"unresolved": True})
        with self.assertRaises(RuntimeError):
            self.route.prepare("virtual")
        self.assertEqual(self.backend.default(0), "speakers")

    def test_opt_in_communications_role_is_restored_independently(self):
        self.route.prepare("virtual", communications=True)
        self.route.activate()
        self.assertEqual(self.backend.default(2), "virtual")
        self.route.restore()
        self.assertEqual(self.backend.default(2), "communications")

    def test_failed_journal_write_changes_no_output(self):
        self.journal.write = lambda state: (_ for _ in ()).throw(OSError("Disk full"))
        with self.assertRaises(OSError):
            self.route.prepare("virtual")
        self.assertIsNone(self.route.state)
        self.assertEqual(self.backend.default(0), "speakers")

    def test_live_process_journal_cannot_be_recovered(self):
        self.route.prepare("virtual")
        recovery = OutputRouting(self.backend, self.journal)
        with self.assertRaisesRegex(RuntimeError, "running process"):
            recovery.load_recovery()
        self.assertIsNone(recovery.state)

    def test_dead_process_recovery_only_restores_matching_roles(self):
        self.route.prepare("virtual")
        self.route.activate()
        self.backend.set_default("speakers", 1)
        recovery = OutputRouting(self.backend, self.journal)
        with patch("audio_session.psutil.Process", side_effect=psutil.NoSuchProcess(123)):
            recovery.load_recovery()
        recovery.restore()
        self.assertEqual(self.backend.default(0), "speakers")
        self.assertEqual(self.backend.default(1), "speakers")

    def test_corrupt_journal_never_changes_outputs(self):
        self.journal.write({"schema_version": 999})
        with self.assertRaises(RuntimeError):
            self.route.load_recovery()
        self.assertEqual(self.backend.default(0), "speakers")


if __name__ == "__main__":
    unittest.main()
