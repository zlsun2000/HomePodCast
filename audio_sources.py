"""Source selection policy; names only suggest candidates, IDs bind devices."""


def is_virtual_source(name):
    name = name.lower()
    return any(part in name for part in ("vb-audio", "cable input", "cable in 16ch", "homepodcast"))


def available_sources(sources, mode, saved_id, missing_label):
    candidates = list(sources)
    if mode == "virtual":
        candidates = [s for s in candidates if s[0] == saved_id or is_virtual_source(s[1])]
        # Keep explicitly saved endpoints, but avoid presenting VB-CABLE's
        # alternate 16-channel pin when its standard playback pin is present.
        if any("cable input" in s[1].lower() for s in candidates):
            candidates = [s for s in candidates if s[0] == saved_id or "cable in 16ch" not in s[1].lower()]
    else:
        candidates = [s for s in candidates if not is_virtual_source(s[1])]
    # A missing saved ID must never silently become a physical/default source.
    if saved_id and not any(s[0] == saved_id for s in candidates):
        return [(saved_id, missing_label, 0)] + candidates
    if not candidates:
        return [(None, missing_label, 0)]
    if mode == "virtual" and not saved_id and len(candidates) > 1:
        return [(None, missing_label, 0)] + candidates
    return candidates


def source_labels(sources, formatter):
    labels = [formatter(name, channels) for _, name, channels in sources]
    return [f"{label} [{endpoint}]" if labels.count(label) > 1 else label
            for (endpoint, _, _), label in zip(sources, labels)]
