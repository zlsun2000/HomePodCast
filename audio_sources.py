"""Source selection policy; names only suggest candidates, IDs bind devices."""


def available_sources(sources, mode, saved_id, missing_label):
    candidates = list(sources)
    if mode == "virtual":
        candidates = [s for s in candidates if s[0] == saved_id or
                      "vb-audio" in s[1].lower() or "cable input" in s[1].lower() or
                      "homepodcast audio" in s[1].lower()]
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
