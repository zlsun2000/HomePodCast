import unittest

from audio_sources import available_sources, source_labels


class SourcePolicyTests(unittest.TestCase):
    def setUp(self):
        self.devices = [("physical", "Speakers", 2), ("cable", "CABLE Input (VB-Audio)", 2)]

    def test_virtual_candidates_exclude_physical_output(self):
        self.assertEqual(available_sources(self.devices, "virtual", None, "Missing"), self.devices[1:])

    def test_missing_saved_virtual_endpoint_cannot_fall_back(self):
        sources = available_sources(self.devices[:1], "virtual", "removed", "Missing")
        self.assertEqual(sources, [("removed", "Missing", 0)])

    def test_empty_device_list_has_unavailable_placeholder(self):
        self.assertEqual(available_sources([], "physical", None, "Missing"), [(None, "Missing", 0)])

    def test_renamed_selected_device_keeps_exact_id(self):
        self.assertEqual(available_sources([("custom", "My audio", 2)], "virtual", "custom", "Missing"),
                         [("custom", "My audio", 2)])

    def test_multiple_virtual_endpoints_require_explicit_choice(self):
        devices = [("a", "CABLE Input", 2), ("b", "CABLE Input", 2)]
        sources = available_sources(devices, "virtual", None, "Choose")
        self.assertEqual(sources[0], (None, "Choose", 0))
        self.assertEqual(sources[1:], devices)

    def test_duplicate_names_remain_individually_selectable(self):
        devices = [("a", "CABLE Input", 2), ("b", "CABLE Input", 2)]
        labels = source_labels(devices, lambda name, channels: name)
        self.assertNotEqual(labels[0], labels[1])

    def test_own_endpoint_is_candidate_but_does_not_replace_saved_cable(self):
        prototype = ("own-driver", "Speakers (HomePodCast Audio)", 2)
        devices = self.devices + [prototype]
        candidates = available_sources(devices, "virtual", "cable", "Missing")
        self.assertEqual(candidates, [self.devices[1], prototype])
        self.assertEqual(available_sources([prototype], "virtual", "removed", "Missing"),
                         [("removed", "Missing", 0), prototype])


if __name__ == "__main__":
    unittest.main()
