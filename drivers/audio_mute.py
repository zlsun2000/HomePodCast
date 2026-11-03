"""Apply an endpoint's mute state to captured PCM without changing its gain."""

import numpy as np


def apply_endpoint_mute(samples, volume, software_volume=False):
    """Gate mute/zero; optionally apply scalar when the driver does not."""
    if volume.GetMute():
        return np.zeros_like(samples)
    scalar = volume.GetMasterVolumeLevelScalar()
    if scalar <= 0:
        return np.zeros_like(samples)
    if software_volume:
        return samples * min(scalar, 1.0)
    return samples
