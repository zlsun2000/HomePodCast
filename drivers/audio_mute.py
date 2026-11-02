"""Apply an endpoint's mute state to captured PCM without changing its gain."""

import numpy as np


def apply_endpoint_mute(samples, volume):
    """Silence mute or zero volume without changing nonzero endpoint gain."""
    return np.zeros_like(samples) if volume.GetMute() or volume.GetMasterVolumeLevelScalar() <= 0 else samples
