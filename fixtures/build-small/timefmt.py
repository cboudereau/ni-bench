"""Duration helpers for schedule displays."""


def format_duration(seconds):
    """Render a non-negative number of seconds as '1h2m3s' (zero parts omitted, 0 -> '0s')."""
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    if seconds == 0:
        return "0s"
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs:
        parts.append(f"{secs}s")
    return "".join(parts)
